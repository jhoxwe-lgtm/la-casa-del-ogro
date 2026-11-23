from concurrent.futures import ThreadPoolExecutor
import time
from .conftest import WSGIClient, guest, reservation, room_id

# RF-01: registrar una reserva con huésped, habitación y fechas.
def test_RF01_registrar_reserva(client):
    rid,_=reservation(client)
    status,rows,_=client.request('GET','/api/reservations')
    assert status==200 and any(r['id']==rid and r['status']=='confirmada' for r in rows)

# RF-02: consultar disponibilidad sin reservas superpuestas.
def test_RF02_disponibilidad_excluye_reserva_superpuesta(client):
    reservation(client)
    status,rooms,_=client.request('GET','/api/availability?checkin=2026-11-25T15:00:00-03:00&checkout=2026-11-27T12:00:00-03:00')
    assert status==200 and all(r['number']!='101' for r in rooms)

# RF-03: registrar datos básicos de huésped.
def test_RF03_registrar_huesped(client):
    gid=guest(client); status,rows,_=client.request('GET','/api/guests')
    assert status==200 and any(r['id']==gid and r['email']=='ana@example.com' for r in rows)

# RF-04: consultar el estado vigente de todas las habitaciones.
def test_RF04_consultar_estado_habitaciones(client):
    status,rooms,_=client.request('GET','/api/rooms')
    assert status==200 and {'disponible','ocupada','en limpieza'} >= {r['state'] for r in rooms}

# RF-05: limpieza termina y libera la habitación.
def test_RF05_finalizar_limpieza_libera_habitacion(client, clock):
    rid,rid_room=reservation(client,checkin='2026-11-25T15:00:00-03:00',checkout='2026-11-26T12:00:00-03:00')
    clock['value']='2026-11-25T15:30:00-03:00'; assert client.request('POST',f'/api/reservations/{rid}/check-in',{})[0]==200
    clock['value']='2026-11-26T11:30:00-03:00'; assert client.request('POST',f'/api/reservations/{rid}/check-out',{})[0]==200
    cleaner=WSGIClient(client.app); assert cleaner.login('limpieza','limp123')[0]==200
    status,_,_=cleaner.request('POST',f'/api/rooms/{rid_room}/cleaning/start',{})
    assert status==201
    status,data,_=cleaner.request('POST',f'/api/rooms/{rid_room}/cleaning/finish',{})
    assert status==200
    _,room,_=client.request('GET',f'/api/rooms/{rid_room}')
    assert room['state']=='disponible'

# RF-06: recibir y asociar una lectura con sensor, espacio, fecha/hora y conteo.
def test_RF06_recibir_lectura_sensor(client):
    status,data,_=client.request('POST','/api/readings',{'sensor_id':'sensor-piscina','count':17,'timestamp':'2026-11-17T10:29:55-03:00'})
    assert status==201 and data['count']==17 and data['space']=='Piscina' and data['received_at']

# RF-07: consultar último conteo registrado.
def test_RF07_consultar_ultimo_conteo(client):
    client.request('POST','/api/readings',{'sensor_id':'sensor-piscina','count':16})
    client.request('POST','/api/readings',{'sensor_id':'sensor-piscina','count':18})
    status,rows,_=client.request('GET','/api/occupancy')
    pool=next(x for x in rows if x['kind']=='piscina')
    assert status==200 and pool['count']==18

# RF-08: crear, modificar rol y desactivar una cuenta.
def test_RF08_gestionar_usuarios_y_roles(client):
    admin=WSGIClient(client.app); assert admin.login('admin','admin123')[0]==200
    status,u,_=admin.request('POST','/api/users',{'username':'nuevo','password':'clave123','role':'limpieza'})
    assert status==201
    status,u,_=admin.request('PATCH',f"/api/users/{u['id']}",{'role':'recepcion'})
    assert status==200 and u['role']=='recepcion'
    status,u,_=admin.request('PATCH',f"/api/users/{u['id']}",{'active':False})
    assert status==200 and u['active']==0

# RF-09: iniciar sesión con credenciales válidas e inválidas.
def test_RF09_inicio_sesion_valida_e_invalida(client):
    other=WSGIClient(client.app)
    assert other.request('POST','/api/login',{'username':'recepcion','password':'incorrecta'})[0]==401
    assert other.login()[0]==200

# RF-10: check-in desde las 15:00; autorización administrativa para anticipos.
def test_RF10_checkin_regla_horaria(client, clock):
    rid,_=reservation(client,checkin='2026-11-17T15:00:00-03:00',checkout='2026-11-19T12:00:00-03:00')
    clock['value']='2026-11-17T14:00:00-03:00'
    assert client.request('POST',f'/api/reservations/{rid}/check-in',{})[0]==403
    admin=WSGIClient(client.app); assert admin.login('admin','admin123')[0]==200
    assert admin.request('POST',f'/api/reservations/{rid}/check-in',{})[0]==200

# RF-11: check-out hasta las 12:00 y transición a limpieza.
def test_RF11_checkout_y_estado_limpieza(client, clock):
    rid,rid_room=reservation(client,checkin='2026-11-17T15:00:00-03:00',checkout='2026-11-18T12:00:00-03:00')
    clock['value']='2026-11-17T15:30:00-03:00'; assert client.request('POST',f'/api/reservations/{rid}/check-in',{})[0]==200
    clock['value']='2026-11-18T12:00:00-03:00'; assert client.request('POST',f'/api/reservations/{rid}/check-out',{})[0]==200
    _,room,_=client.request('GET',f'/api/rooms/{rid_room}')
    assert room['state']=='en limpieza'

# RF-12: modificar reserva; exige Administrador dentro de las últimas 24 horas.
def test_RF12_modificar_reserva(client, clock):
    rid,_=reservation(client,checkin='2026-11-25T15:00:00-03:00',checkout='2026-11-27T12:00:00-03:00')
    status,data,_=client.request('POST',f'/api/reservations/{rid}/modify',{'checkin':'2026-11-26T15:00:00-03:00','checkout':'2026-11-28T12:00:00-03:00'})
    assert status==200 and data['checkin'].startswith('2026-11-26')
    clock['value']='2026-11-26T14:30:00-03:00'
    assert client.request('POST',f'/api/reservations/{rid}/modify',{'checkin':'2026-11-27T15:00:00-03:00'})[0]==403

# RF-13: cancelar reserva y liberar disponibilidad.
def test_RF13_cancelar_reserva(client):
    rid,_=reservation(client)
    status,data,_=client.request('POST',f'/api/reservations/{rid}/cancel',{})
    assert status==200 and data['reservation']['status']=='cancelada'

# RF-14: configurar capacidad máxima de piscina y habitaciones.
def test_RF14_configurar_capacidad(client):
    admin=WSGIClient(client.app); assert admin.login('admin','admin123')[0]==200
    status,spaces,_=admin.request('GET','/api/occupancy')
    pool=next(s for s in spaces if s['kind']=='piscina')
    status,data,_=admin.request('POST',f"/api/spaces/{pool['space_id']}/capacity",{'capacity':25})
    assert status==200 and data['capacity']==25

# RF-15: comparar una lectura nueva con la capacidad configurada.
def test_RF15_comparar_conteo_y_capacidad(client):
    status,data,_=client.request('POST','/api/readings',{'sensor_id':'sensor-piscina','count':19})
    assert status==201 and data['capacity']==20 and data['state']=='normal'

# RF-16: generar estado completo/excedido y persistir alerta.
def test_RF16_generar_alerta_al_alcanzar_o_superar_capacidad(client):
    assert client.request('POST','/api/readings',{'sensor_id':'sensor-piscina','count':20})[1]['state']=='completo'
    status,data,_=client.request('POST','/api/readings',{'sensor_id':'sensor-piscina','count':21})
    assert status==201 and data['state']=='excedido' and data['alert_id'] is not None

# RF-17: revisar alerta sin borrar la condición de aforo.
def test_RF17_revisar_alerta_conserva_estado(client):
    _,reading,_=client.request('POST','/api/readings',{'sensor_id':'sensor-piscina','count':21})
    status,data,_=client.request('POST',f"/api/alerts/{reading['alert_id']}/review",{'observation':'Se avisó al responsable.'})
    assert status==200 and data['aforo_state']=='excedido'
    _,alerts,_=client.request('GET','/api/alerts')
    assert alerts[0]['reviewed_at'] is not None

# RNF-01: los permisos por rol impiden operaciones ajenas y no modifican datos.
def test_RNF01_permisos_por_rol(client):
    limpieza=WSGIClient(client.app); assert limpieza.login('limpieza','limp123')[0]==200
    status,_,_=limpieza.request('POST','/api/guests',{'first_name':'X','last_name':'Y','phone':'1','email':'x@y.cl'})
    assert status==403

# RNF-02: hasta 10 sesiones consultan datos en menos de 3 segundos en entorno local.
def test_RNF02_rendimiento_diez_consultas_concurrentes(client):
    sessions=[]
    for _ in range(10):
        c=WSGIClient(client.app)
        assert c.login('recepcion','recep123')[0]==200
        sessions.append(c)
    start=time.perf_counter()
    with ThreadPoolExecutor(max_workers=10) as pool:
        statuses=list(pool.map(lambda c:c.request('GET','/api/dashboard')[0],sessions))
    elapsed=time.perf_counter()-start
    assert statuses==[200]*10 and elapsed<3.0

# RNF-03: prueba de disponibilidad básica; no demuestra el 99% mensual.
def test_RNF03_servicio_responde_healthcheck(client):
    c=WSGIClient(client.app); status,data,_=c.request('GET','/health')
    assert status==200 and data['status']=='ok'

# RNF-04: estado de habitación accesible desde el panel con un acceso a Habitaciones.
def test_RNF04_panel_entrega_estado_de_habitaciones(client):
    status,data,_=client.request('GET','/api/dashboard')
    assert status==200 and len(data['rooms'])>=1 and all('state' in r for r in data['rooms'])

# RNF-05: lectura aparece en consulta del panel en menos de 10 segundos.
def test_RNF05_lectura_visible_en_menos_de_diez_segundos(client):
    start=time.perf_counter()
    status,reading,_=client.request('POST','/api/readings',{'sensor_id':'sensor-piscina','count':12})
    status2,spaces,_=client.request('GET','/api/occupancy')
    elapsed=time.perf_counter()-start
    pool=next(s for s in spaces if s['kind']=='piscina')
    assert status==201 and status2==200 and pool['count']==12 and elapsed<10

# RNF-06: conteo de más de 2 minutos se marca desactualizado.
def test_RNF06_conteo_antiguo_marcado_desactualizado(client, clock):
    clock['value']='2026-11-17T10:03:01-03:00'
    client.request('POST','/api/readings',{'sensor_id':'sensor-piscina','count':12,'timestamp':'2026-11-17T10:00:00-03:00'})
    _,spaces,_=client.request('GET','/api/occupancy')
    pool=next(s for s in spaces if s['kind']=='piscina')
    assert pool['state']=='desactualizado'

# RNF-07: interfaz de sensor acepta solo conteo, sensor y fecha/hora; no imágenes ni identidades.
def test_RNF07_lectura_no_acepta_imagenes_ni_datos_personales(client):
    status,data,_=client.request('POST','/api/readings',{'sensor_id':'sensor-piscina','count':10,'image':'foto.jpg','guest_name':'Ana'})
    assert status==400 and 'no se reciben imágenes' in data['error']

# CP adicional: límite de salida después de las 12:00 requiere autorización.
def test_RF11B_checkout_tardio_requiere_administrador(client, clock):
    rid,_=reservation(client,checkin='2026-11-17T15:00:00-03:00',checkout='2026-11-18T12:00:00-03:00')
    clock['value']='2026-11-17T15:30:00-03:00'; assert client.request('POST',f'/api/reservations/{rid}/check-in',{})[0]==200
    clock['value']='2026-11-18T13:00:00-03:00'; assert client.request('POST',f'/api/reservations/{rid}/check-out',{})[0]==403
    admin=WSGIClient(client.app); assert admin.login('admin','admin123')[0]==200
    assert admin.request('POST',f'/api/reservations/{rid}/check-out',{})[0]==200

# CP adicional: el Administrador puede autorizar una modificación dentro de las últimas 24 horas.
def test_RF12B_modificacion_tardia_autorizada(client, clock):
    rid,_=reservation(client,checkin='2026-11-18T15:00:00-03:00',checkout='2026-11-20T12:00:00-03:00')
    clock['value']='2026-11-18T10:00:00-03:00'
    assert client.request('POST',f'/api/reservations/{rid}/modify',{'checkin':'2026-11-19T15:00:00-03:00'})[0]==403
    admin=WSGIClient(client.app); assert admin.login('admin','admin123')[0]==200
    status,data,_=admin.request('POST',f'/api/reservations/{rid}/modify',{'checkin':'2026-11-19T15:00:00-03:00'})
    assert status==200 and data['checkin'].startswith('2026-11-19')

# CP adicional: cancelar dentro de las últimas 24 horas exige Administrador.
def test_RF13B_cancelacion_tardia_requiere_administrador(client, clock):
    rid,_=reservation(client,checkin='2026-11-18T15:00:00-03:00',checkout='2026-11-20T12:00:00-03:00')
    clock['value']='2026-11-18T10:00:00-03:00'
    assert client.request('POST',f'/api/reservations/{rid}/cancel',{})[0]==403
    admin=WSGIClient(client.app); assert admin.login('admin','admin123')[0]==200
    status,data,_=admin.request('POST',f'/api/reservations/{rid}/cancel',{})
    assert status==200 and data['reservation']['status']=='cancelada'

# CP adicional: una lectura de sensor no identificado no sustituye el último conteo válido.
def test_RF06B_sensor_desconocido_no_actualiza_conteo(client):
    client.request('POST','/api/readings',{'sensor_id':'sensor-piscina','count':17})
    status,_,_=client.request('POST','/api/readings',{'sensor_id':'sensor-desconocido','count':21})
    _,spaces,_=client.request('GET','/api/occupancy')
    pool=next(x for x in spaces if x['kind']=='piscina')
    assert status==400 and pool['count']==17

# CP adicional: capacidad de habitación se actualiza y se utiliza para su sensor.
def test_RF14B_configurar_capacidad_habitacion(client):
    admin=WSGIClient(client.app); assert admin.login('admin','admin123')[0]==200
    _,spaces,_=admin.request('GET','/api/occupancy')
    room_space=next(s for s in spaces if s['kind']=='habitacion' and s['name']=='Habitación 101')
    status,_,_=admin.request('POST',f"/api/spaces/{room_space['space_id']}/capacity",{'capacity':3})
    assert status==200
    status,reading,_=admin.request('POST','/api/readings',{'sensor_id':'sensor-hab-1','count':3})
    assert status==201 and reading['capacity']==3 and reading['state']=='completo'

# CP adicional: exactamente 2 minutos todavía no excede el umbral de RNF-06.
def test_RNF06B_exactamente_dos_minutos_no_esta_desactualizado(client, clock):
    clock['value']='2026-11-17T10:02:00-03:00'
    client.request('POST','/api/readings',{'sensor_id':'sensor-piscina','count':11,'timestamp':'2026-11-17T10:00:00-03:00'})
    _,spaces,_=client.request('GET','/api/occupancy')
    pool=next(s for s in spaces if s['kind']=='piscina')
    assert pool['state']=='normal'

# Panel administrativo: edicion y eliminacion reflejadas en la misma base de datos.
def admin_client(client):
    admin=WSGIClient(client.app)
    assert admin.login('admin','admin123')[0]==200
    return admin

def test_ADMIN01_panel_de_gestion_solo_administrador(client):
    assert client.request('GET','/api/admin/management')[0]==403
    admin=admin_client(client)
    status,data,_=admin.request('GET','/api/admin/management')
    assert status==200 and {'guests','reservations','rooms'} <= set(data)

def test_ADMIN02_editar_huesped_actualiza_registro_principal(client):
    gid=guest(client); admin=admin_client(client)
    status,data,_=admin.request('PATCH',f'/api/guests/{gid}',{'first_name':'Ana Maria','last_name':'Editada','phone':'999','email':'editada@example.com'})
    assert status==200 and data['first_name']=='Ana Maria' and data['email']=='editada@example.com'
    _,rows,_=admin.request('GET','/api/guests')
    assert any(x['id']==gid and x['last_name']=='Editada' for x in rows)

def test_ADMIN03_eliminar_huesped_sin_reservas(client):
    gid=guest(client); admin=admin_client(client)
    status,data,_=admin.request('DELETE',f'/api/guests/{gid}')
    assert status==200 and data['guest_id']==gid
    _,rows,_=admin.request('GET','/api/guests')
    assert all(x['id']!=gid for x in rows)

def test_ADMIN04_no_eliminar_huesped_con_reservas_asociadas(client):
    _,_=reservation(client); admin=admin_client(client)
    _,rows,_=admin.request('GET','/api/guests')
    gid=rows[0]['id']
    status,data,_=admin.request('DELETE',f'/api/guests/{gid}')
    assert status==409 and 'reservas asociadas' in data['error']

def test_ADMIN05_editar_reserva_confirmada(client):
    rid,_=reservation(client); admin=admin_client(client)
    status,data,_=admin.request('PATCH',f'/api/reservations/{rid}',{'checkin':'2026-11-26T15:00:00-03:00','checkout':'2026-11-28T12:00:00-03:00'})
    assert status==200 and data['checkin'].startswith('2026-11-26')
    _,rows,_=admin.request('GET','/api/reservations')
    assert any(x['id']==rid and x['checkin'].startswith('2026-11-26') for x in rows)

def test_ADMIN06_eliminar_reserva_y_liberar_huesped_para_borrado(client):
    rid,_=reservation(client); admin=admin_client(client)
    _,rows,_=admin.request('GET','/api/admin/management')
    gid=next(x['guest_id'] for x in rows['reservations'] if x['id']==rid)
    status,data,_=admin.request('DELETE',f'/api/reservations/{rid}')
    assert status==200
    status,_,_=admin.request('DELETE',f'/api/guests/{gid}')
    assert status==200

def test_ADMIN07_preparar_limpieza_y_completarla_desde_panel(client):
    admin=admin_client(client)
    rid=room_id(client)
    status,data,_=admin.request('POST',f'/api/admin/rooms/{rid}/prepare-cleaning',{})
    assert status==200 and data['state']=='en limpieza'
    status,_,_=admin.request('POST',f'/api/rooms/{rid}/cleaning/start',{})
    assert status==201
    status,_,_=admin.request('POST',f'/api/rooms/{rid}/cleaning/finish',{})
    assert status==200
    _,room,_=admin.request('GET',f'/api/rooms/{rid}')
    assert room['state']=='disponible'

def test_ADMIN08_no_preparar_limpieza_para_habitacion_ocupada(client,clock):
    rid,room=reservation(client,checkin='2026-11-17T15:00:00-03:00',checkout='2026-11-19T12:00:00-03:00')
    clock['value']='2026-11-17T15:30:00-03:00'
    assert client.request('POST',f'/api/reservations/{rid}/check-in',{})[0]==200
    admin=admin_client(client)
    status,data,_=admin.request('POST',f'/api/admin/rooms/{room}/prepare-cleaning',{})
    assert status==409 and 'ocupada' in data['error']

def test_ADMIN09_no_editar_reserva_en_curso(client,clock):
    rid,_=reservation(client,checkin='2026-11-17T15:00:00-03:00',checkout='2026-11-19T12:00:00-03:00')
    clock['value']='2026-11-17T15:30:00-03:00'
    assert client.request('POST',f'/api/reservations/{rid}/check-in',{})[0]==200
    admin=admin_client(client)
    status,data,_=admin.request('PATCH',f'/api/reservations/{rid}',{'checkin':'2026-11-20T15:00:00-03:00'})
    assert status==409 and 'Solo se pueden editar reservas confirmadas' in data['error']

# Panel administrativo ampliado: habitaciones, usuarios, sensores, reinicio y bitácora.
def test_ADMIN10_crear_habitacion_crea_espacio_y_sensor(client):
    admin=admin_client(client)
    status,data,_=admin.request('POST','/api/admin/rooms',{'number':'301','room_type':'Suite','capacity':5})
    assert status==201 and data['room']['number']=='301' and data['sensor_id']
    status,rooms,_=client.request('GET','/api/rooms')
    assert status==200 and any(r['number']=='301' for r in rooms)
    status,reading,_=admin.request('POST','/api/readings',{'sensor_id':data['sensor_id'],'count':5})
    assert status==201 and reading['state']=='completo' and reading['capacity']==5

def test_ADMIN11_editar_habitacion_sincroniza_capacidad_espacio_y_sensor(client):
    admin=admin_client(client)
    _,rooms,_=admin.request('GET','/api/rooms'); rid=next(r['id'] for r in rooms if r['number']=='101')
    status,data,_=admin.request('PATCH',f'/api/admin/rooms/{rid}',{'number':'101-A','room_type':'Suite','capacity':6})
    assert status==200 and data['number']=='101-A' and data['capacity']==6
    _,management,_=admin.request('GET','/api/admin/management')
    space=next(s for s in management['spaces'] if s['room_id']==rid)
    assert space['name']=='Habitación 101-A' and space['capacity']==6

def test_ADMIN12_eliminar_habitacion_sin_historial_elimina_sensor_y_espacio(client):
    admin=admin_client(client)
    _,data,_=admin.request('POST','/api/admin/rooms',{'number':'302','room_type':'Doble','capacity':2})
    rid=data['room']['id']; sid=data['sensor_id']
    status,result,_=admin.request('DELETE',f'/api/admin/rooms/{rid}')
    assert status==200
    _,management,_=admin.request('GET','/api/admin/management')
    assert not any(r['id']==rid for r in management['rooms'])
    assert not any(s['sensor_id']==sid for s in management['sensors'])

def test_ADMIN13_habitacion_con_historial_se_desactiva_en_vez_de_borrarse(client):
    admin=admin_client(client); gid=guest(admin); rid=room_id(admin,'101')
    status,res,_=admin.request('POST','/api/reservations',{'guest_id':gid,'room_id':rid,'checkin':'2026-11-25T15:00:00-03:00','checkout':'2026-11-26T12:00:00-03:00'})
    assert status==201
    assert admin.request('DELETE',f'/api/admin/rooms/{rid}')[0]==409
    status,data,_=admin.request('PATCH',f'/api/admin/rooms/{rid}/active',{'active':False})
    assert status==200 and data['active']==0
    _,main_rooms,_=admin.request('GET','/api/rooms')
    assert all(r['id']!=rid for r in main_rooms)
    _,management,_=admin.request('GET','/api/admin/management')
    assert any(r['id']==rid and r['active']==0 for r in management['rooms'])

def test_ADMIN14_reactivar_habitacion(client):
    admin=admin_client(client); _,rooms,_=admin.request('GET','/api/rooms'); rid=rooms[0]['id']
    assert admin.request('PATCH',f'/api/admin/rooms/{rid}/active',{'active':False})[0]==200
    status,data,_=admin.request('PATCH',f'/api/admin/rooms/{rid}/active',{'active':True})
    assert status==200 and data['active']==1

def test_ADMIN15_no_desactivar_habitacion_con_reserva_en_curso(client,clock):
    admin=admin_client(client); rid,room=reservation(admin,checkin='2026-11-17T15:00:00-03:00',checkout='2026-11-18T12:00:00-03:00')
    clock['value']='2026-11-17T15:30:00-03:00'; assert admin.request('POST',f'/api/reservations/{rid}/check-in',{})[0]==200
    status,data,_=admin.request('PATCH',f'/api/admin/rooms/{room}/active',{'active':False})
    assert status==409 and 'reserva' in data['error']

def test_ADMIN16_estado_manual_solo_permite_disponible_o_limpieza(client):
    admin=admin_client(client); _,rooms,_=admin.request('GET','/api/rooms'); rid=rooms[0]['id']
    status,data,_=admin.request('POST',f'/api/admin/rooms/{rid}/state',{'state':'en limpieza'})
    assert status==200 and data['state']=='en limpieza'
    assert admin.request('POST',f'/api/admin/rooms/{rid}/state',{'state':'ocupada'})[0]==400

def test_ADMIN17_usuario_edicion_nombre_rol_password_y_login(client):
    admin=admin_client(client)
    _,u,_=admin.request('POST','/api/users',{'username':'operador','password':'clave123','role':'limpieza'})
    status,data,_=admin.request('PATCH',f"/api/users/{u['id']}",{'username':'operador2','role':'recepcion','active':True,'password':'nueva123'})
    assert status==200 and data['username']=='operador2' and data['role']=='recepcion'
    other=WSGIClient(client.app)
    assert other.login('operador2','nueva123')[0]==200

def test_ADMIN18_proteger_sesion_actual_de_cambio_de_rol_o_desactivacion(client):
    admin=admin_client(client)
    status,data,_=admin.request('PATCH','/api/users/1',{'active':False})
    assert status==409 and 'propia sesión' in data['error']

def test_ADMIN19_eliminar_usuario_sin_historial_y_proteger_usuario_con_historial(client):
    admin=admin_client(client)
    _,u,_=admin.request('POST','/api/users',{'username':'temporal','password':'clave123','role':'limpieza'})
    status,data,_=admin.request('DELETE',f"/api/users/{u['id']}")
    assert status==200
    # A user referenced by a cleaning record must be deactivated rather than deleted.
    _,rooms,_=admin.request('GET','/api/rooms'); room=rooms[0]['id']
    admin.request('POST',f'/api/admin/rooms/{room}/prepare-cleaning',{})
    admin.request('POST',f'/api/rooms/{room}/cleaning/start',{})
    status,cleaner,_=admin.request('POST','/api/users',{'username':'historial','password':'clave123','role':'limpieza'})
    assert status==201
    # Create a cleaning specifically under the new user to establish history.
    cleaner_client=WSGIClient(client.app); assert cleaner_client.login('historial','clave123')[0]==200
    # use a second room for a clean path
    _,rooms,_=cleaner_client.request('GET','/api/rooms'); room2=next(r['id'] for r in rooms if r['id']!=room)
    admin.request('POST',f'/api/admin/rooms/{room2}/prepare-cleaning',{})
    cleaner_client.request('POST',f'/api/rooms/{room2}/cleaning/start',{})
    status,data,_=admin.request('DELETE',f"/api/users/{cleaner['id']}")
    assert status==409 and 'historial' in data['error']

def test_ADMIN20_crear_sensor_y_proteger_sensor_activo_unico_por_espacio(client):
    admin=admin_client(client); _,management,_=admin.request('GET','/api/admin/management')
    pool=next(s for s in management['spaces'] if s['kind']=='piscina')
    assert admin.request('POST','/api/admin/sensors',{'sensor_id':'sensor-piscina-nuevo','space_id':pool['id']})[0]==409
    # Deactivate the original sensor, then attach a replacement.
    assert admin.request('PATCH','/api/admin/sensors/sensor-piscina',{'active':False})[0]==200
    status,data,_=admin.request('POST','/api/admin/sensors',{'sensor_id':'sensor-piscina-nuevo','space_id':pool['id']})
    assert status==201 and data['sensor_id']=='sensor-piscina-nuevo'
    assert admin.request('POST','/api/readings',{'sensor_id':'sensor-piscina-nuevo','count':8})[0]==201

def test_ADMIN21_quitar_sensor_con_lecturas_lo_desactiva_y_conserva_historial(client):
    admin=admin_client(client)
    admin.request('POST','/api/readings',{'sensor_id':'sensor-piscina','count':12})
    status,data,_=admin.request('DELETE','/api/admin/sensors/sensor-piscina')
    assert status==200 and 'desactivado' in data['message']
    assert admin.request('POST','/api/readings',{'sensor_id':'sensor-piscina','count':13})[0]==400
    _,management,_=admin.request('GET','/api/admin/management')
    assert any(s['sensor_id']=='sensor-piscina' and s['active']==0 for s in management['sensors'])

def test_ADMIN22_reset_operativo_requiere_frase_y_conserva_configuracion(client):
    admin=admin_client(client); gid=guest(admin)
    assert admin.request('POST','/api/admin/reset-operational-data',{'confirm':'mal'})[0]==400
    status,data,_=admin.request('POST','/api/admin/reset-operational-data',{'confirm':'LIMPIAR DATOS OPERATIVOS'})
    assert status==200
    _,guests,_=admin.request('GET','/api/guests'); _,rooms,_=admin.request('GET','/api/rooms')
    assert guests==[] and len(rooms)>=3

def test_ADMIN23_bitacora_solo_admin_y_registra_acciones(client):
    gid=guest(client); admin=admin_client(client)
    admin.request('PATCH',f'/api/guests/{gid}',{'first_name':'Auditado'})
    assert client.request('GET','/api/admin/audit')[0]==403
    status,rows,_=admin.request('GET','/api/admin/audit')
    assert status==200 and any(x['entity']=='huésped' and x['action']=='editar' for x in rows)

def test_ADMIN24_crear_habitacion_valida_numero_unico_y_capacidad(client):
    admin=admin_client(client)
    assert admin.request('POST','/api/admin/rooms',{'number':'101','room_type':'Doble','capacity':2})[0]==409
    assert admin.request('POST','/api/admin/rooms',{'number':'399','room_type':'Doble','capacity':0})[0]==400

def test_ADMIN25_sensor_inactivo_no_recibe_lecturas(client):
    admin=admin_client(client)
    assert admin.request('PATCH','/api/admin/sensors/sensor-piscina',{'active':False})[0]==200
    status,data,_=admin.request('POST','/api/readings',{'sensor_id':'sensor-piscina','count':7})
    assert status==400 and 'no identificado o inactivo' in data['error']


def test_ADMIN26_sensor_eliminado_sin_historial_no_se_recrea_al_reiniciar(tmp_path,clock):
    from casa_ogro.webapp import create_application
    db_path=tmp_path/'persistent.sqlite3'
    app=create_application(db_path,clock=lambda:clock['value'])
    admin=WSGIClient(app); assert admin.login('admin','admin123')[0]==200
    status,data,_=admin.request('DELETE','/api/admin/sensors/sensor-piscina')
    assert status==200 and data['message']=='Sensor eliminado.'
    app2=create_application(db_path,clock=lambda:clock['value'])
    admin2=WSGIClient(app2); assert admin2.login('admin','admin123')[0]==200
    _,management,_=admin2.request('GET','/api/admin/management')
    assert not any(s['sensor_id']=='sensor-piscina' for s in management['sensors'])

def test_ADMIN27_migracion_de_base_v2_agrega_columnas_y_bitacora(tmp_path,clock):
    import sqlite3
    from casa_ogro.webapp import create_application
    db_path=tmp_path/'legacy_v2.sqlite3'
    conn=sqlite3.connect(db_path)
    conn.execute("CREATE TABLE rooms (id INTEGER PRIMARY KEY AUTOINCREMENT, number TEXT UNIQUE NOT NULL, room_type TEXT NOT NULL, capacity INTEGER NOT NULL CHECK(capacity > 0), state TEXT NOT NULL DEFAULT 'disponible' CHECK(state IN ('disponible','ocupada','en limpieza')))" )
    conn.commit(); conn.close()
    app=create_application(db_path,clock=lambda:clock['value'])
    conn=sqlite3.connect(db_path)
    columns=[r[1] for r in conn.execute('PRAGMA table_info(rooms)').fetchall()]
    audit=conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='admin_audit'").fetchone()
    conn.close()
    assert 'active' in columns and audit is not None
    admin=WSGIClient(app); assert admin.login('admin','admin123')[0]==200
    assert admin.request('GET','/api/admin/management')[0]==200

def test_ADMIN28_nuevas_rutas_administrativas_rechazan_roles_no_admin(client):
    assert client.request('POST','/api/admin/rooms',{'number':'777','room_type':'Doble','capacity':2})[0]==403
    assert client.request('POST','/api/admin/sensors',{'sensor_id':'sensor-extra','space_id':1})[0]==403
    assert client.request('POST','/api/admin/reset-operational-data',{'confirm':'LIMPIAR DATOS OPERATIVOS'})[0]==403


# CP-RF-11-03: el check-out de Recepción debe rechazarse después de las 12:00 exactas.
def test_RF11C_checkout_a_las_1201_requiere_autorizacion_admin(client,clock):
    rid,_=reservation(client,checkin='2026-11-17T15:00:00-03:00',checkout='2026-11-18T12:00:00-03:00')
    clock['value']='2026-11-17T15:30:00-03:00'
    assert client.request('POST',f'/api/reservations/{rid}/check-in',{})[0]==200
    clock['value']='2026-11-18T12:01:00-03:00'
    status,_,_=client.request('POST',f'/api/reservations/{rid}/check-out',{})
    assert status==403
    admin=admin_client(client)
    status,_,_=admin.request('POST',f'/api/reservations/{rid}/check-out',{})
    assert status==200


# CP-RF-12-03: no se pueden modificar reservas que ya están en curso.
def test_RF12C_no_modificar_reserva_en_curso_por_endpoint_operativo(client,clock):
    rid,_=reservation(client,checkin='2026-11-17T15:00:00-03:00',checkout='2026-11-18T12:00:00-03:00')
    clock['value']='2026-11-17T15:30:00-03:00'
    assert client.request('POST',f'/api/reservations/{rid}/check-in',{})[0]==200
    admin=admin_client(client)
    status,_,_=admin.request('POST',f'/api/reservations/{rid}/modify',{'checkin':'2026-11-20T15:00:00-03:00'})
    assert status==409
    _,rows,_=admin.request('GET','/api/reservations')
    saved=next(row for row in rows if row['id']==rid)
    assert saved['status']=='en_curso' and saved['checkin'].startswith('2026-11-17')


# CP-RF-12-04: tampoco se pueden modificar reservas que ya fueron completadas.
def test_RF12D_no_modificar_reserva_completada_por_endpoint_operativo(client,clock):
    rid,_=reservation(client,checkin='2026-11-17T15:00:00-03:00',checkout='2026-11-18T12:00:00-03:00')
    clock['value']='2026-11-17T15:30:00-03:00'
    assert client.request('POST',f'/api/reservations/{rid}/check-in',{})[0]==200
    clock['value']='2026-11-18T11:30:00-03:00'
    assert client.request('POST',f'/api/reservations/{rid}/check-out',{})[0]==200
    admin=admin_client(client)
    status,_,_=admin.request('POST',f'/api/reservations/{rid}/modify',{'checkin':'2026-11-20T15:00:00-03:00'})
    assert status==409
    _,rows,_=admin.request('GET','/api/reservations')
    saved=next(row for row in rows if row['id']==rid)
    assert saved['status']=='completada' and saved['checkin'].startswith('2026-11-17')


# CP-RF-13-03: una reserva en curso no debe poder cancelarse.
def test_RF13C_no_cancelar_reserva_en_curso(client,clock):
    rid,room=reservation(client,checkin='2026-11-17T15:00:00-03:00',checkout='2026-11-18T12:00:00-03:00')
    clock['value']='2026-11-17T15:30:00-03:00'
    assert client.request('POST',f'/api/reservations/{rid}/check-in',{})[0]==200
    admin=admin_client(client)
    status,_,_=admin.request('POST',f'/api/reservations/{rid}/cancel',{})
    assert status==409
    _,rows,_=admin.request('GET','/api/reservations')
    saved=next(row for row in rows if row['id']==rid)
    assert saved['status']=='en_curso'
    clock['value']='2026-11-18T11:30:00-03:00'
    status,_,_=client.request('POST',f'/api/reservations/{rid}/check-out',{})
    assert status==200
    _,room_data,_=client.request('GET',f'/api/rooms/{room}')
    assert room_data['state']=='en limpieza'


# ADM-29: una habitación no puede tener dos registros de limpieza pendientes.
def test_ADMIN29_no_permitir_inicios_de_limpieza_duplicados(client):
    admin=admin_client(client)
    room=room_id(admin)
    status,_,_=admin.request('POST',f'/api/admin/rooms/{room}/prepare-cleaning',{})
    assert status==200
    first_status,_,_=admin.request('POST',f'/api/rooms/{room}/cleaning/start',{})
    second_status,second_data,_=admin.request('POST',f'/api/rooms/{room}/cleaning/start',{})
    assert first_status==201
    assert second_status==409
    assert 'pendiente' in second_data['error']
    _,management,_=admin.request('GET','/api/admin/management')
    assert len([row for row in management['cleanings'] if row['room_id']==room and row['finished_at'] is None])==1
