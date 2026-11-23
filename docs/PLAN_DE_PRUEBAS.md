# Plan de pruebas — Ejercicio 4

Proyecto: **Sistema de Gestión Hotelera — La Casa del Ogro**  
Equipo: José Molina, Ana Murillo y Felipe Cáceres.  
Base de requisitos: informe de los Ejercicios 2 y 3.  
Versión: prototipo del Ejercicio 4 con panel de Administración completa (v3).  

## 1. Estrategia y alcance

### Alcance del prototipo

El prototipo implementa los 17 requisitos funcionales (RF-01 a RF-17) y los 7 requisitos no funcionales (RNF-01 a RNF-07) definidos en el Ejercicio 2. Las lecturas de aforo son simuladas; no se conecta hardware real, cámaras, reconocimiento facial ni mecanismos físicos de control de acceso.

La validación completa de algunas métricas no se puede concluir únicamente con pruebas automatizadas locales: RNF-03 exige monitoreo durante el período definido para medir disponibilidad mensual; RNF-04 requiere observar y contar interacciones reales en el navegador; RNF-02 y RNF-05 deben repetirse en el computador y entorno de la presentación.

**Asistencia de IA:** se utilizó ChatGPT como apoyo para revisar reglas, proponer casos de regresión y estructurar documentación. El equipo debe ejecutar, revisar y validar los resultados en su propio entorno.

### Niveles, tipos y técnicas

| Nivel | Qué se prueba | Tipo | Técnica | Herramienta / entorno | Criterio de término |
|---|---|---|---|---|---|
| Unitaria | Reglas aisladas en `casa_ogro.rules`: clasificación de aforo, antigüedad de lectura, corte horario de check-out y estado de reserva. | Caja blanca | Cobertura de sentencias y ramas; entradas válidas, inválidas y valores límite. | Pytest + pytest-cov. Se informa la cobertura de ramas del módulo `casa_ogro.rules`. | Los caminos verdadero/falso de las reglas seleccionadas tienen pruebas; se informa cualquier rama no cubierta y el resultado real de la ejecución. |
| Integración | Interacción entre rutas WSGI, autenticación, SQLite, reservas, habitaciones, limpieza, sensores y alertas. | Principalmente caja negra | Pruebas de interfaces, particiones de equivalencia, límites, estados y persistencia. | Pytest con cliente WSGI y SQLite temporal. | Las operaciones aceptadas/rechazadas producen el estado persistido esperado y respetan permisos e integridad. |
| Sistema / aceptación | Recorridos completos desde el navegador con Recepción, Limpieza y Administración. | Caja negra | Escenarios de uso, flujos principales, alternativos y mediciones observables. | Navegador en el computador de demostración; capturas y logs. | Los flujos críticos se completan y cada caso manual conserva evidencia identificada por ID, fecha y commit. |

Las pruebas de `tests/test_requirements.py` ejercitan principalmente las rutas y la persistencia como pruebas de integración; no se presentan como pruebas unitarias aisladas. Las pruebas unitarias de caja blanca están separadas en `tests/test_rules.py` y se concentran en las reglas puras de `casa_ogro/rules.py`.

### Ejecución y herramienta

En Windows, instalar dependencias con `py -m pip install -r requirements-dev.txt` y ejecutar `run_tests.bat`. El lanzador ejecuta Pytest y mide cobertura de ramas del módulo `casa_ogro.rules` con `pytest-cov`. La suite completa puede ejecutarse directamente con:

```bash
py -m pytest -v --cov=casa_ogro.rules --cov-branch --cov-report=term-missing
```

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

## Casos unitarios de caja blanca

| ID del caso | Función | Datos | Resultado esperado |
|---|---|---|---|
| CP-RF-15-02 | `classify_occupancy` | 19 personas, capacidad 20. | `normal`. |
| CP-RF-16-02 | `classify_occupancy` | 20 personas, capacidad 20. | `completo`. |
| CP-RF-16-03 | `classify_occupancy` | 21 personas, capacidad 20. | `excedido`. |
| CP-RF-06-03 | `classify_occupancy` | Conteo -1. | Rechaza el dato con `ValueError`. |
| CP-RF-06-05 | `classify_occupancy` | Conteo booleano `True`. | Rechaza el dato con `ValueError`.
| CP-RF-14-03 | `classify_occupancy` | Capacidad 0. | Rechaza el dato con `ValueError`. |
| CP-RNF-06-03 | `is_reading_stale` | Antigüedad exacta de 2 minutos. | La lectura sigue vigente. |
| CP-RNF-06-04 | `is_reading_stale` | Antigüedad de 2 minutos y 1 segundo. | La lectura se considera antigua. |
| CP-RF-11-04 | `is_after_checkout_cutoff` | 11:59:00. | No supera el límite. |
| CP-RF-11-05 | `is_after_checkout_cutoff` | 12:00:00 exactas. | No supera el límite. |
| CP-RF-11-06 | `is_after_checkout_cutoff` | 12:01:00. | Supera el límite. |
| CP-RF-12-05 | `is_confirmed_reservation` | Estado `confirmada`. | Devuelve verdadero. |
| CP-RF-12-06 | `is_confirmed_reservation` | Estado `en_curso`. | Devuelve falso. |
| CP-RF-12-07 | `is_confirmed_reservation` | Estado `completada`. | Devuelve falso. |
| CP-RF-12-08 | `is_confirmed_reservation` | Estado `cancelada`. | Devuelve falso. |

El archivo `tests/test_rules.py` contiene estos escenarios. La matriz de cobertura utiliza IDs individuales para los casos parametrizados. La cobertura se limita explícitamente a `casa_ogro.rules`; no debe interpretarse como cobertura de todo `webapp.py`.

## 4. Registro de ejecución automatizada

### Línea base histórica (versión principal anterior a las correcciones)

El archivo `evidence/pytest_results.txt` conserva una ejecución previa de la versión base, fechada el 18 de noviembre de 2026:

| Métrica | Resultado histórico |
|---|---:|
| Casos ejecutados | 58 |
| Aprobados | 58 |
| Fallidos | 0 |
| Bloqueados | 0 |

Este resultado corresponde a la suite anterior de 58 pruebas. **No representa la rama de correcciones actual** y no debe presentarse como evidencia de sus cambios.

### Suite de la rama de correcciones

La rama `fix/ejercicio4-reglas-reservas` incorpora **80 casos automatizados planificados**: 51 casos relacionados con RF/RNF y reglas de negocio, más 29 pruebas de soporte administrativo. Incluye las nuevas pruebas de regresión y las pruebas unitarias aisladas de caja blanca.

| Métrica | Resultado de la rama corregida |
|---|---:|
| Casos planificados | 80 |
| Casos ejecutados | Pendiente de ejecutar en VS Code |
| Aprobados | Pendiente |
| Fallidos | Pendiente |
| Bloqueados | Pendiente |
| Cobertura de ramas de `casa_ogro.rules` | Pendiente de medir |

No se asignará un porcentaje de aprobación a esta rama hasta obtener una ejecución real. Después de ejecutarla, guardar la salida completa de Pytest, la cobertura, la fecha y el commit probado en `evidence/pytest_results.txt`.

La medición automatizada no sustituye las comprobaciones manuales de RNF-03 (disponibilidad mensual), RNF-04 (interacciones reales del navegador) ni las mediciones en el computador de presentación para RNF-02 y RNF-05.

## Registro de defectos

El detalle de hallazgos, severidad, corrección y prueba de regresión está en `docs/REGISTRO_DEFECTOS.md`. Los cambios se encuentran implementados en la rama de correcciones, pero su cierre definitivo queda pendiente de ejecutar y aprobar los casos asociados.

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
| CP-RF-11-03 | Check-out a las 12:01 | Recepción recibe 403; Administrador puede autorizarlo. |
| CP-RF-12-03 | Modificar reserva en curso por la ruta operativa | Se rechaza con 409 y conserva fechas/estado. |
| CP-RF-12-04 | Modificar reserva completada por la ruta operativa | Se rechaza con 409 y conserva historial. |
| CP-RF-13-03 | Cancelar reserva en curso | Se rechaza con 409; el check-out posterior sigue disponible. |
| CP-RF-13-04 | Cancelar reserva completada | Se rechaza con 409 y conserva estado completado. |
| CP-RF-06-04 | Conteo booleano del sensor | Se rechaza; no sustituye la última lectura válida. |


## Administración completa — casos automatizados complementarios v3

La suite corregida incluye 29 pruebas del panel administrativo. Estas pruebas no reemplazan los 24 casos mínimos por requisito (RF-01 a RF-17 y RNF-01 a RNF-07); verifican que el panel permita preparar demostraciones y que conserve la integridad de los datos compartidos con la aplicación principal.

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
| ADM-29 | Evitar inicios de limpieza duplicados. | Preparar una habitación para limpieza, iniciar el registro y volver a pulsar iniciar sin finalizar el primero. | El segundo inicio se rechaza con 409 y se conserva una sola limpieza pendiente. |

## Evidencia manual recomendada por sección

- **Habitaciones:** captura de formulario antes de crear, habitación nueva en lista y sensor generado; captura de desactivación y desaparición del módulo principal.
- **Huéspedes/reservas:** captura del registro, formulario de edición y fila actualizada en la lista principal.
- **Usuarios:** captura de usuario creado, rol/estado final y login con la cuenta; captura del rechazo al intentar una acción no autorizada.
- **Sensores/aforo:** captura del sensor activo, lecturas con conteos bajo/igual/sobre el límite y alerta generada; captura del estado desactualizado.
- **Limpieza:** captura antes (en limpieza), inicio de trabajo y después (disponible).
- **Bitácora:** captura con acción, actor, entidad y fecha/hora.

Cada evidencia de ejecución que se incluya en el informe debe llevar ID del caso, fecha y versión/commit del código. El resultado automatizado de Pytest no reemplaza la captura del flujo manual en el navegador.

