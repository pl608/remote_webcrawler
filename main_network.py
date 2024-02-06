from json import loads, dumps
from typing import Any
from mqtt import Network
from dataclasses import dataclass
from base64 import urlsafe_b64decode as b64decode
from base64 import urlsafe_b64encode as b64encode
from os import remove
from zipfile import ZipFile
from time import time
def get_domain(url):
    return url.split('/')[2]
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
    scanned = False
    def __setattr__(self, __name: str, __value: Any) -> None:
        super().__setattr__(__name, __value)
        self.data.trigger_save(self.url)
class Data():
    def __init__(self, file='websites.zip') -> None:
        self.filename = file
        self.unpros = ['https://www.wikipedia.org/']
        try: ZipFile(file, 'a').close() # create file if it doesnt exists
        except: pass
        zip = ZipFile(file, 'r')
        self.urls = {}
        for file in zip.infolist():
            url = b64decode(file.filename)
            data = loads(zip.read(file.filename))
            self.urls.update({url:Website(**data)})
    def trigger_save(self,url):
        zip = ZipFile(self.filename, 'a')
        open(b64encode(url).decode('utf-8'),'w').write(dumps(self.urls[url].__dict__))
        zip.write(b64encode(url).decode('utf-8'))
        remove(b64encode(url).decode('utf-8'))
        zip.close()
    def add(self, cls):
        if cls.url in self.urls:
            self.urls[cls.url].alt_parents += cls.parent
            self.urls[cls.url].alt_runner += cls.runner
            self.trigger_save(cls.url)
        else:
            self.unpros.append(cls.url)
            self.add(cls)
        self.urls.update({cls.url: cls})
        self.trigger_save(cls.url)
d = Data()
def on_message(net, cli, usr_data, msg):
    m = msg.payload.decode()
    sender = m[:4]
    if sender == net.device_name: return None
    if sender not in stats['runners']:
        stats['runners'].update({sender:{'connected':False, 'active':False, 'urls':0}})
    if m[4:] in commands:
        if m[4:] == 'connected':
            stats[sender]['connected'] = True
            print('[CONNECTION] ', sender)
            net.publish(n.device_name+'host')
        elif m[4:] == 'disconnected':
            stats[sender]['disconnected'] = False
            print('[DISCONNECTION] ', sender)
        elif m[4:] == 'done':
            stats[sender]['active'] = False
        elif m[4:] == 'request':
            net.publish(net.device_name+sender+b64encode(dumps([d.unpros.pop(0)])).decode('utf-8'))
            print('[REQUEST] ',sender)
        elif m[4:] == 'active':
            stats[sender]['active'] = True
            print('[INFO] ',sender, ' active')
        return None
    data = loads(m[4:])
    data['runner'] = sender
    data['website'] = get_domain(data['url'])
    d.add(Website(**data))
n = Network(topic='web/scanner', on_message=on_message)
n.subscribe()
n.publish(n.device_name+'host')
n.client.loop_forever()