# Casos de prueba de sistema — navegador

La suite WSGI/API no automatiza clics ni renderizado. Ejecutar en Chrome/Edge, guardar fecha, SHA, sistema operativo y capturas nombradas por ID.

## CP-SYS-RESERVA-01 — Reserva y limpieza
- **Requisitos:** RF-01, RF-03, RF-04, RF-05, RF-10, RF-11.
- **Nivel/tipo:** Sistema, caja negra.
- **Objetivo:** completar flujo de Recepción, Administrador y Limpieza.
- **Precondiciones/datos:** aplicación activa; huésped prueba; habitación 101; fechas válidas; cuentas preparadas.
- **Pasos:** login Recepción; crear huésped/reserva; consultar disponibilidad; check-in y check-out; login Limpieza; iniciar/finalizar limpieza; consultar estado.
- **Esperado:** habitación disponible -> ocupada -> en limpieza -> disponible.
- **Evidencia:** `CP-SYS-RESERVA-01_pasoNN.png`. Estado: Pendiente.

## CP-SYS-AFORO-01 — Aforo, alerta y recuperación
- **Requisitos:** RF-06, RF-07, RF-14, RF-15, RF-16, RF-17, RNF-06, RNF-07.
- **Nivel/tipo:** Sistema, caja negra.
- **Objetivo:** demostrar función crítica de aforo.
- **Precondiciones/datos:** sensor-piscina activo; capacidad 20; conteos 19/20/21, lectura antigua y nueva.
- **Pasos:** enviar lecturas; observar normal/completo/excedido; revisar alerta; enviar timestamp antiguo; observar desactualizado; enviar lectura actual; verificar recuperación; probar payload extra.
- **Esperado:** estados, alerta y recuperación correctos; datos personales/imágenes rechazados.
- **Evidencia:** `CP-SYS-AFORO-01_pasoNN.png` y log. Estado: Pendiente.

## CP-SYS-RNF01-01 — Acción no autorizada
- **Requisito:** RNF-01. **Nivel/tipo:** Sistema, caja negra.
- **Pasos:** login Limpieza; comprobar menú; intentar ruta protegida; verificar rechazo sin cambios.
- **Esperado:** acceso denegado. Estado: Pendiente.

## CP-SYS-RNF02-01 — Rendimiento en equipo defensa
- **Requisito:** RNF-02. **Nivel/tipo:** Sistema, caja negra/rendimiento.
- **Pasos:** ejecutar diez sesiones concurrentes; guardar tiempos/errores; repetir tres veces.
- **Esperado:** diez respuestas válidas y umbral del requisito. Estado: Pendiente.

## CP-SYS-RNF03-01 — Disponibilidad mensual
- **Requisito:** RNF-03. **Nivel/tipo:** Sistema, caja negra/disponibilidad.
- **Pasos:** monitor continuo; registrar checks/fallos en el mes; calcular uptime.
- **Esperado:** 99% demostrado por historial, no por healthcheck puntual.
- **Estado:** No validado hasta completar período mensual.

## CP-SYS-RNF04-01 — Usabilidad
- **Requisito:** RNF-04. **Nivel/tipo:** Sistema, caja negra/usabilidad.
- **Pasos:** tres participantes localizan habitación 101 desde inicio; contar acciones individuales.
- **Esperado:** máximo tres interacciones por participante. Estado: Pendiente.

## CP-SYS-RNF05-01 — Latencia visible
- **Requisito:** RNF-05. **Nivel/tipo:** Sistema, caja negra/rendimiento.
- **Pasos:** enviar diez lecturas con panel abierto; medir hasta visualización; calcular min/promedio/máximo.
- **Esperado:** menos de 10s. Estado: Pendiente.
