# Registro de defectos — La Casa del Ogro

**Versión:** rama `fix/ejercicio4-reglas-reservas`  
**Fecha de identificación:** 22 de noviembre de 2026  
**Estado general:** correcciones incorporadas en la rama; pendientes de ejecución y verificación en el equipo del proyecto.

La severidad se clasifica según el impacto en la operación y la integridad de los datos. Un defecto no se marca como cerrado solo porque el código haya sido modificado: debe ejecutarse el caso asociado y comprobarse el resultado.

| ID | Descripción y comportamiento observado en la versión base | Impacto / severidad | Corrección incorporada en la rama | Casos de regresión | Estado |
|---|---|---|---|---|---|
| DEF-01 | La regla del check-out comparaba solo la hora. Recepción podía operar a las 12:01–12:59 aunque el límite definido era 12:00. | Incumplimiento de regla operativa. **Media**. | Se compara hora, minuto, segundo y microsegundo mediante `is_after_checkout_cutoff`. A las 12:00:00 exactas se permite; después se requiere Administrador. | CP-RF-11-03, CP-RF-11-04, CP-RF-11-05, CP-RF-11-06. | Corregido en código; pendiente ejecución. |
| DEF-02 | La ruta operativa permitía cancelar una reserva `en_curso`, lo que podía dejar la habitación ocupada sin una reserva que pudiera completar el check-out. | Riesgo de inconsistencia del estado de habitación y de la reserva. **Alta**. | Solo se permite cancelar una reserva `confirmada`; las reservas en curso, completadas o canceladas reciben HTTP 409. | CP-RF-13-03, CP-RF-13-04. | Corregido en código; pendiente ejecución. |
| DEF-03 | La ruta operativa de modificación no limitaba la operación a reservas confirmadas. Una reserva en curso o completada podía modificarse mediante POST. | Alteración del historial de reservas. **Alta**. | La ruta exige estado `confirmada` antes de validar fechas o aplicar cambios. | CP-RF-12-03, CP-RF-12-04 y ADM-09 (la ruta administrativa PATCH ya tenía protección). | Corregido en código; pendiente ejecución. |
| DEF-04 | El inicio de limpieza podía insertar más de un registro pendiente para una misma habitación. | Historial duplicado y posible confusión operativa. **Media**. | Antes de iniciar se consulta si existe una limpieza sin finalizar; si existe, se responde HTTP 409. | ADM-29. | Corregido en código; pendiente ejecución. |
| DEF-05 | Python considera `True` y `False` como subtipos de entero. La validación anterior podía aceptar `true` como conteo de una persona. | Entrada inválida que podía alterar el aforo y la alerta asociada. **Media**. | El endpoint y la regla unitaria rechazan valores booleanos explícitamente. | CP-RF-06-04, CP-RF-06-05. | Corregido en código; pendiente ejecución. |

## Criterio de cierre

Para cerrar cada defecto se debe:

1. Ejecutar los casos de regresión indicados.
2. Guardar salida Pytest, captura o log que corresponda.
3. Registrar fecha, resultado obtenido y commit probado.
4. Reejecutar toda la suite automatizada para detectar regresiones.
5. Marcar el defecto como cerrado solo cuando el resultado esperado esté verificado.

**Nota:** hasta ejecutar la rama corregida, no se informa ningún defecto como cerrado por evidencia de ejecución. Los estados anteriores describen la incorporación de la corrección en el código, no una aprobación de pruebas.
