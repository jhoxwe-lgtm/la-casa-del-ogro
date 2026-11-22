# Registro de defectos y hallazgos — Ejercicio 4

| ID | Tipo | Descripción | Severidad | Estado | Acción |
|---|---|---|---|---|---|
| DEF-PRU-01 | Defecto de prueba | RF-04 solo comprobaba pertenencia a una lista; podía pasar sin estado ocupado/en limpieza real. | Alta para validez | Corregido en rama v4; pendiente CI | Ahora reserva, check-in y check-out; exige tres estados. |
| DEF-PRU-02 | Cobertura unitaria | Clasificación de aforo inline sin test aislado de ramas. | Media | Corregido en rama v4; pendiente CI | Extraída a `classify_occupancy`; tres caminos V(G)=3. |
| DEF-PRU-03 | Cobertura crítica | Se probaba lectura antigua pero no recuperación al volver telemetría. | Alta para comportamiento crítico | Corregido en rama v4; pendiente CI | Añadida secuencia antiguo -> desactualizado -> nuevo -> normal. |
| HALL-01 | Evidencia pendiente | RNF-04 API/dashboard no mide interacciones reales. | Media | Abierto | Ejecutar CP-SYS-RNF04-01. |
| HALL-02 | Métrica no demostrada | GET /health puntual no prueba 99% mensual. | Alta RNF | Abierto | Monitoreo continuo mensual. |
| HALL-03 | Evidencia de sistema | WSGI/API no sustituye recorridos completos de navegador. | Media | Abierto | Ejecutar escenarios reserva y aforo con capturas por ID. |
| HALL-04 | Medición pendiente | RNF-02/RNF-05 requieren medición en equipo de defensa. | Media | Abierto | Repetir mediciones y guardar salida. |
| HALL-05 | Limitación de alcance | Sensores simulados; no se probaron hardware físico, ruido ni pérdidas reales. | Media | Conocido | Declararlo; no afirmar validación física. |
| HALL-06 | Riesgo de despliegue | Credenciales demo públicas, sesiones en memoria y SQLite local no son aptos para Internet sin endurecimiento. | Alta producción | Abierto antes de nube | Secretos, sesiones seguras/persistentes, CSRF, PostgreSQL y pruebas despliegue. |

DEF-PRU son hallazgos de calidad de pruebas, no fallos confirmados de lógica de negocio. Su cierre requiere CI verde. HALL-01 a HALL-06 siguen pendientes hasta completar sus acciones.
