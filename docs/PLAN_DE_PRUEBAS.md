# Plan de pruebas — Ejercicio 4

Proyecto: **Sistema de Gestión Hotelera — La Casa del Ogro**  
Equipo: José Molina, Ana Murillo y Felipe Cáceres.  
Base de requisitos: informe de los Ejercicios 2 y 3.  
Versión: prototipo del Ejercicio 4 con panel de Administración completa (v3).  

## 1. Estrategia y alcance

| Nivel | Qué se prueba | Tipo/técnica | Herramienta | Criterio de término |
|---|---|---|---|---|
| Unitaria | Regla pura `classify_occupancy(count, capacity)`: conteo menor, igual y mayor | Caja blanca: dos decisiones y caminos independientes; caja negra: valores de frontera | Pytest aislado; pytest-cov con cobertura de ramas | Tres caminos. V(G) = 2 decisiones + 1 = 3. Se cubren ambos lados de cada decisión. |
| Integración | Rutas HTTP, autenticación, reservas, limpieza, sensores, alertas y persistencia SQLite | Caja negra en interfaces: entradas, códigos HTTP, salidas y cambios persistidos; límites/alternativos | Pytest, WSGIClient y SQLite temporal | Resultado esperado y cambio consultable; acción no autorizada no modifica datos. |
| Sistema | Recorridos completos por navegador para Recepción, Limpieza y Administrador; reserva y aforo | Caja negra, casos de uso y RNF; manual reproducible | Chrome/Edge, aplicación local/LAN, capturas y logs | Flujos principales y alternativos críticos; fecha, commit y evidencia. Los casos manuales pendientes no se marcan aprobados. |

WSGI/API no se considera prueba de sistema de navegador: no automatiza clics ni renderizado. Los recorridos reales se especifican en `docs/CASOS_PRUEBA_SISTEMA.md`. Los sensores son simulados según el alcance; no se afirma validar hardware físico.
## 2. Casos de prueba — funcionales

Los pasos pueden ejecutarse en la interfaz cuando el módulo está disponible o mediante la API `/api/...`. El archivo `tests/test_requirements.py` contiene la ejecución automatizada de estos casos.

| ID | Requisito | Objetivo / precondición | Pasos y datos | Resultado esperado |
|---|---|---|---|---|
| CP-RF-01-01 | RF-01 | Verificar creación de reserva. Recepción autenticada; huésped y habitación existentes. | Registrar una reserva para huésped válido, habitación 101, entrada 25-11-2026 15:00 y salida 27-11-2026 12:00. | Reserva creada como confirmada y asociada al huésped, habitación y fechas. |
| CP-RF-02-01 | RF-02 | Verificar exclusión de habitación con reserva superpuesta. | Consultar disponibilidad para el período 25 a 27-11-2026, después de reservar habitación 101. | La habitación 101 no aparece como disponible para ese período. |
| CP-RF-03-01 | RF-03 | Verificar registro de datos de huésped. Recepción autenticada. | Ingresar nombre, apellido, teléfono y correo electrónico. | Se genera un ID y los cuatro datos quedan asociados al huésped. |
| CP-RF-04-01 | RF-04 | Verificar consulta del estado de habitaciones. | Abrir Habitaciones o consultar `/api/rooms`. | Se muestran habitación, tipo, capacidad y estado operativo actual. |
| CP-RF-05-01 | RF-05 | Verificar término de limpieza. Habitación en estado “en limpieza”. | Iniciar registro de limpieza con usuario Limpieza; luego finalizarlo. | Se guarda inicio y fin; la habitación cambia a “disponible”. |
| CP-RF-06-01 | RF-06 | Verificar recepción y asociación de lectura. | Enviar `sensor-piscina`, conteo 17 y fecha/hora. | Se guarda lectura vinculada al sensor, espacio, conteo y fecha/hora. |
| CP-RF-07-01 | RF-07 | Verificar consulta de último conteo. | Enviar sucesivamente 16 y 18 personas al sensor de piscina; consultar aforo. | La consulta devuelve el último conteo: 18 personas. |
| CP-RF-08-01 | RF-08 | Verificar administración de cuentas. Administrador autenticado. | Crear un usuario, cambiar su rol y desactivar la cuenta. | El usuario aparece creado, refleja el nuevo rol y queda inactivo. |
| CP-RF-09-01 | RF-09 | Verificar autenticación. | Intentar acceso con contraseña incorrecta y luego con credenciales válidas de una cuenta activa. | Se rechaza el primer intento y se inicia sesión con las credenciales válidas. |
| CP-RF-10-01 | RF-10 | Verificar check-in y autorización de ingreso anticipado. | Con Recepción, intentar check-in a las 14:00; repetir con Administrador. | Recepción recibe rechazo antes de las 15:00; Administrador puede autorizar y la habitación queda ocupada. |
| CP-RF-11-01 | RF-11 | Verificar check-out. Reserva en curso. | Registrar check-out a las 11:30 del día de salida. | La reserva se completa y la habitación pasa a “en limpieza”. |
| CP-RF-12-01 | RF-12 | Verificar modificación de reserva y límite de 24 horas. | Modificar una reserva con más de 24 horas; luego intentar modificar dentro de las últimas 24 horas con Recepción. | La primera modificación se acepta si hay disponibilidad; la tardía se rechaza sin autorización administrativa. |
| CP-RF-13-01 | RF-13 | Verificar cancelación y regla de 24 horas. | Cancelar una reserva con más de 24 horas de anticipación. | La reserva cambia a cancelada y deja de bloquear disponibilidad. Una cancelación tardía requiere Administrador. |
| CP-RF-14-01 | RF-14 | Verificar configuración de capacidad. Administrador autenticado. | Cambiar capacidad de la piscina de 20 a 25. | La nueva capacidad queda guardada y será usada por la comparación de lecturas. |
| CP-RF-15-01 | RF-15 | Verificar comparación de conteo inferior al límite. | Enviar 19 personas a piscina con capacidad 20. | El sistema devuelve capacidad 20 y estado normal. Los límites 20/21 se revisan en CP-RF-16-01. |
| CP-RF-16-01 | RF-16 | Verificar estados completo y excedido. | Enviar 20 y luego 21 personas a piscina con capacidad 20. | Para 20 muestra completo; para 21 muestra excedido y almacena una alerta vinculada a la lectura. |
| CP-RF-17-01 | RF-17 | Verificar revisión de alerta. Recepción autenticada; alerta pendiente. | Abrir alerta de piscina y marcarla como revisada con observación. | Se registra usuario y fecha/hora de revisión; la alerta conserva el nivel completo/excedido. |

## 3. Casos de prueba — no funcionales

| ID | Requisito | Objetivo / precondición | Pasos y datos | Resultado esperado / alcance de la evidencia |
|---|---|---|---|---|
| CP-RNF-01-01 | RNF-01 | Comprobar permisos por rol. | Iniciar sesión como Limpieza e intentar registrar un huésped. | HTTP 403; no se crea huésped. Prueba automatizada. |
| CP-RNF-02-01 | RNF-02 | Medir consultas con hasta 10 sesiones concurrentes. | Ejecutar 10 consultas concurrentes al panel/resumen. | Todas responden y la ejecución local completa en menos de 3 s. Repetir en el equipo de presentación. |
| CP-RNF-03-01 | RNF-03 | Comprobar respuesta básica del servicio. | Consultar `/health`. | Servicio responde correctamente. **Limitación:** el objetivo 99 % mensual requiere un registro continuo durante un mes; este caso no valida el porcentaje mensual. |
| CP-RNF-04-01 | RNF-04 | Comprobar consulta de habitación en máximo 3 interacciones. | Desde el panel, abrir Habitaciones y localizar el estado de la habitación. | El estado debe quedar visible en no más de 3 interacciones. Completar observación manual y anotar el conteo real. |
| CP-RNF-05-01 | RNF-05 | Medir tiempo de disponibilidad de una lectura en el panel. | Enviar lectura de piscina y consultar aforo inmediatamente después. | Lectura visible en menos de 10 s. Registrar tiempo medido en el equipo de presentación. |
| CP-RNF-06-01 | RNF-06 | Verificar caducidad de conteo. | Registrar una lectura con hora de hace más de 2 minutos y consultar aforo. | Estado visible como “desactualizado”. Prueba automatizada con reloj controlado. |
| CP-RNF-07-01 | RNF-07 | Verificar que la entrada del sensor no acepte imágenes ni identificación. | Enviar lectura con sensor, conteo, más un campo `image` y un campo de identificación. | Se rechaza la carga adicional; el sistema solo acepta sensor, conteo y fecha/hora. |

## 4. Registro de ejecución automatizada

Ejecución realizada sobre el prototipo entregado:

| Métrica | Resultado |
|---|---:|
| Casos automatizados planificados | 62 (31 RF/RNF/complementarias + 28 administrativas + 3 unitarias) |
| Casos automatizados ejecutados | Pendiente de CI (62 planificados) |
| Aprobados | Pendiente de CI |
| Fallidos | Pendiente de CI |
| Bloqueados en esta suite | Pendiente de CI |

La línea base v3 fue de 58 pruebas aprobadas en 9,91 s (commit 30890233b278dd1181255e30773551889012950f). La rama de auditoría agrega tres unitarias y una prueba de recuperación de telemetría; el resultado definitivo se obtiene del workflow GitHub Actions. RNF-03 y RNF-04 requieren evidencia manual.

## 5. Riesgos y limitaciones conocidos

- RNF-03 no se puede validar con una prueba puntual; se requiere monitoreo mensual y evidencia histórica.
- RNF-02 y RNF-05 deben medirse también en el computador y entorno que se usará en la demostración.
- Las lecturas de aforo son simuladas; no se probó hardware físico ni ruido de sensores.
- La interfaz es un prototipo funcional para demostrar flujos principales y no un producto listo para producción.
- Si el código cambia, el registro de ejecución se debe actualizar con una nueva ejecución.

## 6. Trazabilidad requisito → caso de prueba

| Requisito | Caso asociado |
|---|---|
| RF-01 a RF-17 | CP-RF-01-01 a CP-RF-17-01 (un caso mínimo por requisito) |
| RNF-01 a RNF-07 | CP-RNF-01-01 a CP-RNF-07-01 (un caso mínimo por requisito) |

No hay requisitos funcionales ni no funcionales sin un caso identificado en este plan.

### Casos complementarios ejecutados

| ID | Cobertura adicional | Resultado esperado |
|---|---|---|
| CP-RF-06-02 | Sensor no identificado | Rechazo sin sustituir el último conteo válido. |
| CP-RF-11-02 | Check-out después de las 12:00 | Recepción no puede ejecutarlo; Administrador puede autorizarlo. |
| CP-RF-12-02 | Modificación dentro de las últimas 24 horas | Recepción es rechazada; Administrador puede autorizarla. |
| CP-RF-13-02 | Cancelación dentro de las últimas 24 horas | Recepción es rechazada; Administrador puede autorizarla. |
| CP-RF-14-02 | Capacidad de habitación monitorizada | El cambio de capacidad se refleja en la comparación del sensor. |
| CP-RNF-06-02 | Límite exacto de 2 minutos | El conteo no se marca desactualizado hasta superar los 2 minutos. |


## Administración completa — casos automatizados complementarios v3

La suite incluye 28 pruebas del panel administrativo. Estas pruebas no reemplazan los 24 casos mínimos por requisito (RF-01 a RF-17 y RNF-01 a RNF-07); verifican que el panel permita preparar demostraciones y que conserve la integridad de los datos compartidos con la aplicación principal.

| ID | Objetivo / precondición | Pasos y datos | Resultado esperado |
|---|---|---|---|
| ADM-01 | Acceso restringido al panel. | Intentar consultar el panel como Recepción y como Administrador. | Recepción obtiene 403; Administrador consulta huéspedes, reservas, habitaciones, usuarios, espacios, sensores, limpiezas, alertas y bitácora. |
| ADM-02 | Editar huésped. | Modificar nombre, apellido, teléfono y correo desde el formulario de edición. | El registro se actualiza en la misma base y aparece corregido en los módulos principales. |
| ADM-03 | Eliminar huésped sin reservas. | Crear huésped nuevo y eliminarlo. | El huésped desaparece del listado principal. |
| ADM-04 | Proteger huésped con reservas. | Crear una reserva para un huésped e intentar eliminarlo. | Se rechaza con 409 y se conservan ambas entidades. |
| ADM-05 | Editar reserva confirmada. | Cambiar fechas de una reserva confirmada sin solapamientos. | Se guardan las nuevas fechas y la reserva aparece actualizada. |
| ADM-06 | Eliminar reserva cerrada y liberar huésped. | Eliminar una reserva no activa; después eliminar el huésped si ya no tiene otras reservas. | Ambas operaciones se permiten y no quedan referencias huérfanas. |
| ADM-07 | Preparar y completar limpieza. | Forzar `en limpieza`, registrar inicio y finalizar. | Se crea el registro de limpieza y la habitación vuelve a `disponible`. |
| ADM-08 | Proteger habitación ocupada. | Intentar forzar limpieza sobre habitación con reserva en curso. | Se rechaza la operación; la habitación sigue `ocupada`. |
| ADM-09 | Proteger reserva en curso. | Intentar editar una reserva `en_curso`. | Se rechaza para preservar la historia operativa. |
| ADM-10 | Crear habitación y su sensor. | Agregar habitación 301, tipo Suite/Triple, capacidad 5. | Aparece en Habitaciones, con espacio monitorizado y sensor nuevo; el sensor puede recibir lectura. |
| ADM-11 | Editar habitación y sincronizar capacidad. | Cambiar número, tipo y capacidad de la habitación 101. | Se modifica la ficha y también el nombre/capacidad del espacio asociado. |
| ADM-12 | Eliminar habitación sin historial. | Crear una habitación sin reservas, limpiezas, lecturas o alertas; eliminarla. | Se elimina también su espacio monitorizado y sensor asociado. |
| ADM-13 | Retirar habitación con historial. | Crear reserva asociada; intentar borrado y luego desactivar habitación. | El borrado se rechaza; la desactivación la quita del módulo principal pero la conserva en Administración. |
| ADM-14 | Reactivar habitación. | Desactivar y luego reactivar una habitación sin operación en curso. | Vuelve a mostrarse en el módulo Habitaciones y disponibilidad. |
| ADM-15 | Proteger habitación con reserva en curso. | Registrar check-in y luego intentar desactivar la habitación. | Se rechaza hasta completar check-out. |
| ADM-16 | Cambiar estado manual de forma controlada. | Forzar `en limpieza` y luego intentar estado `ocupada` manualmente. | Se acepta el estado permitido; `ocupada` se rechaza y debe demostrarse con check-in. |
| ADM-17 | Editar cuenta y contraseña. | Cambiar nombre de usuario, rol y contraseña de una cuenta de prueba; iniciar sesión con las credenciales nuevas. | Los cambios se guardan y la nueva contraseña autentica correctamente. |
| ADM-18 | Proteger la propia sesión. | Intentar desactivar o quitar el rol admin de la cuenta con la que se inició sesión. | La operación se rechaza. |
| ADM-19 | Eliminar usuario según historial. | Eliminar cuenta sin historial; intentar borrar otra que tenga registros de limpieza. | La primera se elimina; la segunda se conserva y debe desactivarse. |
| ADM-20 | Asociar sensor nuevo a espacio. | Intentar crear segundo sensor activo; desactivar el existente y asociar uno nuevo. | Se impide tener dos sensores activos en un espacio; el sensor sustituto puede enviar lecturas. |
| ADM-21 | Quitar sensor con historial. | Enviar lectura y luego quitar el sensor. | Se desactiva, no se borra; las lecturas previas se conservan y no acepta nuevas. |
| ADM-22 | Reinicio seguro de datos operativos. | Intentar reiniciar con frase errónea y luego con `LIMPIAR DATOS OPERATIVOS`. | La frase errónea se rechaza; la correcta elimina registros operativos y conserva usuarios, habitaciones, sensores y capacidades. |
| ADM-23 | Bitácora administrativa. | Editar huésped desde Administrador y consultar bitácora; intentar acceder como Recepción. | Se registra actor/acción/entidad/fecha; Recepción obtiene 403. |
| ADM-24 | Validar datos de habitación. | Crear habitación con número duplicado y luego con capacidad cero. | Ambos intentos se rechazan con mensaje claro. |
| ADM-25 | Rechazar sensor inactivo. | Desactivar sensor y enviar lectura con su ID. | Se rechaza la lectura; el último conteo válido no se reemplaza. |
| ADM-26 | Persistencia de sensor eliminado. | Eliminar sensor sin lecturas y reiniciar la aplicación. | El sensor eliminado no se recrea automáticamente. |
| ADM-27 | Migración de base v2. | Abrir una base anterior sin `rooms.active` ni bitácora. | La migración añade la columna y crea la bitácora sin perder datos existentes. |
| ADM-28 | Seguridad de nuevas rutas. | Intentar crear habitaciones/sensores o reiniciar datos desde Recepción. | Las acciones administrativas se rechazan con HTTP 403. |

## Evidencia manual recomendada por sección

- **Habitaciones:** captura de formulario antes de crear, habitación nueva en lista y sensor generado; captura de desactivación y desaparición del módulo principal.
- **Huéspedes/reservas:** captura del registro, formulario de edición y fila actualizada en la lista principal.
- **Usuarios:** captura de usuario creado, rol/estado final y login con la cuenta; captura del rechazo al intentar una acción no autorizada.
- **Sensores/aforo:** captura del sensor activo, lecturas con conteos bajo/igual/sobre el límite y alerta generada; captura del estado desactualizado.
- **Limpieza:** captura antes (en limpieza), inicio de trabajo y después (disponible).
- **Bitácora:** captura con acción, actor, entidad y fecha/hora.

Cada evidencia de ejecución que se incluya en el informe debe llevar ID del caso, fecha y versión/commit del código. El resultado automatizado de Pytest no reemplaza la captura del flujo manual en el navegador.



## 7. Cobertura de caja blanca

`classify_occupancy` contiene dos decisiones; V(G) = 2 + 1 = 3.

| Caso | count == capacity | count > capacity | Entrada | Salida |
|---|---|---|---|---|
| CP-UNIT-RF15-01 | Falso | Falso | 19/20 | normal |
| CP-UNIT-RF16-01 | Verdadero | No evaluada por retorno | 20/20 | completo |
| CP-UNIT-RF16-02 | Falso | Verdadero | 21/20 | excedido |

Los tres casos ejecutan caminos independientes y ambos lados de cada decisión. El workflow mide cobertura de ramas únicamente para `casa_ogro.rules`.
