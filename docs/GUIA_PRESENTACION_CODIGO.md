# Guía para presentar el código - La Casa del Ogro

## Orden recomendado

### 1. static/index.html
Buscar: PRESENTACIÓN 1

Explicación:
Desde la interfaz enviamos una lectura simulada.
Los botones permiten probar diferentes cantidades de personas.

### 2. casa_ogro/webapp.py
Buscar: PRESENTACIÓN 2

Explicación:
El servidor recibe la lectura, valida los datos,
guarda la información y comprueba el estado del aforo.

### 3. casa_ogro/rules.py
Buscar: PRESENTACIÓN 3

Explicación:
Aquí están las reglas que comparan el conteo
con la capacidad máxima del espacio.

Ejemplo:
19 personas: normal.
20 personas: completo.
21 personas: excedido.

### 4. tests/test_rules.py
Buscar: PRESENTACIÓN 4

Explicación:
Estas pruebas comprueban que las reglas entreguen
el resultado esperado para cada situación.

### 5. casa_ogro/webapp.py
Buscar: PRESENTACIÓN 5

Explicación:
El sistema permite consultar las alertas y registrar
cuándo Recepción revisó una de ellas.

## Recorrido completo

Interfaz web
-> Servidor
-> Reglas de negocio
-> Base de datos
-> Resultado mostrado en pantalla

## Datos importantes

Las lecturas de los sensores son simuladas.
La cobertura del 100 % corresponde a casa_ogro/rules.py.
La ejecución registrada fue de 80 pruebas aprobadas.
