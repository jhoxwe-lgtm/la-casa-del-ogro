# Casos de prueba detallados — La Casa del Ogro

Versión objetivo: v4, rama `quality/ejercicio4-auditoria`. Base: RF-01 a RF-17 y RNF-01 a RNF-07. Los casos WSGI/API son integración; los casos de navegador están separados.

## Convenciones
- Unitario: función aislada, sin servidor ni BD.
- Integración: módulos conectados mediante WSGI/API y SQLite temporal.
- Sistema: aplicación observada desde el navegador.
- Caja negra: entradas, salidas, códigos y efectos observables.
- Caja blanca: decisiones y caminos internos.

## Casos mínimos funcionales

| ID / requisito | Nivel/tipo | Objetivo, precondición, datos y pasos | Resultado esperado / evidencia |
|---|---|---|---|
| CP-RF-01-01 / RF-01 | Integración, negra | Recepción autenticada; huésped válido; habitación 101 libre. Crear reserva 25-11-2026 15:00 a 27-11-2026 12:00 y consultar. | HTTP 201, confirmada y asociada; `test_RF01_registrar_reserva`. |
| CP-RF-02-01 / RF-02 | Integración, negra | Crear reserva hab. 101 para 25–27 nov; consultar disponibilidad del mismo intervalo. | HTTP 200 y habitación 101 excluida; `test_RF02_disponibilidad_excluye_reserva_superpuesta`. |
| CP-RF-03-01 / RF-03 | Integración, negra | Recepción registra Ana Prueba, 912345678, ana@example.com; consulta listado. | HTTP 201, ID y campos persistidos; `test_RF03_registrar_huesped`. |
| CP-RF-04-01 / RF-04 | Integración, negra | Consultar disponible; reloj 25-11 15:30 y check-in; verificar ocupada; reloj 26-11 11:30 y check-out; verificar en limpieza y otra disponible. | Tres estados reales; `test_RF04_consultar_estado_habitaciones`. |
| CP-RF-05-01 / RF-05 | Integración, negra | Habitación en limpieza; usuario Limpieza inicia, finaliza y consulta historial/estado. | Inicio/fin guardados; estado disponible; `test_RF05_finalizar_limpieza_libera_habitacion`. |
| CP-RF-06-01 / RF-06 | Integración, negra | Sensor-piscina activo; enviar 17 y timestamp ISO; consultar historial. | HTTP 201, lectura asociada; `test_RF06_recibir_lectura_sensor`. |
| CP-RF-07-01 / RF-07 | Integración, negra | Enviar 16 y luego 18; consultar aforo. | Último conteo 18; `test_RF07_consultar_ultimo_conteo`. |
| CP-RF-08-01 / RF-08 | Integración, negra | Admin crea usuario Limpieza, cambia a Recepción, desactiva y consulta. | Cambios persistidos; `test_RF08_gestionar_usuarios_y_roles`. |
| CP-RF-09-01 / RF-09 | Integración, negra | Login con clave incorrecta y después cuenta Recepción válida. | 401 sin sesión y login válido; `test_RF09_inicio_sesion_valida_e_invalida`. |
| CP-RF-10-01 / RF-10 | Integración, negra | Reserva confirmada; reloj 14:00: Recepción intenta check-in, Admin autoriza. | Recepción 403; Admin autorizado; `test_RF10_checkin_regla_horaria`. |
| CP-RF-11-01 / RF-11 | Integración, negra | Reserva en curso; checkout 11:30 del día de salida. | Reserva finalizada y habitación en limpieza; `test_RF11_checkout_y_estado_limpieza`. |
| CP-RF-12-01 / RF-12 | Integración, negra | Modificar reserva confirmada fuera de ventana y con nuevas fechas disponibles. | HTTP 200 y fechas modificadas; `test_RF12_modificar_reserva`. |
| CP-RF-13-01 / RF-13 | Integración, negra | Cancelar reserva futura con más de 24 h; consultar estado/disponibilidad. | Cancelada y período liberado; `test_RF13_cancelar_reserva`. |
| CP-RF-14-01 / RF-14 | Integración, negra | Admin cambia capacidad Piscina 20->25 y consulta. | Capacidad persistida; `test_RF14_configurar_capacidad`. |
| CP-RF-15-01 / RF-15 | Integración, negra | Piscina capacidad 20; enviar 19. | Estado normal; `test_RF15_comparar_conteo_y_capacidad`. |
| CP-RF-16-01 / RF-16 | Integración, negra | Enviar 20 y 21 a Piscina capacidad 20. | Completo, luego excedido y alerta; `test_RF16_generar_alerta_al_alcanzar_o_superar_capacidad`. |
| CP-RF-17-01 / RF-17 | Integración, negra | Recepción revisa alerta pendiente con observación y consulta. | Usuario/fecha/observación persistidos; `test_RF17_revisar_alerta_conserva_estado`. |

## Casos mínimos no funcionales

| ID / requisito | Nivel/tipo | Objetivo, precondiciones, datos y pasos | Resultado esperado / evidencia |
|---|---|---|---|
| CP-RNF-01-01 / RNF-01 | Integración, negra/seguridad | Limpieza autenticado intenta registrar huésped válido. | HTTP 403, sin datos nuevos; `test_RNF01_permisos_por_rol`. |
| CP-RNF-02-01 / RNF-02 | Integración, negra/rendimiento | 10 sesiones y 10 GET /api/dashboard en paralelo; umbral local 3s. | 10 respuestas 200 y tiempo medido bajo umbral; `test_RNF02_rendimiento_diez_consultas_concurrentes`; repetir en defensa. |
| CP-RNF-03-01 / RNF-03 | Sistema, negra/disponibilidad | Monitoreo continuo /health durante el mes y cálculo de uptime. | 99% respaldado por historial; un 200 puntual no basta. Automatizada `test_RNF03_servicio_responde_healthcheck` es smoke test solamente. |
| CP-RNF-04-01 / RNF-04 | Sistema, negra/usabilidad | Recepción consulta estado habitación 101 desde inicio; contar acciones reales. | Máximo 3 interacciones; test API no mide clics, manual pendiente. |
| CP-RNF-05-01 / RNF-05 | Sistema, negra/rendimiento | Enviar lectura con panel abierto; medir hasta visualizar; repetir 10 veces. | Menos de 10s; el test API local no sustituye medición navegador. |
| CP-RNF-06-01 / RNF-06 | Integración, negra/temporal | Lectura a 10:00; reloj 10:03:01; consultar aforo. | Desactualizado; `test_RNF06_conteo_antiguo_marcado_desactualizado`. |
| CP-RNF-07-01 / RNF-07 | Integración, negra/privacidad | Enviar sensor/count más image y guest_name. | HTTP 400; `test_RNF07_lectura_no_acepta_imagenes_ni_datos_personales`. |

## Alternativos y límites

| ID | Requisito | Acción | Resultado esperado |
|---|---|---|---|
| CP-RF-06-02 | RF-06 | Sensor desconocido tras lectura válida | HTTP 400; conteo previo se conserva. |
| CP-RF-11-02 | RF-11 | Checkout posterior 12:00 por Recepción y Admin | Recepción rechazada; Admin autoriza. |
| CP-RF-12-02 | RF-12 | Modificar dentro de 24h | Recepción rechazada; Admin autoriza. |
| CP-RF-13-02 | RF-13 | Cancelar dentro de 24h | Recepción rechazada; Admin autoriza. |
| CP-RF-14-02 | RF-14 | Cambiar capacidad de habitación y contar en nuevo límite | Capacidad sincronizada y comparación correcta. |
| CP-RNF-06-02 | RNF-06 | Antigüedad exacta 2:00 min | Todavía no desactualizado. |
| CP-RNF-06-03 | RNF-06 | Lectura 3:01 min y luego nueva lectura | Primero desactualizado; después normal y conteo actualizado. |

## Unitarias de caja blanca — caminos independientes

`classify_occupancy` tiene dos decisiones; V(G)=2+1=3.

| ID | Requisito | count == capacity | count > capacity | Entrada | Salida |
|---|---|---|---|---|---|
| CP-UNIT-RF15-01 | RF-15 | Falso | Falso | 19/20 | normal |
| CP-UNIT-RF16-01 | RF-16 | Verdadero | No evaluada por retorno | 20/20 | completo |
| CP-UNIT-RF16-02 | RF-16 | Falso | Verdadero | 21/20 | excedido |
