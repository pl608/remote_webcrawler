from threading import Thread
from requests import get    
from bs4 import BeautifulSoup
from time import sleep
from threading import active_count as ac
from threading import Thread
from mqtt import Network
from json import dumps, loads
from base64 import urlsafe_b64decode as b64decode_
from base64 import urlsafe_b64encode as b64encode_
b64decode = lambda args: b64decode_(str(args).encode('utf-8')).decode('utf-8')
b64encode = lambda args: b64encode_(str(args).encode('utf-8')).decode('utf-8')
hosts = []
active = False
def scan(url, parent):
    global n, active
    active = True
    try:
        l = []
        try:
            page = get(url)
            soup = BeautifulSoup(page.text or '', 'html.parser')
            l = soup.findAll('a')
        except:pass
        for link in l or []:
            new_url = link.attrs.get('href')
            if new_url != None: 
                if new_url.startswith('//'): new_url = 'https:'+new_url
                elif new_url.startswith('/'): new_url = url.split('/')[2]+new_url
                elif new_url.startswith('#'): continue
                elif new_url == '': continue
                print('[INFO] Url Found, "',new_url ,'"')
                n.publish(b64encode(dumps({'url':new_url, 'parent_url':url})))
    except Exception as e: print(e, end=' <-- scan\n')
    active = False
connected = False
def on_message(net, cli, usr, msg):
    global connected, active
    m = msg.payload.decode()
    if m == 'start':
        connected = False
        #net.publish('request')
    sender = m[:4]
    if sender == net.device_name: return None
    if sender in hosts:
        print('[MESSAGE] ',m)
    m = m[4:]
    if m == 'host': 
        hosts.append(sender)
        if active == False:
            #net.publish('connected')
            net.publish('request')
            active = True
    elif m.startswith(net.device_name) == True:
        net.publish('active')
        print('[NEW URL]')
        d = loads(b64decode(m[4:]))
        scan(d[0], d[1])
        net.publish('request')
n = Network(topic='web/scanner', on_message_=on_message)
#n_ = Network(topic='web/host', on_message_=on_message, user='scanner',pwd='Scanner1234')
#n_.subscribe()
n.subscribe()
print('publishing')
n.publish('connected')
n.publish('request')
n.client.loop_forever()
