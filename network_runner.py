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
    global n
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
                if new_url.startswith('/'): new_url = url+new_url
                print('[INFO] Url Found')
                print(new_url)
                n.publish(n.device_name+b64encode(dumps({'url':new_url, 'parent_url':parent})))
    except Exception as e: print(e, end=' <-- scan\n')
def on_message(net, cli, usr, msg):
    m = msg.payload.decode()
    sender = m[:4]
    if sender == net.device_name: return None
    print('[MESSAGE] ',m)
    m = m[4:]
    if m == 'host': hosts.append(sender)
    elif m.startswith(net.device_name) == True:
        net.publish(net.device_name+'active')
        print('[NEW URL]')
        scan(loads(b64decode(m[:4])))
        net.publish(net.device_name+'request')
n = Network(topic='web/scanner')
n.subscribe()
n.publish(n.device_name+'connected')
n.client.loop_forever()