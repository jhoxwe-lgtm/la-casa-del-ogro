# La Casa del Ogro — Ejercicio 4 (versión 3)

Prototipo web para el Sistema de Gestión Hotelera **La Casa del Ogro**, basado en los requisitos RF-01 a RF-17 y RNF-01 a RNF-07 del informe de los Ejercicios 2 y 3. Incluye una aplicación web para los roles Recepción, Limpieza y Administración, pruebas automatizadas con Pytest y un panel de Administración completa para preparar y demostrar casos manuales.

## Tecnologías

- Python 3.10 o superior (recomendado 3.11+).
- Servidor WSGI y SQLite de la biblioteca estándar; no requiere Flask ni servidor de base de datos externo.
- HTML, CSS y JavaScript sin framework.
- Pytest y pytest-cov para pruebas automatizadas y cobertura de ramas.

## Ejecutar en Windows

1. Descomprime el ZIP en una carpeta, por ejemplo `C:\CasaDelOgro`.
2. Abre esa carpeta en Visual Studio Code o una terminal.
3. Comprueba Python con `py --version`.
4. Instala las dependencias de pruebas: `py -m pip install -r requirements-dev.txt`.
5. Ejecuta `run_demo.bat`.
6. Abre `http://127.0.0.1:8000`.

La base se crea automáticamente en `data/casa_ogro.sqlite3`.

## Acceso desde otros equipos de la red local (LAN)

- Para usar solo en el PC servidor, sigue utilizando `run_demo.bat` (escucha en `127.0.0.1`).
- Para compartir en una red local autorizada, ejecuta `run_red_local.bat` (escucha en `0.0.0.0`, puerto TCP 8000).
- En el PC servidor ejecuta `ipconfig` y busca la IPv4 del adaptador Wi-Fi. Desde el otro equipo abre `http://IP-DEL-PC-SERVIDOR:8000`. No uses `0.0.0.0` en el navegador.
- Puede ser necesario permitir TCP 8000 en el Firewall de Windows. En redes universitarias, Wi-Fi y Ethernet pueden estar aisladas o en VLAN diferentes; si ocurre, solicita autorización al área TI para permitir el acceso. No intentes evadir esa segmentación.
- Esta modalidad es solo para una demostración controlada: el prototipo usa HTTP sin TLS. Cambia las contraseñas demo, no uses datos personales reales y no publiques el puerto en Internet.
- Guía paso a paso: `docs/ACCESO_RED_LOCAL_WINDOWS.md`.

## Cuentas iniciales

| Rol | Usuario | Contraseña |
|---|---|---|
| Administrador | `admin` | `admin123` |
| Recepción | `recepcion` | `recep123` |
| Limpieza | `limpieza` | `limp123` |

Son credenciales de demostración local. Se recomienda cambiarlas desde Administración y pruebas antes de utilizar otros datos.

## Panel de Administración completa

Al iniciar sesión como Administrador aparece **Administración y pruebas**. El panel usa la misma SQLite que la aplicación principal y contiene:

- **General:** indicadores y accesos rápidos.
- **Habitaciones:** crear, editar, desactivar/reactivar o eliminar cuando no exista historial; cada nueva habitación obtiene su espacio monitorizado y sensor simulado. Herramientas para preparar estado de limpieza y ejecutar el flujo.
- **Huéspedes:** crear, editar y eliminar cuando no existan reservas asociadas.
- **Reservas:** crear, editar, cancelar, check-in, check-out o eliminar reservas cerradas/no activas con validaciones de disponibilidad e integridad.
- **Usuarios y roles:** crear cuentas; editar usuario/rol; activar/desactivar; restablecer contraseña; eliminar solo si no hay historial. No permite desactivar la propia sesión ni quitar el último Administrador activo.
- **Sensores y aforo:** agregar, quitar y activar/desactivar sensores; configurar capacidades de piscina y habitaciones.
- **Pruebas manuales:** lecturas simuladas 19/20/21; lectura antigua (+3 min); toggle de sensor; consulta de limpiezas/alertas; medición exploratoria de 10 solicitudes; health check y reinicio de datos operativos.
- **Bitácora:** historial de acciones administrativas.

Las reglas de integridad evitan borrar un huésped con reservas, una habitación con historial o una cuenta con operaciones asociadas. En esos casos, el panel propone retirar/desactivar el registro en lugar de borrar su historia.

La sección incluye un recorrido recomendado en `docs/GUIA_PANEL_ADMINISTRACION.md`.

## Casos de prueba y trazabilidad

- Plan detallado: `docs/PLAN_DE_PRUEBAS.md`.
- Matriz RF/RNF y pruebas de administración: `docs/MATRIZ_COBERTURA.csv`.
- Código automatizado: `tests/test_requirements.py`.
- Evidencia de ejecución Pytest: `evidence/pytest_results.txt`.

Ejecuta `run_tests.bat` o usa:

```bash
py -m pip install -r requirements-dev.txt
py -m pytest -v --cov=casa_ogro.rules --cov-branch --cov-report=term-missing
```

La rama de correcciones incorpora **80 casos automatizados**: 51 casos funcionales/no funcionales y de reglas de negocio, más 29 pruebas del panel administrativo ampliado. La cobertura de caja blanca se mide expresamente sobre `casa_ogro.rules`; no representa la cobertura total de toda la aplicación.

**Importante:** `evidence/pytest_results.txt` conserva la ejecución histórica de 58 pruebas de la versión base. Después de ejecutar esta rama, guarda una nueva salida con los 80 casos, la cobertura, la fecha y el commit probado; no presentes la evidencia histórica como si correspondiera a esta versión.

## Limitaciones que deben explicarse en la presentación

- **RNF-03:** `/health` solo verifica una respuesta puntual; no demuestra 99 % de disponibilidad mensual. Para validarlo se requiere monitoreo durante el período mensual.
- **RNF-02:** la medición exploratoria del panel lanza 10 consultas simultáneas desde una misma sesión. No sustituye pruebas con 10 sesiones independientes y medición repetida en el equipo de presentación.
- **RNF-04:** se debe realizar y registrar la observación manual del número de interacciones desde el panel hasta consultar el estado.
- **RNF-05:** la prueba automática mide recepción/consulta local; debe repetirse en el equipo de presentación y registrar el tiempo real.
- **Sensores:** las lecturas son simuladas según el alcance académico. No se integran sensores físicos, cámaras, reconocimiento facial ni bloqueo automático de acceso.
- El prototipo demuestra flujos y reglas de negocio; no es un sistema hotelero listo para producción.

## Actualizar desde v2 conservando tus datos

1. Cierra la aplicación v2 y guarda una copia completa de su carpeta.
2. Descomprime v3 en una carpeta nueva.
3. Copia `data/casa_ogro.sqlite3` desde la carpeta v2 a la carpeta `data` de v3, reemplazando la base de ejemplo incluida.
4. Ejecuta `run_demo.bat`.

Al iniciar, v3 migra automáticamente la base anterior: agrega `rooms.active` y crea `admin_audit` si faltan. Los datos ya existentes se conservan.

## Alcance de datos

Crear una habitación crea también un espacio monitorizado y un sensor simulado. Desactivar una habitación o cuenta permite retirarla sin perder historial. Un sensor con lecturas se desactiva en lugar de eliminarse. El botón de limpieza de demostración borra únicamente datos operativos (huéspedes, reservas, limpiezas, lecturas y alertas), conservando usuarios, habitaciones, espacios, sensores, capacidades y bitácora. Requiere escribir exactamente `LIMPIAR DATOS OPERATIVOS`.

## Respaldo en GitHub

Este repositorio debe mantenerse **privado** mientras contenga el código del prototipo académico y las credenciales de demostración descritas arriba. No se incluye `data/casa_ogro.sqlite3`: la base local se crea automáticamente al iniciar la aplicación. Esto evita subir datos de huéspedes, usuarios o pruebas guardados en el equipo.

Antes de compartir el repositorio con otras personas:

1. Cambia las contraseñas de demostración.
2. No agregues archivos `.sqlite3`, `.db`, `.env`, tokens ni contraseñas reales.
3. Mantén este repositorio privado salvo que el equipo decida conscientemente publicar una versión sanitizada.
4. Para respaldar los datos operativos, realiza una copia cifrada de la base SQLite por separado y guárdala en un lugar privado; no la subas al repositorio de código.
