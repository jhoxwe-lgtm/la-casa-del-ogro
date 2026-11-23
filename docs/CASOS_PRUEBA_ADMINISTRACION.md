# Casos de prueba del panel de Administración completa (v3)

Este anexo contiene las pruebas de soporte del panel que permiten preparar demostraciones manuales de RF y RNF. Se ejecutan con rol Administrador y una base de datos de prueba o de demostración. Las 29 pruebas complementarias también están automatizadas en `tests/test_requirements.py`.

| ID | Prueba manual | Datos / pasos | Resultado esperado | Relación |
|---|---|---|---|---|
| ADM-01 | Acceso del administrador | Iniciar sesión como Recepción y abrir `/api/admin/management`; repetir como admin. | Recepción: 403. Admin: panel y entidades disponibles. | RNF-01 |
| ADM-02 | Editar huésped | Crear huésped de prueba y cambiar nombre, apellido, teléfono y correo. | Cambio visible en Huéspedes y en Reserva asociada. | RF-03 |
| ADM-03 | Eliminar huésped libre | Crear huésped sin reservas y eliminarlo. | Desaparece del listado. | RF-03 |
| ADM-04 | Proteger huésped asociado | Crear reserva y luego intentar eliminar al huésped. | Se bloquea con explicación; datos permanecen. | RF-01, RF-03 |
| ADM-05 | Editar reserva | Editar fechas de reserva confirmada a un período disponible. | Cambio guardado y visible. | RF-01, RF-12 |
| ADM-06 | Eliminar reserva cerrada | Eliminar reserva no activa y luego huésped sin otras reservas. | Se elimina sin romper integridad. | RF-01, RF-13 |
| ADM-07 | Ciclo de limpieza | Forzar estado `en limpieza`, iniciar y finalizar. | Se registra limpieza y estado final `disponible`. | RF-04, RF-05 |
| ADM-08 | Impedir limpieza de ocupada | Intentar forzar limpieza de habitación con check-in activo. | Se rechaza y conserva `ocupada`. | RF-05, RF-10 |
| ADM-09 | Proteger reserva en curso | Intentar editar reserva `en_curso`. | Se rechaza; el check-out es el flujo correcto. | RF-10, RF-11 |
| ADM-10 | Agregar habitación | Número 301, tipo Triple, capacidad 3. | Se crea habitación, espacio y sensor simulado. | RF-04, RF-06, RF-14 |
| ADM-11 | Editar habitación | Cambiar número/tipo/capacidad. | Se sincronizan ficha y espacio monitorizado. | RF-04, RF-14, RF-15 |
| ADM-12 | Eliminar habitación sin historia | Eliminar habitación recién creada sin operaciones. | Se eliminan habitación, espacio y sensor. | RF-04 |
| ADM-13 | Desactivar habitación con historia | Crear reserva y probar eliminación; después desactivar. | Borrado bloqueado; la retirada conserva historia. | RF-01, RF-02, RF-04 |
| ADM-14 | Reactivar habitación | Reactivar habitación retirada. | Vuelve a aparecer en operación y disponibilidad. | RF-02, RF-04 |
| ADM-15 | Impedir desactivación ocupada | Hacer check-in y tratar de desactivar la habitación. | Se rechaza hasta registrar check-out. | RF-10, RF-11 |
| ADM-16 | Estado manual controlado | Forzar `disponible` o `en limpieza`; intentar `ocupada`. | Los estados manuales permitidos funcionan; `ocupada` exige check-in. | RF-04, RF-05, RF-10 |
| ADM-17 | Administrar cuenta | Crear usuario, cambiar nombre, rol, estado y contraseña. | Nuevo login funciona con contraseña actualizada. | RF-08, RF-09 |
| ADM-18 | Protección de sesión | Intentar desactivar o cambiar el rol de la propia cuenta admin. | Operación rechazada. | RNF-01 |
| ADM-19 | Eliminar o desactivar usuario | Borrar usuario sin historial; probar usuario con limpieza asociada. | El primero se elimina; el histórico se desactiva. | RF-08, RNF-01 |
| ADM-20 | Agregar sensor | Probar un segundo sensor activo en el mismo espacio, desactivar el anterior y crear sustituto. | Un único sensor activo por espacio; el nuevo acepta lectura. | RF-06, RF-15 |
| ADM-21 | Quitar sensor con historia | Enviar lectura y luego quitar sensor. | Sensor se desactiva, historia permanece y nuevas lecturas se rechazan. | RF-06, RNF-06 |
| ADM-22 | Reiniciar datos operativos | Escribir frase incorrecta y luego `LIMPIAR DATOS OPERATIVOS`. | Confirmación errónea rechazada; la exacta reinicia solo registros operativos. | Preparación de pruebas |
| ADM-23 | Bitácora | Cambiar huésped desde admin y consultar Bitácora; consultar desde Recepción. | Acción registrada con actor y fecha; acceso no admin prohibido. | Trazabilidad / RNF-01 |
| ADM-24 | Datos inválidos | Crear habitación duplicada y con capacidad cero. | Se rechazan ambos datos. | RF-04, RF-14 |
| ADM-25 | Sensor apagado | Desactivar sensor y enviar lectura. | Se rechaza la lectura y no sustituye el último conteo válido. | RF-06, RNF-06 |
| ADM-26 | Persistencia de sensor eliminado | Quitar un sensor sin lecturas y reiniciar el servidor. | El sensor eliminado permanece fuera del listado; el arranque no lo vuelve a crear. | Persistencia / gestión de sensores |
| ADM-27 | Migración de base anterior | Copiar una base v2 sin columna `rooms.active` y abrir v3. | La aplicación migra la base y crea bitácora automáticamente, sin borrar registros. | Compatibilidad / persistencia |
| ADM-28 | Seguridad de rutas nuevas | Con rol Recepción, llamar a creación de habitación/sensor y limpieza de datos. | Se rechazan todas las operaciones con 403. | RNF-01 |
| ADM-29 | Evitar limpieza pendiente duplicada | Preparar la habitación, iniciar limpieza y volver a iniciar sin finalizar el primer registro. | El segundo intento se rechaza con 409; queda un único registro pendiente. | RF-05 / integridad |

## Evidencias a guardar

Para cada caso manual, guarda capturas que muestren el ID del caso, el estado inicial, la acción y el resultado final. Identifica el archivo con nombre similar a `ADM-10_habitacion_creada_2026-11-18.png`. Para una evidencia formal, añade la fecha y la versión o commit que se probó. No declares aprobada una prueba manual hasta ejecutarla en el navegador del equipo que se utilizará en la evaluación.

