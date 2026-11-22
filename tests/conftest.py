import io, json, time
from urllib.parse import urlsplit
import pytest
from casa_ogro.webapp import create_application

class WSGIClient:
    def __init__(self, app): self.app=app; self.cookie=''
    def request(self, method, path, data=None):
        u=urlsplit(path); raw=json.dumps(data).encode() if data is not None else b''
        env={'REQUEST_METHOD':method,'PATH_INFO':u.path,'QUERY_STRING':u.query,'CONTENT_TYPE':'application/json',
             'CONTENT_LENGTH':str(len(raw)),'wsgi.input':io.BytesIO(raw),'wsgi.errors':io.StringIO(),
             'wsgi.version':(1,0),'wsgi.url_scheme':'http','wsgi.multithread':True,'wsgi.multiprocess':False,
             'wsgi.run_once':False,'SERVER_NAME':'localhost','SERVER_PORT':'8000','SERVER_PROTOCOL':'HTTP/1.1'}
        if self.cookie: env['HTTP_COOKIE']=self.cookie
        captured={}
        def start_response(status, headers, exc_info=None): captured['status']=int(status.split()[0]); captured['headers']=dict(headers)
        result=b''.join(self.app(env,start_response)); payload=json.loads(result) if result and captured['headers'].get('Content-Type','').startswith('application/json') else result
        set_cookie=captured['headers'].get('Set-Cookie')
        if set_cookie:
            first=set_cookie.split(';',1)[0]
            if first.endswith('='): self.cookie=''
            else: self.cookie=first
        return captured['status'],payload,captured['headers']
    def login(self, username='recepcion', password='recep123'):
        return self.request('POST','/api/login',{'username':username,'password':password})

@pytest.fixture
def clock():
    return {'value':'2026-11-17T10:30:00-03:00'}

@pytest.fixture
def client(tmp_path, clock):
    app=create_application(tmp_path/'test.sqlite3', clock=lambda:clock['value'])
    c=WSGIClient(app)
    assert c.login()[0]==200
    return c

def guest(c):
    status,data,_=c.request('POST','/api/guests',{'first_name':'Ana','last_name':'Prueba','phone':'912345678','email':'ana@example.com'})
    assert status==201
    return data['id']

def room_id(c, number='101'):
    status,rooms,_=c.request('GET','/api/rooms')
    assert status==200
    return next(r['id'] for r in rooms if r['number']==number)

def reservation(c, checkin='2026-11-25T15:00:00-03:00', checkout='2026-11-27T12:00:00-03:00', number='101'):
    gid=guest(c); rid=room_id(c,number)
    status,data,_=c.request('POST','/api/reservations',{'guest_id':gid,'room_id':rid,'checkin':checkin,'checkout':checkout})
    assert status==201, data
    return data['id'],rid
