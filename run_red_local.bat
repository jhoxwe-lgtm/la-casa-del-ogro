@echo off
cd /d "%~dp0"
set CASA_OGRO_HOST=0.0.0.0
set CASA_OGRO_PORT=8000
echo =====================================================
echo  LA CASA DEL OGRO - MODO RED LOCAL
echo =====================================================
echo El servidor escuchara en las interfaces de red.
echo Busca la direccion IPv4 de este PC con IPCONFIG.
echo Los otros equipos deben abrir: http://IP-DE-ESTE-PC:8000
echo No cierres esta ventana mientras uses la aplicacion.
echo =====================================================
py -m casa_ogro.webapp
pause
