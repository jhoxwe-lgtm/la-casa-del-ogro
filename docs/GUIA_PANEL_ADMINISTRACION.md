# Guía del panel de Administración completa y pruebas manuales

Proyecto: **Sistema de Gestión Hotelera — La Casa del Ogro**  
Versión: **Ejercicio 4 — Panel administrativo ampliado (v3)**

## 1. Acceso y seguridad

Inicia sesión con una cuenta de rol `admin`. En el menú aparecerá **Administración y pruebas**. La sección y sus rutas API están protegidas para que Recepción y Limpieza no puedan administrar habitaciones, cuentas, sensores ni reiniciar datos.

Credenciales iniciales de demostración:

| Rol | Usuario | Contraseña |
|---|---|---|
| Administrador | `admin` | `admin123` |
| Recepción | `recepcion` | `recep123` |
| Limpieza | `limpieza` | `limp123` |

Cambia las contraseñas de demostración antes de utilizar datos reales. Este es un prototipo académico local, no un sistema listo para producción.

## 2. Secciones del panel

### General

Muestra indicadores de habitaciones activas, huéspedes, reservas, usuarios activos, sensores activos y alertas. Incluye accesos rápidos a las demás secciones y un botón para actualizar los módulos principales desde la misma base de datos.

### Habitaciones

Permite:

- Crear una habitación con número, tipo y capacidad.
- Editar número, tipo y capacidad.
- Desactivar o reactivar una habitación.
- Eliminar físicamente una habitación solo cuando no tenga reservas, limpiezas, lecturas ni alertas asociadas.
- Forzar un estado de prueba `disponible` o `en limpieza` cuando no haya una reserva ocupada ni una limpieza pendiente.
- Preparar una limpieza, registrar inicio y finalizarla desde el mismo flujo utilizado en la aplicación.

**Importante:** al crear una habitación también se crea automáticamente su espacio monitorizado y un sensor simulado. La capacidad de la habitación y la capacidad del espacio quedan sincronizadas. Si una habitación tiene historial, usa **Desactivar** en vez de eliminarla: desaparecerá de la operación normal, pero su historia se conserva. Para demostrar el estado `ocupada`, registra una reserva y realiza check-in; no se fuerza manualmente.

### Huéspedes

Permite crear, editar y eliminar huéspedes. La eliminación solo se acepta si el huésped no conserva reservas asociadas. Para liberar ese huésped, primero elimina o cancela sus reservas según el caso que estés demostrando; el historial de reservas no se borra automáticamente.

### Reservas

Permite crear reservas, editar reservas confirmadas, cancelarlas o eliminarlas cuando no están en curso. En la tabla aparecen accesos para check-in y check-out de acuerdo con el estado de la reserva. El sistema vuelve a validar las fechas, la habitación y la disponibilidad.

- Una reserva `en_curso` no se puede borrar ni editar desde el panel; primero registra el check-out.
- La modificación y cancelación tardías siguen exigiendo autorización administrativa desde los flujos operativos.
- Para probar el check-in anticipado o el check-out tardío, utiliza las acciones normales con el reloj/fecha del caso preparado.

### Usuarios y roles

Permite:

- Crear usuarios de Recepción, Limpieza o Administración.
- Cambiar el nombre de usuario y el rol.
- Activar o desactivar cuentas.
- Restablecer la contraseña (deja el campo vacío para mantener la actual).
- Eliminar una cuenta solo cuando no tenga operaciones históricas asociadas.

No se puede desactivar la propia sesión ni retirar el último Administrador activo. Las cuentas con registros históricos se desactivan para conservar la trazabilidad.

### Sensores y aforo

Permite agregar sensores a los espacios monitorizados, activar/desactivar sensores y quitarlos. Cada espacio admite un sensor activo a la vez. Si un sensor tiene lecturas, al quitarlo se desactiva en vez de borrarse, para conservar el historial.

También permite configurar la capacidad máxima de la piscina y de cada habitación monitorizada. Al modificar la capacidad de una habitación, se actualiza la ficha de habitación y el espacio monitorizado asociado.

### Pruebas manuales

Incluye herramientas para:

- Enviar lecturas simuladas con un conteo y fecha/hora seleccionables.
- Probar rápidamente la piscina con 19, 20 y 21 personas (normal, completo y excedido, cuando la capacidad configurada es 20).
- Enviar una lectura de hace tres minutos para demostrar el estado `desactualizado` de RNF-06.
- Desactivar un sensor y comprobar que las nuevas lecturas se rechazan.
- Consultar el historial de limpiezas y alertas.
- Ejecutar 10 solicitudes de consulta simultáneas como medición exploratoria de rendimiento.
- Consultar `/health` como comprobación puntual del servicio.
- Limpiar los datos operativos de demostración para comenzar una nueva ronda.

La limpieza de datos operativos requiere escribir exactamente `LIMPIAR DATOS OPERATIVOS`. Elimina huéspedes, reservas, limpiezas, lecturas y alertas. Conserva usuarios, habitaciones, espacios, sensores y capacidades; también conserva la bitácora administrativa.

**Límites de medición:** la prueba rápida de 10 solicitudes usa una misma sesión del navegador; no sustituye una medición con 10 sesiones independientes. `/health` no demuestra el 99 % de disponibilidad mensual de RNF-03: ese requisito requiere monitoreo continuo durante el período acordado.

### Bitácora

Muestra las operaciones administrativas guardadas: quién realizó la acción, tipo de acción, entidad afectada, identificador, detalle y fecha/hora. La bitácora permite apoyar la trazabilidad de las demostraciones. No almacena contraseñas.

## 3. Reflejo en la aplicación principal

El panel y los módulos ordinarios usan la misma base SQLite: `data/casa_ogro.sqlite3`. Por ejemplo:

- Una habitación nueva aparece en Habitaciones y en el Resumen.
- Un huésped editado aparece con sus datos actualizados en Huéspedes y Reservas.
- La capacidad modificada se usa al comparar las próximas lecturas del sensor.
- Un sensor desactivado ya no acepta lecturas.
- La limpieza finalizada devuelve la habitación a `disponible` en el Resumen.

Usa **Actualizar todo** dentro del panel o el botón de actualización de los módulos cuando necesites volver a consultar la base de datos.

## 4. Recorrido recomendado de demostración

1. Inicia sesión como Administrador.
2. Crea la habitación 301, tipo Triple, capacidad 3; comprueba que aparece en Habitaciones y que se genera un sensor.
3. Crea un huésped y una reserva para esa habitación.
4. Edita los datos del huésped y confirma que la reserva muestra el nombre actualizado.
5. Registra check-in y comprueba el estado `ocupada`.
6. Registra check-out; la habitación debe pasar a `en limpieza`.
7. Registra inicio y finalización de limpieza; debe volver a `disponible`.
8. Envía 19, 20 y 21 personas al sensor de piscina; muestra los estados y la alerta.
9. Revisa una alerta y comprueba el registro de usuario/fecha.
10. Crea un usuario de Limpieza, inicia sesión con esa cuenta y demuestra que no puede acceder al menú administrativo.
11. Abre la bitácora y muestra las acciones registradas.

## 5. Actualizar desde la versión anterior sin perder registros

1. Cierra la aplicación anterior.
2. Copia toda la carpeta anterior a otra ubicación como respaldo.
3. Descomprime la versión v3 en una carpeta nueva.
4. Copia el archivo `data/casa_ogro.sqlite3` de la versión anterior a la carpeta `data` de la nueva versión, reemplazando el archivo de demostración incluido.
5. Ejecuta `run_demo.bat`.

La aplicación ejecuta una migración compatible al iniciar: agrega la columna de activación de habitaciones y crea la bitácora si todavía no existen. No elimina los huéspedes, reservas o registros existentes.

## 6. Evidencias para el Ejercicio 4

Para cada caso manual, conserva una captura o salida que muestre el ID del caso, la fecha y la versión del código/commit. Es útil capturar el estado anterior, la acción y el resultado posterior. No declares un RNF validado solo porque una acción se ejecutó una vez: registra la medición real y su entorno.
