# Registro de defectos y hallazgos — Ejercicio 4

| ID | Tipo | Descripción | Severidad | Estado | Acción / evidencia |
|---|---|---|---|---|---|
| DEF-PRU-01 | Defecto de prueba | RF-04 solo comprobaba pertenencia a una lista y podía pasar sin demostrar los tres estados simultáneamente. | Alta para validez | Corregido y regresión aprobada | Se preparan dos habitaciones: una permanece ocupada mientras la otra pasa a limpieza; una tercera queda disponible. Aprobado en [Actions run #4](https://github.com/jhoxwe-lgtm/la-casa-del-ogro/actions/runs/45051510264). |
| DEF-PRU-02 | Cobertura unitaria | Clasificación de aforo inline sin test aislado de ramas. | Media | Corregido y regresión aprobada | Extraída a `classify_occupancy`; tres caminos V(G)=3; 100 % sentencias/ramas en ese módulo. |
| DEF-PRU-03 | Cobertura crítica | Se probaba lectura antigua, pero no recuperación al volver telemetría. | Alta para comportamiento crítico | Corregido y regresión aprobada | Prueba desactualizado -> nueva lectura -> normal; aprobada en run #4. |
| HALL-01 | Evidencia pendiente | RNF-04 API/dashboard no mide interacciones reales. | Media | Abierto | Ejecutar CP-SYS-RNF04-01. |
| HALL-02 | Métrica no demostrada | GET /health puntual no prueba 99 % mensual. | Alta RNF | Abierto | Monitoreo continuo mensual. |
| HALL-03 | Evidencia de sistema | WSGI/API no sustituye recorridos completos de navegador. | Media | Abierto | Ejecutar escenarios de reserva y aforo con capturas por ID. |
| HALL-04 | Medición pendiente | RNF-02/RNF-05 requieren medición en equipo de defensa. | Media | Abierto | Repetir mediciones y guardar salida. |
| HALL-05 | Limitación de alcance | Sensores simulados; no se probaron hardware físico, ruido ni pérdidas reales. | Media | Conocido | Declararlo; no afirmar validación física. |
| HALL-06 | Riesgo de despliegue | Credenciales demo públicas, sesiones en memoria y SQLite local no son aptos para Internet sin endurecimiento. | Alta producción | Abierto antes de nube | Secretos, sesiones seguras/persistentes, CSRF, PostgreSQL y pruebas de despliegue. |

Los tres DEF-PRU quedaron cerrados con la regresión aprobada en v4. HALL-01 a HALL-06 siguen pendientes hasta completar sus acciones.
