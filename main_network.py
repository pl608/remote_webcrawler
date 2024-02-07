from json import loads, dumps
from typing import Any
from mqtt import Network
from dataclasses import dataclass, field
from base64 import urlsafe_b64decode as b64decode
from base64 import urlsafe_b64encode as b64encode
from os import remove, mkdir, walk, path, remove
from zipfile import ZipFile
from time import time
from hashlib import md5 
def get_domain(url):
    try:
        return url.split('/')[2]
    except:
        print(url)
stats = {
    'urlsps':0,
    'urls':0,
    'start':time(),
    'runners':{}
}
commands = [
    'connected',
    'disconnected',
    'done',
    'active',
    'request', # requesting a job
]
@dataclass
class Website:
    url: str
    website: str
    parent_url: str
    runner: str
    alt_runner: []
    alt_parents: []
    scanned:bool = field(default= False)
    def __setattr__(self, __name: str, __value: Any) -> None:
        super().__setattr__(__name, __value)
class Data():
    def __init__(self, directory='D:\\urls') -> None:
        self.dir = directory
        self.unpros = [['https://www.wikipedia.org/','']]
        self.urls = {}
        for root, dirs, files in walk(self.dir):
            for file in files:
                    #remove()
                    zip = open(path.join(root, file), 'r')
                    data = loads(zip.read())
                    data['scanned'] = data.get('scanned', False)
                    data['url'] = data['url'].split('?',1)[0]
                    self.urls.update({data['url']:Website(**data)})
                    if data.get('scanned', False) == False:
                        self.unpros.append([data['url'], data['parent_url']])
    def trigger_save(self,url):
        path_ = path.join(self.dir, md5(url.encode('utf-8')).hexdigest()[:2],md5(url.encode('utf-8')).hexdigest()[:16])
        try: mkdir(path.join(self.dir, path.basename(path_)[:2]))
        except: pass
        f = open(path_, 'w')
        f.write(dumps(self.urls[url].__dict__))
        f.close()
    def add(self, cls):
        cls.url = cls.url.split('?',1)[0]
        if cls.url in self.urls:
            self.urls[cls.url].alt_parents += [cls.parent_url]
            self.urls[cls.url].alt_parents = list(set(self.urls[cls.url].alt_parents))
            self.urls[cls.url].alt_runner += [cls.runner]
            self.urls[cls.url].alt_parents = list(set(self.urls[cls.url].alt_runner))
            self.trigger_save(cls.url)
        else:
            self.unpros.append([cls.url, cls.parent_url])
            self.urls.update({cls.url: cls})
            self.trigger_save(cls.url)
d = Data()
_ = None
def on_message(net, cli, usr_data, msg):
    m = msg.payload.decode()
    sender = m[:4]
    if sender == net.device_name: return None
    #print('[MESSAGE] ',m)
    if sender not in stats['runners']:
        stats['runners'].update({sender:{'connected':False, 'active':False, 'urls':0}})
    if m[4:] in commands:
        if m[4:] == 'connected':
            stats['runners'][sender]['connected'] = True
            print('[CONNECTION] ', sender)
            net.publish('host')
        elif m[4:] == 'disconnected':
            stats['runners'][sender]['disconnected'] = False
            print('[DISCONNECTION] ', sender)
        elif m[4:] == 'done':
            stats['runners'][sender]['active'] = False
        elif m[4:] == 'request':
            try:
                d_ = d.unpros.pop(0)
                try:
                    d.urls[d_[0]].scanned = True
                    d.trigger_save(d_[0])
                except: pass
                
                net.publish(sender+b64encode(dumps([d_[0].split('?',1)[0], d_[1].split('?',1)[0]]).encode('utf-8')).decode('utf-8'))
            except Exception as e:
                _ = e
            print('[REQUEST] ',sender)
        elif m[4:] == 'active':
            stats['runners'][sender]['active'] = True
            print('[INFO] ',sender, ' active')
        return None
    data = loads(b64decode(m[4:].encode('utf-8')))
    data['runner'] = sender
    data['website'] = get_domain(data['url'])
    data['alt_runner'] = []
    data['alt_parents'] = []
    d.add(Website(**data))
n = Network(topic='web/scanner', on_message_=on_message)
#n_ = Network(topic='web/hosts', on_message_=on_message, usr='host', pwd='Hoster1234')
#n_.subscribe()
n.subscribe()
n.publish('host')
n.client.publish('start')
n.client.loop_forever()
