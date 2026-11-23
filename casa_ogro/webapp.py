from __future__ import annotations
import json, os, re, secrets, time, sqlite3, socket
from datetime import datetime, timedelta
from http import cookies
from pathlib import Path
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server, WSGIServer
from socketserver import ThreadingMixIn
from .db import connect, init_db, verify_password, password_hash
from .rules import classify_occupancy, is_after_checkout_cutoff, is_confirmed_reservation, is_reading_stale

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB = BASE_DIR / 'data' / 'casa_ogro.sqlite3'
SESSIONS: dict[str, int] = {}
ROLES = {'admin': 'Administrador', 'recepcion': 'Recepción', 'limpieza': 'Limpieza'}

class APIError(Exception):
    def __init__(self, status: int, message: str):
        self.status, self.message = status, message

def now_iso():
    return datetime.now().astimezone().replace(microsecond=0).isoformat()

def parse_dt(value: str) -> datetime:
    try:
        if isinstance(value, str) and value.endswith('Z'):
            value = value[:-1] + '+00:00'
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.astimezone()
        return dt
    except (ValueError, TypeError):
        raise APIError(400, 'Fecha inválida. Use formato ISO, por ejemplo 2026-11-20T15:00:00.')

def serial(row):
    return dict(row) if row is not None else None

def create_application(db_path: str | Path = DEFAULT_DB, clock=None):
    db_path = str(db_path)
    init_db(db_path, demo=True)
    current_time = clock or now_iso

    def response(start_response, status, payload, extra_headers=None):
        body = payload if isinstance(payload, bytes) else json.dumps(payload, ensure_ascii=False).encode('utf-8')
        headers = [('Content-Type', 'application/json; charset=utf-8'), ('Content-Length', str(len(body))), ('Cache-Control','no-store')]
        if extra_headers: headers.extend(extra_headers)
        start_response(f'{status} {status_text(status)}', headers)
        return [body]

    def audit(conn, user, action, entity, entity_id=None, detail=''):
        conn.execute('INSERT INTO admin_audit(user_id,username,action,entity,entity_id,detail,created_at) VALUES(?,?,?,?,?,?,?)',
                     (user['id'] if user else None, user['username'] if user else 'sistema', action, entity,
                      str(entity_id) if entity_id is not None else None, str(detail)[:500], current_time()))

    def status_text(code):
        return {200:'OK',201:'Created',204:'No Content',302:'Found',400:'Bad Request',401:'Unauthorized',403:'Forbidden',404:'Not Found',409:'Conflict',422:'Unprocessable Entity',500:'Internal Server Error'}.get(code,'OK')

    def app(environ, start_response):
        method, path = environ.get('REQUEST_METHOD','GET').upper(), environ.get('PATH_INFO','/')
        query = parse_qs(environ.get('QUERY_STRING',''))
        length = int(environ.get('CONTENT_LENGTH') or 0)
        raw = environ['wsgi.input'].read(length) if length else b''
        data = {}
        if raw:
            ctype = environ.get('CONTENT_TYPE','')
            try:
                if 'application/json' in ctype:
                    data = json.loads(raw.decode('utf-8'))
                else:
                    data = {k:v[-1] for k,v in parse_qs(raw.decode('utf-8')).items()}
            except (ValueError, UnicodeDecodeError):
                return response(start_response,400,{'error':'Cuerpo de solicitud inválido.'})
        cookie = cookies.SimpleCookie()
        cookie.load(environ.get('HTTP_COOKIE',''))
        sid = cookie['ogro_session'].value if 'ogro_session' in cookie else None
        user_id = SESSIONS.get(sid) if sid else None
        conn = connect(db_path)
        try:
            user = conn.execute('SELECT id,username,role,active FROM users WHERE id=?', (user_id,)).fetchone() if user_id else None
            if path == '/' and method == 'GET':
                html = (BASE_DIR / 'static' / 'index.html').read_bytes()
                start_response('200 OK',[('Content-Type','text/html; charset=utf-8'),('Content-Length',str(len(html)))])
                return [html]
            if path == '/static/style.css' and method == 'GET':
                body=(BASE_DIR/'static'/'style.css').read_bytes(); start_response('200 OK',[('Content-Type','text/css'),('Content-Length',str(len(body)))]); return [body]
            if path == '/health' and method == 'GET':
                return response(start_response,200,{'status':'ok','timestamp':current_time()})
            if path == '/api/login' and method == 'POST':
                username, password = str(data.get('username','')).strip(), str(data.get('password',''))
                row = conn.execute('SELECT * FROM users WHERE username=?',(username,)).fetchone()
                if not row or not row['active'] or not verify_password(password,row['password_hash']):
                    raise APIError(401,'Credenciales incorrectas o cuenta desactivada.')
                token=secrets.token_urlsafe(32); SESSIONS[token]=row['id']
                return response(start_response,200,{'message':'Sesión iniciada.','user':{'id':row['id'],'username':row['username'],'role':row['role'],'role_name':ROLES[row['role']]}},[('Set-Cookie',f'ogro_session={token}; HttpOnly; SameSite=Lax; Path=/')])
            if path == '/api/logout' and method == 'POST':
                if sid: SESSIONS.pop(sid,None)
                return response(start_response,200,{'message':'Sesión cerrada.'},[('Set-Cookie','ogro_session=; Max-Age=0; Path=/; HttpOnly; SameSite=Lax')])
            if path == '/api/me' and method == 'GET':
                require_user(user)
                return response(start_response,200,{'id':user['id'],'username':user['username'],'role':user['role'],'role_name':ROLES[user['role']]})
            if path == '/api/dashboard' and method == 'GET':
                require_user(user)
                return response(start_response,200,dashboard_data(conn,current_time()))
            # Guests
            if path == '/api/guests' and method == 'GET':
                require_roles(user,'recepcion','admin')
                return response(start_response,200,[serial(r) for r in conn.execute('SELECT * FROM guests ORDER BY id DESC').fetchall()])
            if path == '/api/guests' and method == 'POST':
                require_roles(user,'recepcion','admin'); require_fields(data,'first_name','last_name','phone','email')
                cur=conn.execute('INSERT INTO guests(first_name,last_name,phone,email) VALUES(?,?,?,?)',tuple(str(data[k]).strip() for k in ('first_name','last_name','phone','email')))
                if user and user['role']=='admin': audit(conn,user,'crear','huésped',cur.lastrowid)
                conn.commit(); return response(start_response,201,serial(conn.execute('SELECT * FROM guests WHERE id=?',(cur.lastrowid,)).fetchone()))
            m=re.fullmatch(r'/api/guests/(\d+)',path)
            if m and method == 'PATCH':
                require_roles(user,'admin')
                gid=int(m.group(1)); row=conn.execute('SELECT * FROM guests WHERE id=?',(gid,)).fetchone()
                if not row: raise APIError(404,'Huésped no encontrado.')
                values={k:str(data.get(k,row[k])).strip() for k in ('first_name','last_name','phone','email')}
                if any(not v for v in values.values()): raise APIError(400,'Todos los campos del huésped son obligatorios.')
                conn.execute('UPDATE guests SET first_name=?,last_name=?,phone=?,email=? WHERE id=?',(*values.values(),gid)); audit(conn,user,'editar','huésped',gid,values['first_name']+' '+values['last_name']); conn.commit()
                return response(start_response,200,serial(conn.execute('SELECT * FROM guests WHERE id=?',(gid,)).fetchone()))
            if m and method == 'DELETE':
                require_roles(user,'admin')
                gid=int(m.group(1)); row=conn.execute('SELECT id FROM guests WHERE id=?',(gid,)).fetchone()
                if not row: raise APIError(404,'Huésped no encontrado.')
                linked=conn.execute('SELECT COUNT(*) FROM reservations WHERE guest_id=?',(gid,)).fetchone()[0]
                if linked: raise APIError(409,'No se puede eliminar el huésped porque conserva reservas asociadas. Elimina primero esas reservas desde Administración y pruebas.')
                conn.execute('DELETE FROM guests WHERE id=?',(gid,)); audit(conn,user,'eliminar','huésped',gid); conn.commit()
                return response(start_response,200,{'message':'Huésped eliminado.','guest_id':gid})
            # Rooms and availability
            if path == '/api/rooms' and method == 'GET':
                require_roles(user,'recepcion','admin','limpieza')
                rooms=[serial(r) for r in conn.execute('SELECT * FROM rooms WHERE active=1 ORDER BY number').fetchall()]
                return response(start_response,200,rooms)
            m=re.fullmatch(r'/api/rooms/(\d+)',path)
            if m and method=='GET':
                require_roles(user,'recepcion','admin','limpieza'); room=conn.execute('SELECT * FROM rooms WHERE id=?',(m.group(1),)).fetchone()
                if not room: raise APIError(404,'Habitación no encontrada.')
                return response(start_response,200,serial(room))
            if path == '/api/availability' and method == 'GET':
                require_roles(user,'recepcion','admin')
                checkin=parse_dt(first(query,'checkin')); checkout=parse_dt(first(query,'checkout'))
                if checkout <= checkin: raise APIError(400,'La salida debe ser posterior a la entrada.')
                available=[]
                for room in conn.execute('SELECT * FROM rooms ORDER BY number').fetchall():
                    overlap=conn.execute("SELECT 1 FROM reservations WHERE room_id=? AND status IN ('confirmada','en_curso') AND checkin < ? AND checkout > ? LIMIT 1",(room['id'],checkout.isoformat(),checkin.isoformat())).fetchone()
                    if room['active'] and not overlap and room['state']!='en limpieza': available.append(serial(room))
                return response(start_response,200,available)
            # Reservations
            if path == '/api/reservations' and method == 'GET':
                require_roles(user,'recepcion','admin')
                rows=conn.execute('SELECT r.*,g.first_name,g.last_name,rm.number AS room_number FROM reservations r JOIN guests g ON g.id=r.guest_id JOIN rooms rm ON rm.id=r.room_id ORDER BY r.id DESC').fetchall()
                return response(start_response,200,[serial(r) for r in rows])
            if path == '/api/reservations' and method == 'POST':
                require_roles(user,'recepcion','admin'); require_fields(data,'guest_id','room_id','checkin','checkout')
                guest=conn.execute('SELECT id FROM guests WHERE id=?',(data['guest_id'],)).fetchone()
                room=conn.execute('SELECT * FROM rooms WHERE id=?',(data['room_id'],)).fetchone()
                if not guest or not room or not room['active']: raise APIError(400,'Huésped o habitación inexistente o inactiva.')
                start,end=parse_dt(data['checkin']),parse_dt(data['checkout'])
                if end<=start: raise APIError(400,'La salida debe ser posterior a la entrada.')
                if room['state']=='en limpieza' and start.date() <= parse_dt(current_time()).date(): raise APIError(409,'La habitación está en limpieza para la fecha de ingreso.')
                overlap=conn.execute("SELECT 1 FROM reservations WHERE room_id=? AND status IN ('confirmada','en_curso') AND checkin < ? AND checkout > ? LIMIT 1",(room['id'],end.isoformat(),start.isoformat())).fetchone()
                if overlap: raise APIError(409,'La habitación no está disponible para todo el período.')
                cur=conn.execute("INSERT INTO reservations(guest_id,room_id,checkin,checkout,status,created_by) VALUES(?,?,?,?, 'confirmada',?)",(guest['id'],room['id'],start.isoformat(),end.isoformat(),user['id']))
                if user and user['role']=='admin': audit(conn,user,'crear','reserva',cur.lastrowid)
                conn.commit(); return response(start_response,201,serial(conn.execute('SELECT * FROM reservations WHERE id=?',(cur.lastrowid,)).fetchone()))
            m=re.fullmatch(r'/api/reservations/(\d+)',path)
            if m and method == 'PATCH':
                require_roles(user,'admin')
                rid=int(m.group(1)); reservation=conn.execute('SELECT * FROM reservations WHERE id=?',(rid,)).fetchone()
                if not reservation: raise APIError(404,'Reserva no encontrada.')
                if not is_confirmed_reservation(reservation['status']): raise APIError(409,'Solo se pueden editar reservas confirmadas desde este panel. Las reservas en curso o cerradas mantienen su historial.')
                guest_id=int(data.get('guest_id',reservation['guest_id'])); room_id=int(data.get('room_id',reservation['room_id']))
                guest=conn.execute('SELECT id FROM guests WHERE id=?',(guest_id,)).fetchone()
                room=conn.execute('SELECT * FROM rooms WHERE id=?',(room_id,)).fetchone()
                if not guest or not room or not room['active']: raise APIError(400,'Huésped o habitación inexistente o inactiva.')
                start=parse_dt(data.get('checkin',reservation['checkin'])); end=parse_dt(data.get('checkout',reservation['checkout']))
                if end<=start: raise APIError(400,'La salida debe ser posterior a la entrada.')
                if room['state']=='en limpieza' and start.date() <= parse_dt(current_time()).date(): raise APIError(409,'La habitación está en limpieza para la fecha de ingreso.')
                overlap=conn.execute("SELECT 1 FROM reservations WHERE room_id=? AND id<>? AND status IN ('confirmada','en_curso') AND checkin < ? AND checkout > ? LIMIT 1",(room_id,rid,end.isoformat(),start.isoformat())).fetchone()
                if overlap: raise APIError(409,'La habitación no está disponible para las nuevas fechas.')
                conn.execute('UPDATE reservations SET guest_id=?,room_id=?,checkin=?,checkout=? WHERE id=?',(guest_id,room_id,start.isoformat(),end.isoformat(),rid)); audit(conn,user,'editar','reserva',rid); conn.commit()
                return response(start_response,200,serial(conn.execute('SELECT * FROM reservations WHERE id=?',(rid,)).fetchone()))
            if m and method == 'DELETE':
                require_roles(user,'admin')
                rid=int(m.group(1)); reservation=conn.execute('SELECT * FROM reservations WHERE id=?',(rid,)).fetchone()
                if not reservation: raise APIError(404,'Reserva no encontrada.')
                if reservation['status']=='en_curso': raise APIError(409,'No se puede eliminar una reserva en curso. Registra primero el check-out para conservar la consistencia de la habitación.')
                conn.execute('DELETE FROM reservations WHERE id=?',(rid,)); audit(conn,user,'eliminar','reserva',rid); conn.commit()
                return response(start_response,200,{'message':'Reserva eliminada.','reservation_id':rid})
            m=re.fullmatch(r'/api/reservations/(\d+)/(modify|cancel|check-in|check-out)',path)
            if m:
                require_roles(user,'recepcion','admin'); rid,action=int(m.group(1)),m.group(2)
                reservation=conn.execute('SELECT * FROM reservations WHERE id=?',(rid,)).fetchone()
                if not reservation: raise APIError(404,'Reserva no encontrada.')
                now=parse_dt(current_time())
                if action=='modify' and method=='POST':
                    if not is_confirmed_reservation(reservation['status']): raise APIError(409,'Solo se pueden modificar reservas confirmadas. Las reservas en curso o cerradas mantienen su historial.')
                    new_start=parse_dt(data.get('checkin',reservation['checkin'])); new_end=parse_dt(data.get('checkout',reservation['checkout']))
                    if new_end<=new_start: raise APIError(400,'La salida debe ser posterior a la entrada.')
                    if parse_dt(reservation['checkin'])-now < timedelta(hours=24) and user['role']!='admin': raise APIError(403,'Se requiere autorización del Administrador para modificar dentro de las últimas 24 horas.')
                    overlap=conn.execute("SELECT 1 FROM reservations WHERE room_id=? AND id<>? AND status IN ('confirmada','en_curso') AND checkin < ? AND checkout > ? LIMIT 1",(reservation['room_id'],rid,new_end.isoformat(),new_start.isoformat())).fetchone()
                    if overlap: raise APIError(409,'La habitación no está disponible para las nuevas fechas.')
                    conn.execute('UPDATE reservations SET checkin=?,checkout=? WHERE id=?',(new_start.isoformat(),new_end.isoformat(),rid)); audit(conn,user,'modificar fechas','reserva',rid); conn.commit()
                    return response(start_response,200,serial(conn.execute('SELECT * FROM reservations WHERE id=?',(rid,)).fetchone()))
                if action=='cancel' and method=='POST':
                    if not is_confirmed_reservation(reservation['status']): raise APIError(409,'Solo se pueden cancelar reservas confirmadas. Las reservas en curso o cerradas no se pueden cancelar.')
                    if parse_dt(reservation['checkin'])-now < timedelta(hours=24) and user['role']!='admin': raise APIError(403,'Se requiere autorización del Administrador para una cancelación tardía.')
                    conn.execute("UPDATE reservations SET status='cancelada' WHERE id=?",(rid,)); audit(conn,user,'cancelar','reserva',rid); conn.commit()
                    return response(start_response,200,{'message':'Reserva cancelada.','reservation':serial(conn.execute('SELECT * FROM reservations WHERE id=?',(rid,)).fetchone())})
                if action=='check-in' and method=='POST':
                    if now.date() < parse_dt(reservation['checkin']).date(): raise APIError(409,'El check-in no puede registrarse antes de la fecha de llegada.')
                    if now.hour < 15 and user['role']!='admin': raise APIError(403,'El check-in antes de las 15:00 requiere autorización del Administrador.')
                    if reservation['status']!='confirmada': raise APIError(409,'La reserva no está confirmada.')
                    room=conn.execute('SELECT * FROM rooms WHERE id=?',(reservation['room_id'],)).fetchone()
                    if room['state']!='disponible': raise APIError(409,'La habitación no está disponible.')
                    conn.execute("UPDATE rooms SET state='ocupada' WHERE id=?",(room['id'],)); conn.execute("UPDATE reservations SET status='en_curso' WHERE id=?",(rid,)); audit(conn,user,'registrar check-in','reserva',rid); conn.commit()
                    return response(start_response,200,{'message':'Check-in registrado.','room_state':'ocupada'})
                if action=='check-out' and method=='POST':
                    if now.date() < parse_dt(reservation['checkout']).date(): raise APIError(409,'El check-out no puede registrarse antes de la fecha de salida.')
                    if is_after_checkout_cutoff(now) and user['role']!='admin': raise APIError(403,'El check-out después de las 12:00 requiere autorización del Administrador.')
                    if reservation['status']!='en_curso': raise APIError(409,'La reserva no está en curso.')
                    conn.execute("UPDATE rooms SET state='en limpieza' WHERE id=?",(reservation['room_id'],)); conn.execute("UPDATE reservations SET status='completada' WHERE id=?",(rid,)); audit(conn,user,'registrar check-out','reserva',rid); conn.commit()
                    return response(start_response,200,{'message':'Check-out registrado.','room_state':'en limpieza'})
            # Cleaning
            m=re.fullmatch(r'/api/rooms/(\d+)/cleaning/(start|finish)',path)
            if m and method=='POST':
                require_roles(user,'limpieza','admin'); room_id=int(m.group(1)); action=m.group(2)
                room=conn.execute('SELECT * FROM rooms WHERE id=?',(room_id,)).fetchone()
                if not room: raise APIError(404,'Habitación no encontrada.')
                if action=='start':
                    if room['state']!='en limpieza': raise APIError(409,'La habitación debe estar en limpieza para iniciar el registro.')
                    pending=conn.execute('SELECT 1 FROM cleanings WHERE room_id=? AND finished_at IS NULL LIMIT 1',(room_id,)).fetchone()
                    if pending: raise APIError(409,'Ya existe una limpieza iniciada y pendiente para esta habitación.')
                    cur=conn.execute('INSERT INTO cleanings(room_id,started_at,user_id) VALUES(?,?,?)',(room_id,current_time(),user['id']));
                    if user['role']=='admin': audit(conn,user,'iniciar limpieza','habitación',room_id)
                    conn.commit()
                    return response(start_response,201,{'cleaning_id':cur.lastrowid,'message':'Inicio de limpieza registrado.'})
                cleaning=conn.execute('SELECT * FROM cleanings WHERE room_id=? AND finished_at IS NULL ORDER BY id DESC LIMIT 1',(room_id,)).fetchone()
                if not cleaning: raise APIError(409,'No existe una limpieza iniciada pendiente.')
                conn.execute('UPDATE cleanings SET finished_at=? WHERE id=?',(current_time(),cleaning['id'])); conn.execute("UPDATE rooms SET state='disponible' WHERE id=?",(room_id,));
                if user['role']=='admin': audit(conn,user,'finalizar limpieza','habitación',room_id)
                conn.commit()
                return response(start_response,200,{'message':'Limpieza finalizada. Habitación disponible.'})
            # Administrative tools for controlled demonstrations and manual requirement checks.
            if path == '/api/admin/management' and method == 'GET':
                require_roles(user,'admin')
                guests=[serial(r) for r in conn.execute('SELECT * FROM guests ORDER BY id DESC').fetchall()]
                reservations=conn.execute('''SELECT r.*,g.first_name,g.last_name,rm.number AS room_number
                    FROM reservations r JOIN guests g ON g.id=r.guest_id JOIN rooms rm ON rm.id=r.room_id ORDER BY r.id DESC''').fetchall()
                rooms=[serial(r) for r in conn.execute('SELECT * FROM rooms ORDER BY number').fetchall()]
                users=[serial(r) for r in conn.execute('SELECT id,username,role,active FROM users ORDER BY id').fetchall()]
                spaces=[serial(r) for r in conn.execute('SELECT p.*,rm.number AS room_number FROM spaces p LEFT JOIN rooms rm ON rm.id=p.room_id ORDER BY p.kind,p.name').fetchall()]
                sensors=[serial(r) for r in conn.execute('SELECT s.*,p.name AS space_name,p.kind,p.room_id FROM sensors s JOIN spaces p ON p.id=s.space_id ORDER BY s.sensor_id').fetchall()]
                cleanings=[serial(r) for r in conn.execute('SELECT c.*,rm.number AS room_number,u.username FROM cleanings c JOIN rooms rm ON rm.id=c.room_id JOIN users u ON u.id=c.user_id ORDER BY c.id DESC LIMIT 100').fetchall()]
                alerts=[serial(r) for r in conn.execute('SELECT a.*,p.name AS space_name FROM alerts a JOIN spaces p ON p.id=a.space_id ORDER BY a.id DESC LIMIT 100').fetchall()]
                audit_rows=[serial(r) for r in conn.execute('SELECT * FROM admin_audit ORDER BY id DESC LIMIT 100').fetchall()]
                return response(start_response,200,{'guests':guests,'reservations':[serial(r) for r in reservations],'rooms':rooms,'users':users,'spaces':spaces,'sensors':sensors,'cleanings':cleanings,'alerts':alerts,'audit':audit_rows})
            # Full room administration: rooms stay in the same database and get a sensor/space pair.
            if path == '/api/admin/rooms' and method == 'POST':
                require_roles(user,'admin'); require_fields(data,'number','room_type','capacity')
                number=str(data['number']).strip(); room_type=str(data['room_type']).strip(); cap=data['capacity']
                if not number or not room_type or not isinstance(cap,int) or cap<=0:
                    raise APIError(400,'Número, tipo y capacidad positiva son obligatorios.')
                try:
                    cur=conn.execute("INSERT INTO rooms(number,room_type,capacity,state,active) VALUES(?,?,?,'disponible',1)",(number,room_type,cap))
                except sqlite3.IntegrityError:
                    raise APIError(409,'Ya existe una habitación con ese número.')
                room_id=cur.lastrowid
                space_cur=conn.execute("INSERT INTO spaces(name,kind,room_id,capacity) VALUES(?, 'habitacion', ?, ?)",(f'Habitación {number}',room_id,cap))
                sensor_id=f'sensor-hab-{room_id}'
                conn.execute('INSERT INTO sensors(sensor_id,space_id,active) VALUES(?,?,1)',(sensor_id,space_cur.lastrowid))
                audit(conn,user,'crear','habitación',room_id,f'{number} · {room_type} · capacidad {cap}')
                conn.commit()
                return response(start_response,201,{'room':serial(conn.execute('SELECT * FROM rooms WHERE id=?',(room_id,)).fetchone()),'space_id':space_cur.lastrowid,'sensor_id':sensor_id})
            m=re.fullmatch(r'/api/admin/rooms/(\d+)',path)
            if m and method=='PATCH':
                require_roles(user,'admin'); room_id=int(m.group(1))
                room=conn.execute('SELECT * FROM rooms WHERE id=?',(room_id,)).fetchone()
                if not room: raise APIError(404,'Habitación no encontrada.')
                number=str(data.get('number',room['number'])).strip(); room_type=str(data.get('room_type',room['room_type'])).strip(); cap=data.get('capacity',room['capacity'])
                if not number or not room_type or not isinstance(cap,int) or cap<=0: raise APIError(400,'Datos de habitación inválidos.')
                try:
                    conn.execute('UPDATE rooms SET number=?,room_type=?,capacity=? WHERE id=?',(number,room_type,cap,room_id))
                except sqlite3.IntegrityError:
                    raise APIError(409,'Ya existe otra habitación con ese número.')
                conn.execute("UPDATE spaces SET name=?,capacity=? WHERE room_id=?",(f'Habitación {number}',cap,room_id))
                audit(conn,user,'editar','habitación',room_id,f'{number} · {room_type} · capacidad {cap}')
                conn.commit()
                return response(start_response,200,serial(conn.execute('SELECT * FROM rooms WHERE id=?',(room_id,)).fetchone()))
            if m and method=='DELETE':
                require_roles(user,'admin'); room_id=int(m.group(1))
                room=conn.execute('SELECT * FROM rooms WHERE id=?',(room_id,)).fetchone()
                if not room: raise APIError(404,'Habitación no encontrada.')
                space=conn.execute('SELECT id FROM spaces WHERE room_id=?',(room_id,)).fetchone()
                linked_res=conn.execute('SELECT COUNT(*) FROM reservations WHERE room_id=?',(room_id,)).fetchone()[0]
                linked_clean=conn.execute('SELECT COUNT(*) FROM cleanings WHERE room_id=?',(room_id,)).fetchone()[0]
                linked_read=conn.execute('SELECT COUNT(*) FROM readings WHERE space_id=?',(space['id'],)).fetchone()[0] if space else 0
                linked_alert=conn.execute('SELECT COUNT(*) FROM alerts WHERE space_id=?',(space['id'],)).fetchone()[0] if space else 0
                if linked_res or linked_clean or linked_read or linked_alert:
                    raise APIError(409,'La habitación tiene historial asociado. Desactívala para retirarla de la operación sin perder su historial.')
                if space:
                    conn.execute('DELETE FROM sensors WHERE space_id=?',(space['id'],))
                    conn.execute('DELETE FROM spaces WHERE id=?',(space['id'],))
                conn.execute('DELETE FROM rooms WHERE id=?',(room_id,))
                audit(conn,user,'eliminar','habitación',room_id,room['number'])
                conn.commit()
                return response(start_response,200,{'message':'Habitación eliminada. También se eliminó su espacio monitorizado y sensor sin historial.','room_id':room_id})
            m=re.fullmatch(r'/api/admin/rooms/(\d+)/active',path)
            if m and method=='PATCH':
                require_roles(user,'admin'); room_id=int(m.group(1)); active=data.get('active')
                if active not in (0,1,True,False): raise APIError(400,'Estado activo inválido.')
                room=conn.execute('SELECT * FROM rooms WHERE id=?',(room_id,)).fetchone()
                if not room: raise APIError(404,'Habitación no encontrada.')
                if not active:
                    current=conn.execute("SELECT 1 FROM reservations WHERE room_id=? AND status='en_curso' LIMIT 1",(room_id,)).fetchone()
                    pending=conn.execute('SELECT 1 FROM cleanings WHERE room_id=? AND finished_at IS NULL LIMIT 1',(room_id,)).fetchone()
                    if current or pending: raise APIError(409,'No se puede retirar una habitación con una reserva o limpieza en curso.')
                conn.execute('UPDATE rooms SET active=? WHERE id=?',(int(active),room_id))
                audit(conn,user,'activar' if active else 'desactivar','habitación',room_id,room['number'])
                conn.commit()
                return response(start_response,200,serial(conn.execute('SELECT * FROM rooms WHERE id=?',(room_id,)).fetchone()))
            m=re.fullmatch(r'/api/admin/rooms/(\d+)/state',path)
            if m and method=='POST':
                require_roles(user,'admin'); room_id=int(m.group(1)); target_state=data.get('state')
                if target_state not in ('disponible','en limpieza'):
                    raise APIError(400,'Para demostrar el estado ocupada debes registrar un check-in. Aquí solo se permiten disponible o en limpieza.')
                room=conn.execute('SELECT * FROM rooms WHERE id=? AND active=1',(room_id,)).fetchone()
                if not room: raise APIError(404,'Habitación no encontrada o inactiva.')
                active_res=conn.execute("SELECT 1 FROM reservations WHERE room_id=? AND status='en_curso' LIMIT 1",(room_id,)).fetchone()
                pending=conn.execute('SELECT 1 FROM cleanings WHERE room_id=? AND finished_at IS NULL LIMIT 1',(room_id,)).fetchone()
                if active_res or room['state']=='ocupada': raise APIError(409,'No se puede cambiar manualmente una habitación ocupada; registra el check-out.')
                if target_state=='disponible' and pending: raise APIError(409,'Primero finaliza el registro de limpieza pendiente.')
                conn.execute('UPDATE rooms SET state=? WHERE id=?',(target_state,room_id))
                audit(conn,user,'forzar estado','habitación',room_id,target_state); conn.commit()
                return response(start_response,200,{'message':f'Estado actualizado a {target_state}.','room_id':room_id,'state':target_state})
            # Sensor administration supports disabling/replacing sensors without erasing history.
            if path == '/api/admin/sensors' and method == 'POST':
                require_roles(user,'admin'); require_fields(data,'sensor_id','space_id')
                sensor_id=str(data['sensor_id']).strip(); space_id=int(data['space_id'])
                if not re.fullmatch(r'[A-Za-z0-9_.-]{3,80}',sensor_id): raise APIError(400,'El ID del sensor debe tener entre 3 y 80 caracteres y usar letras, números, punto, guion o guion bajo.')
                if not conn.execute('SELECT id FROM spaces WHERE id=?',(space_id,)).fetchone(): raise APIError(404,'Espacio no encontrado.')
                if conn.execute('SELECT 1 FROM sensors WHERE sensor_id=?',(sensor_id,)).fetchone(): raise APIError(409,'Ese identificador de sensor ya existe.')
                if conn.execute('SELECT 1 FROM sensors WHERE space_id=? AND active=1',(space_id,)).fetchone(): raise APIError(409,'El espacio ya tiene un sensor activo. Desactívalo antes de asociar otro.')
                conn.execute('INSERT INTO sensors(sensor_id,space_id,active) VALUES(?,?,1)',(sensor_id,space_id))
                audit(conn,user,'crear','sensor',sensor_id,f'espacio {space_id}')
                conn.commit()
                return response(start_response,201,serial(conn.execute('SELECT * FROM sensors WHERE sensor_id=?',(sensor_id,)).fetchone()))
            m=re.fullmatch(r'/api/admin/sensors/([A-Za-z0-9_.-]+)',path)
            if m and method=='PATCH':
                require_roles(user,'admin'); sensor_id=m.group(1)
                sensor=conn.execute('SELECT * FROM sensors WHERE sensor_id=?',(sensor_id,)).fetchone()
                if not sensor: raise APIError(404,'Sensor no encontrado.')
                active=data.get('active',sensor['active'])
                if active not in (0,1,True,False): raise APIError(400,'Estado activo inválido.')
                if active and conn.execute('SELECT 1 FROM sensors WHERE space_id=? AND active=1 AND sensor_id<>?',(sensor['space_id'],sensor_id)).fetchone():
                    raise APIError(409,'El espacio ya tiene otro sensor activo.')
                conn.execute('UPDATE sensors SET active=? WHERE sensor_id=?',(int(active),sensor_id))
                audit(conn,user,'activar' if active else 'desactivar','sensor',sensor_id)
                conn.commit()
                return response(start_response,200,serial(conn.execute('SELECT * FROM sensors WHERE sensor_id=?',(sensor_id,)).fetchone()))
            if m and method=='DELETE':
                require_roles(user,'admin'); sensor_id=m.group(1)
                sensor=conn.execute('SELECT * FROM sensors WHERE sensor_id=?',(sensor_id,)).fetchone()
                if not sensor: raise APIError(404,'Sensor no encontrado.')
                history=conn.execute('SELECT COUNT(*) FROM readings WHERE sensor_id=?',(sensor_id,)).fetchone()[0]
                if history:
                    conn.execute('UPDATE sensors SET active=0 WHERE sensor_id=?',(sensor_id,))
                    result='El sensor tenía lecturas históricas y fue desactivado para conservarlas.'
                    action='desactivar por historial'
                else:
                    conn.execute('DELETE FROM sensors WHERE sensor_id=?',(sensor_id,))
                    result='Sensor eliminado.'; action='eliminar'
                audit(conn,user,action,'sensor',sensor_id)
                conn.commit()
                return response(start_response,200,{'message':result,'sensor_id':sensor_id})
            # Explicit reset for repeatable manual demos; configuration/users/rooms are preserved.
            if path == '/api/admin/reset-operational-data' and method == 'POST':
                require_roles(user,'admin')
                if data.get('confirm')!='LIMPIAR DATOS OPERATIVOS': raise APIError(400,'Escribe la frase exacta de confirmación para limpiar los datos operativos.')
                conn.execute('DELETE FROM alerts'); conn.execute('DELETE FROM readings'); conn.execute('DELETE FROM cleanings')
                conn.execute('DELETE FROM reservations'); conn.execute('DELETE FROM guests')
                conn.execute("UPDATE rooms SET state='disponible' WHERE active=1")
                audit(conn,user,'limpiar datos operativos','sistema',None,'Se conservaron usuarios, habitaciones, espacios, sensores y capacidades.')
                conn.commit()
                return response(start_response,200,{'message':'Datos operativos de demostración eliminados. Se conservaron usuarios, habitaciones, espacios, sensores y capacidades.'})
            if path == '/api/admin/audit' and method == 'GET':
                require_roles(user,'admin')
                rows=[serial(r) for r in conn.execute('SELECT * FROM admin_audit ORDER BY id DESC LIMIT 200').fetchall()]
                return response(start_response,200,rows)
            m=re.fullmatch(r'/api/admin/rooms/(\d+)/prepare-cleaning',path)
            if m and method == 'POST':
                require_roles(user,'admin')
                room_id=int(m.group(1)); room=conn.execute('SELECT * FROM rooms WHERE id=?',(room_id,)).fetchone()
                if not room: raise APIError(404,'Habitación no encontrada.')
                active=conn.execute("SELECT 1 FROM reservations WHERE room_id=? AND status='en_curso' LIMIT 1",(room_id,)).fetchone()
                if active or room['state']=='ocupada': raise APIError(409,'La habitación tiene una reserva en curso o está ocupada. No se puede forzar a limpieza.')
                pending=conn.execute('SELECT 1 FROM cleanings WHERE room_id=? AND finished_at IS NULL LIMIT 1',(room_id,)).fetchone()
                if pending: raise APIError(409,'Ya existe una limpieza iniciada y pendiente para esta habitación.')
                conn.execute("UPDATE rooms SET state='en limpieza' WHERE id=?",(room_id,)); audit(conn,user,'forzar estado en limpieza','habitación',room_id); conn.commit()
                return response(start_response,200,{'message':'Habitación preparada en estado “en limpieza”. Ahora puedes registrar el inicio y finalizarla para demostrar RF-05.','room_id':room_id,'state':'en limpieza'})
            # Users and roles
            if path == '/api/users' and method == 'GET':
                require_roles(user,'admin'); return response(start_response,200,[serial(r) for r in conn.execute('SELECT id,username,role,active FROM users ORDER BY id').fetchall()])
            if path == '/api/users' and method == 'POST':
                require_roles(user,'admin'); require_fields(data,'username','password','role')
                username=str(data['username']).strip(); password=str(data['password']); role=data['role']
                if not username or len(username)>60 or len(password)<6: raise APIError(400,'Usuario requerido (máximo 60 caracteres) y contraseña de al menos 6 caracteres.')
                if role not in ROLES: raise APIError(400,'Rol inválido.')
                try:
                    cur=conn.execute('INSERT INTO users(username,password_hash,role,active) VALUES(?,?,?,1)',(username,password_hash(password),role))
                except sqlite3.IntegrityError:
                    raise APIError(409,'El nombre de usuario ya existe.')
                audit(conn,user,'crear','usuario',cur.lastrowid,username+' · '+role); conn.commit()
                return response(start_response,201,serial(conn.execute('SELECT id,username,role,active FROM users WHERE id=?',(cur.lastrowid,)).fetchone()))
            m=re.fullmatch(r'/api/users/(\d+)',path)
            if m and method=='PATCH':
                require_roles(user,'admin'); target=int(m.group(1)); row=conn.execute('SELECT * FROM users WHERE id=?',(target,)).fetchone()
                if not row: raise APIError(404,'Usuario no encontrado.')
                username=str(data.get('username',row['username'])).strip(); role=data.get('role',row['role']); active=data.get('active',row['active'])
                if not username or len(username)>60 or role not in ROLES or active not in (0,1,True,False): raise APIError(400,'Usuario, rol o estado inválido.')
                if target==user['id'] and (not active or role!='admin'): raise APIError(409,'No puedes desactivar ni quitar el rol Administrador de tu propia sesión.')
                if row['role']=='admin' and row['active'] and (not active or role!='admin'):
                    admins=conn.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND active=1").fetchone()[0]
                    if admins<=1: raise APIError(409,'Debe permanecer al menos un Administrador activo.')
                try:
                    conn.execute('UPDATE users SET username=?,role=?,active=? WHERE id=?',(username,role,int(active),target))
                except sqlite3.IntegrityError:
                    raise APIError(409,'Ese nombre de usuario ya existe.')
                if data.get('password'):
                    password=str(data['password'])
                    if len(password)<6: raise APIError(400,'La contraseña debe tener al menos 6 caracteres.')
                    conn.execute('UPDATE users SET password_hash=? WHERE id=?',(password_hash(password),target))
                audit(conn,user,'editar','usuario',target,f'{username} · {role} · activo={int(active)}'); conn.commit()
                return response(start_response,200,serial(conn.execute('SELECT id,username,role,active FROM users WHERE id=?',(target,)).fetchone()))
            m=re.fullmatch(r'/api/users/(\d+)',path)
            if m and method=='DELETE':
                require_roles(user,'admin'); target=int(m.group(1))
                row=conn.execute('SELECT * FROM users WHERE id=?',(target,)).fetchone()
                if not row: raise APIError(404,'Usuario no encontrado.')
                if target==user['id']: raise APIError(409,'No puedes eliminar la cuenta con la que has iniciado sesión.')
                if row['role']=='admin' and row['active'] and conn.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND active=1").fetchone()[0]<=1:
                    raise APIError(409,'Debe permanecer al menos un Administrador activo.')
                refs=sum(conn.execute(q,(target,)).fetchone()[0] for q in [
                    'SELECT COUNT(*) FROM reservations WHERE created_by=?',
                    'SELECT COUNT(*) FROM cleanings WHERE user_id=?',
                    'SELECT COUNT(*) FROM alerts WHERE reviewed_by=?'])
                if refs: raise APIError(409,'El usuario tiene historial asociado. Desactívalo para conservar la trazabilidad.')
                audit_refs=conn.execute('SELECT COUNT(*) FROM admin_audit WHERE user_id=?',(target,)).fetchone()[0]
                if audit_refs: raise APIError(409,'El usuario tiene operaciones registradas en la bitácora. Desactívalo para conservar la trazabilidad.')
                conn.execute('DELETE FROM users WHERE id=?',(target,)); audit(conn,user,'eliminar','usuario',target,row['username']); conn.commit()
                return response(start_response,200,{'message':'Usuario eliminado.','user_id':target})
            # Capacity
            m=re.fullmatch(r'/api/spaces/(\d+)/capacity',path)
            if m and method=='POST':
                require_roles(user,'admin'); cap=data.get('capacity')
                if not isinstance(cap,int) or cap<=0: raise APIError(400,'La capacidad debe ser un entero mayor que cero.')
                space=conn.execute('SELECT * FROM spaces WHERE id=?',(m.group(1),)).fetchone()
                if not space: raise APIError(404,'Espacio no encontrado.')
                if space['kind']=='piscina': conn.execute('UPDATE spaces SET capacity=? WHERE id=?',(cap,space['id']))
                else:
                    conn.execute('UPDATE rooms SET capacity=? WHERE id=?',(cap,space['room_id']))
                    conn.execute('UPDATE spaces SET capacity=? WHERE id=?',(cap,space['id']))
                audit(conn,user,'cambiar capacidad','espacio',space['id'],str(cap)); conn.commit(); return response(start_response,200,{'space_id':space['id'],'capacity':cap})
            # Sensor readings and occupancy
            # >>> PRESENTACIÓN 2 | RECEPCIÓN DE DATOS
            # El servidor recibe la lectura, valida el sensor y el conteo,
            # guarda los datos y comprueba si debe generar una alerta.
            if path == '/api/readings' and method == 'POST':
                require_fields(data,'sensor_id','count')
                allowed={'sensor_id','count','timestamp'}
                if set(data)-allowed: raise APIError(400,'La lectura solo admite sensor_id, count y timestamp; no se reciben imágenes ni datos personales.')
                count=data['count']
                if isinstance(count,bool) or not isinstance(count,int) or count<0: raise APIError(400,'El conteo debe ser un entero igual o mayor que cero.')
                sensor=conn.execute("SELECT s.*,p.capacity,p.kind,p.name,rm.active AS room_active FROM sensors s JOIN spaces p ON p.id=s.space_id LEFT JOIN rooms rm ON rm.id=p.room_id WHERE s.sensor_id=? AND s.active=1 AND (p.kind='piscina' OR rm.active=1)",(data['sensor_id'],)).fetchone()
                if not sensor: raise APIError(400,'Sensor no identificado o inactivo; no se modifica el último conteo válido.')
                received_at=data.get('timestamp') or current_time(); parse_dt(received_at)
                cur=conn.execute('INSERT INTO readings(sensor_id,space_id,people_count,received_at) VALUES(?,?,?,?)',(sensor['sensor_id'],sensor['space_id'],count,received_at))
                if user and user['role']=='admin': audit(conn,user,'enviar lectura','sensor',sensor['sensor_id'],f'conteo {count}')
                cap=sensor['capacity']; level=classify_occupancy(count,cap)
                alert_id=None
                if level in ('completo','excedido'):
                    a=conn.execute('INSERT INTO alerts(space_id,reading_id,people_count,capacity,level,created_at) VALUES(?,?,?,?,?,?)',(sensor['space_id'],cur.lastrowid,count,cap,level,received_at)); alert_id=a.lastrowid
                conn.commit()
                return response(start_response,201,{'reading_id':cur.lastrowid,'space_id':sensor['space_id'],'space':sensor['name'],'count':count,'capacity':cap,'state':level,'alert_id':alert_id,'received_at':received_at})
            # PRESENTACIÓN: esta ruta devuelve el estado actual de los espacios.
            if path == '/api/occupancy' and method == 'GET':
                require_roles(user,'recepcion','admin','limpieza')
                return response(start_response,200,occupancy_data(conn,current_time()))
            # >>> PRESENTACIÓN 5 | CONSULTA DE ALERTAS
            # Permite consultar las alertas y saber cuáles siguen pendientes.
            if path == '/api/alerts' and method == 'GET':
                require_roles(user,'recepcion','admin')
                rows=conn.execute('SELECT a.*,s.name AS space_name,u.username AS reviewed_by_name FROM alerts a JOIN spaces s ON s.id=a.space_id LEFT JOIN users u ON u.id=a.reviewed_by ORDER BY a.id DESC').fetchall()
                return response(start_response,200,[serial(r) for r in rows])
            m=re.fullmatch(r'/api/alerts/(\d+)/review',path)
            if m and method=='POST':
                require_roles(user,'recepcion','admin'); alert=conn.execute('SELECT * FROM alerts WHERE id=?',(m.group(1),)).fetchone()
                if not alert: raise APIError(404,'Alerta no encontrada.')
                if alert['reviewed_at']: raise APIError(409,'La alerta ya fue revisada.')
                conn.execute('UPDATE alerts SET reviewed_by=?,reviewed_at=?,observation=? WHERE id=?',(user['id'],current_time(),str(data.get('observation','')),alert['id']));
                if user['role']=='admin': audit(conn,user,'revisar alerta','alerta',alert['id'])
                conn.commit()
                return response(start_response,200,{'message':'Alerta marcada como revisada.','alert_id':alert['id'],'aforo_state':alert['level']})
            raise APIError(404,'Ruta no encontrada.')
        except APIError as exc:
            return response(start_response,exc.status,{'error':exc.message})
        except Exception as exc:
            return response(start_response,500,{'error':'Error interno del servidor.','detail':str(exc)})
        finally:
            conn.close()
    return app

def first(q, key):
    vals=q.get(key)
    if not vals or not vals[0]: raise APIError(400,f'Falta el parámetro {key}.')
    return vals[0]
def require_fields(data,*fields):
    if not isinstance(data,dict): raise APIError(400,'Se esperaba un objeto JSON.')
    missing=[f for f in fields if f not in data or data[f] in (None,'')]
    if missing: raise APIError(400,'Faltan campos obligatorios: '+', '.join(missing))
def require_user(user):
    if not user or not user['active']: raise APIError(401,'Debe iniciar sesión.')
def require_roles(user,*roles):
    require_user(user)
    if user['role'] not in roles: raise APIError(403,'No tiene permisos para realizar esta acción.')
def dashboard_data(conn, current_time):
    rooms=[serial(r) for r in conn.execute('SELECT * FROM rooms WHERE active=1 ORDER BY number').fetchall()]
    occ=occupancy_data(conn,current_time)
    return {'rooms':rooms,'occupancy':occ,'pending_alerts':conn.execute('SELECT COUNT(*) FROM alerts WHERE reviewed_at IS NULL').fetchone()[0], 'counts':{'rooms':len(rooms),'guests':conn.execute('SELECT COUNT(*) FROM guests').fetchone()[0],'reservations':conn.execute("SELECT COUNT(*) FROM reservations WHERE status='confirmada'").fetchone()[0]}}
def occupancy_data(conn,current_time):
    now=parse_dt(current_time); out=[]
    spaces=conn.execute("SELECT p.*,s.sensor_id FROM spaces p LEFT JOIN sensors s ON s.space_id=p.id LEFT JOIN rooms rm ON rm.id=p.room_id WHERE p.kind='piscina' OR rm.active=1 ORDER BY p.kind,p.name").fetchall()
    for p in spaces:
        last=conn.execute('SELECT * FROM readings WHERE space_id=? ORDER BY received_at DESC,id DESC LIMIT 1',(p['id'],)).fetchone()
        if not last: state='sin datos'; count=None; received=None
        else:
            received=last['received_at']; count=last['people_count']; state='desactualizado' if is_reading_stale(now,parse_dt(received)) else classify_occupancy(count,p['capacity'])
        out.append({'space_id':p['id'],'name':p['name'],'kind':p['kind'],'capacity':p['capacity'],'count':count,'received_at':received,'state':state,'sensor_id':p['sensor_id']})
    return out

class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True

def _preferred_lan_ip():
    """Best-effort IPv4 used by this machine for its default network route."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(('192.0.2.1', 80))  # TEST-NET address; no packet is sent.
        return probe.getsockname()[0]
    except OSError:
        return 'IP_DE_TU_PC'
    finally:
        probe.close()


def run_server(host=None,port=None):
    # Local-only is the safe default. Use run_red_local.bat to listen on LAN interfaces.
    host = host or os.environ.get('CASA_OGRO_HOST', '127.0.0.1')
    port = int(port or os.environ.get('CASA_OGRO_PORT', '8000'))
    app=create_application()
    if host in ('0.0.0.0', ''):
        lan_ip = _preferred_lan_ip()
        print('La Casa del Ogro está escuchando en las interfaces de red de este equipo.')
        print(f'En este PC: http://127.0.0.1:{port}')
        print(f'Desde otros equipos de la misma red permitida: http://{lan_ip}:{port}')
        print('Si no conecta, revisa Firewall de Windows y las reglas de la red institucional.')
    else:
        print(f'La Casa del Ogro disponible solo en este PC: http://127.0.0.1:{port}')
    print('Cuentas demo: admin/admin123 | recepcion/recep123 | limpieza/limp123')
    with make_server(host,port,app,server_class=ThreadingWSGIServer) as server: server.serve_forever()

if __name__=='__main__': run_server()
