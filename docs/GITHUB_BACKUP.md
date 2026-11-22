# Respaldo del proyecto en GitHub

## Repositorio recomendado

- Nombre sugerido: `la-casa-del-ogro`
- Visibilidad: **Private**
- Rama principal: `main`

## Subir desde Windows con Git

Abre PowerShell dentro de esta carpeta (la que contiene `README.md`) y ejecuta:

```powershell
git init
git add .
git status
git commit -m "Initial backup - La Casa del Ogro"
git branch -M main
git remote add origin https://github.com/USUARIO/la-casa-del-ogro.git
git push -u origin main
```

Reemplaza `USUARIO` por tu nombre de usuario de GitHub y usa la URL del repositorio privado que creaste. Antes de `git commit`, revisa `git status`: no debe aparecer ninguna base SQLite, archivo `.env`, token ni información personal real.

## Guardar cambios posteriores

```powershell
git add .
git status
git commit -m "Describe el cambio realizado"
git push
```

## Importante: código y datos son respaldos diferentes

El repositorio contiene el código, pruebas y documentación. La base de datos local se excluye intencionalmente mediante `.gitignore`. Para respaldar los datos del sistema, cierra la aplicación y copia `data/casa_ogro.sqlite3` a una ubicación privada y cifrada. No la subas al repositorio.
