# Acceder a La Casa del Ogro desde otros equipos de la red local

## Importante antes de compartir

- Utiliza este modo solo en una red privada/de confianza y con autorización del responsable de la red.
- El prototipo utiliza HTTP sin cifrado TLS. No lo publiques en Internet ni lo uses para datos personales reales.
- Cambia las contraseñas de demostración antes de compartirlo. Las cuentas iniciales son conocidas.
- No configures redirección de puertos (port forwarding) en el router.
- En una universidad, los equipos Wi-Fi y Ethernet pueden estar en VLAN distintas o tener aislamiento entre clientes. En ese caso, solo el área de redes puede habilitar la comunicación autorizada.

## 1. Iniciar el servidor en modo LAN

1. Conecta el PC que ejecutará La Casa del Ogro al Wi-Fi de la universidad.
2. Abre la carpeta del proyecto.
3. Ejecuta `run_red_local.bat`.
4. Mantén abierta esa ventana. Si se cierra, el servidor se detiene.

El modo habitual `run_demo.bat` sigue siendo local (`127.0.0.1`). Para compartir en la red, utiliza `run_red_local.bat`, que escucha en `0.0.0.0`.

## 2. Obtener la dirección IPv4 del PC servidor

1. Presiona `Windows + R`, escribe `cmd` y presiona Enter.
2. Ejecuta `ipconfig`.
3. Busca el adaptador `Adaptador de LAN inalámbrica Wi-Fi`.
4. Anota la `Dirección IPv4`, por ejemplo `10.20.34.56` o `192.168.1.25`.
5. En otro PC conectado a una red con permiso de acceso, abre el navegador y escribe `http://10.20.34.56:8000`, reemplazando la IP por la real.

No uses `0.0.0.0` en el navegador. Esa dirección solo indica que el servidor escucha en todas las interfaces.

## 3. Firewall de Windows

Si Windows pregunta si Python puede aceptar conexiones, no habilites el acceso en redes públicas sin autorización. En un equipo institucional, consulta primero a soporte TI.

Si eres el administrador autorizado del PC y la política de red lo permite, puedes crear una regla limitada al puerto 8000 y a la subred local desde PowerShell como Administrador:

```powershell
New-NetFirewallRule -DisplayName "Casa del Ogro TCP 8000 LAN" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8000 -RemoteAddress LocalSubnet -Profile Any
```

Para eliminarla al terminar:

```powershell
Remove-NetFirewallRule -DisplayName "Casa del Ogro TCP 8000 LAN"
```

La regla limita el origen a la subred local reconocida por Windows; aun así, en una red universitaria la subred puede ser amplia. Sigue las reglas de la institución y solicita a TI que limite el acceso a los equipos autorizados si corresponde.

## 4. Comprobar conectividad desde un PC cliente

En el PC cliente, abre PowerShell y ejecuta (sustituye la IP):

```powershell
Test-NetConnection 10.20.34.56 -Port 8000
```

Si `TcpTestSucceeded` es `True`, abre en el navegador `http://10.20.34.56:8000`.

Si es `False`, revisa:

- Que el servidor siga ejecutándose.
- Que utilizaste la IPv4 del adaptador Wi-Fi correcto.
- Que el Firewall permita TCP 8000.
- Que Wi-Fi y Ethernet puedan comunicarse según la configuración de la universidad.

Si el firewall está correctamente configurado y sigue fallando, puede existir aislamiento Wi-Fi/Ethernet, separación por VLAN o una ACL institucional. No intentes evadirla: pide al área de redes que autorice el flujo desde los equipos clientes hacia la IP del servidor por TCP 8000.

## 5. Detener el acceso compartido

Cierra la ventana del servidor con `Ctrl + C`. Si creaste la regla de firewall temporal, elimínala con `Remove-NetFirewallRule`.

## Seguridad para la demostración

- Cambia `admin123`, `recep123` y `limp123` antes de compartir.
- Comparte la IP solo con las personas que harán la demostración.
- No introduzcas datos reales de huéspedes.
- Recuerda que HTTP transmite las credenciales sin cifrado; este modo es únicamente para una demostración controlada en una LAN autorizada.
