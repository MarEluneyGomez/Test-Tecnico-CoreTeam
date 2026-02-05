# Test Técnico – HTTP, Procesamiento de Datos y KPIs

## Autor
Martín Eluney Gómez Piñeiro

# Descripción


Este proyecto implementa una solución en Python 3 que cubre distintos aspectos habituales en el consumo de APIs y el procesamiento de datos:

- Interacción con endpoints de httpbin.org simulando escenarios comunes (autenticación básica, manejo de cookies y sesiones, manejo de errores 403, extracción de datos en JSON, XML y HTML, envío de formularios y redirecciones).
- Generación de una bitácora ficticia de llamadas HTTP en formato JSONL.
- Cálculo de KPIs diarios por endpoint a partir de dicha bitácora.
El proyecto está alineado con los requisitos definidos en el documento del test técnico.

--------------------------------------

# Requisitos

Python 3.8 o superior
Librerías utilizadas: 
- requests
- beautifulsoup4
- lxml
- numpy

Instalación de dependencias
```bash
pip install requests beautifulsoup4 lxml numpy
```

Requisitos adicionales:

- Pentaho Data Integration (Spoon)
- Base de datos SQLite: `data/kpi.db` (se crea o reutiliza según configuración)

# Uso

Este script interactúa directamente con httpbin.org y realiza las siguientes operaciones:

- Autenticación básica usando HTTP Basic Auth contra /basic-auth/usuario_test/clave123.
- Manejo de cookies y sesiones mediante requests.Session().
- Simulación de acceso denegado (403) utilizando el endpoint /status/403.
- Extracción de datos: 
    - JSON desde /get, guardado en out/datos.json.
    - XML desde /xml, parseado con lxml y guardado en out/datos.xml.
    - HTML desde /html, extrayendo el <title> de la página y guardándolo en out/titulo.html.
- Envío de formulario mediante POST al endpoint /post.
- Manejo de redirecciones usando /redirect-to?url=/get.


Ejecución:
```bash
python cliente_http.py
```

# Generación de datos ficticios – `generar_datos.py`


Este script crea un archivo JSONL que simula una bitácora de llamadas HTTP.


Cada registro contiene:

- timestamp_utc: fecha y hora en UTC dentro de los últimos 3 días.
- endpoint: endpoint llamado.
- status_code: código HTTP simulado.
- elapsed_ms: tiempo de respuesta simulado.
- parse_result: resultado del parseo (ok o error).


Ejecución de ejemplo:
```bash
python generar_datos.py --n_registros 500 --salida out/datos.jsonl --seed 42
```


El uso de --seed permite reproducir siempre los mismos datos.


# Cálculo de KPIs – `calcular_kpi.py`


Este script procesa el archivo out/datos.jsonl y genera un archivo CSV con KPIs diarios por endpoint base.
KPIs calculados:

- requests_total
- success_2xx
- client_4xx
- server_5xx
- parse_errors
- avg_elapsed_ms
- p90_elapsed_ms (percentil 90 calculado con numpy.percentile)

Los endpoints se normalizan eliminando parámetros y valores variables (por ejemplo, /status/403 → /status).


Ejecución:
```bash
python calcular_kpi.py --input out/datos.jsonl --output out/kpi_por_endpoint_dia.csv *FALTA*
```
---
# ETL KPI Diarios (Pentaho PDI / Spoon)
## Conexión a base de datos

Se utiliza una conexión local en PDI llamada:

- **Nombre**: `sqlite_kpi`
- **Tipo**: SQLite
- **Archivo DB**: `data/kpi.db`

Las “credenciales” (para SQLite no hay usuario/contraseña) y la ruta del archivo `.db` se documentan en `Base de Datos/db_config.md`.  
Esto evita hardcodear información de entorno dentro de la documentación o del repositorio.

## Transformación: `t_load_kpi.ktr` (Carga)

### Objetivo
Carga KPIs desde `out/kpi_por_endpoint_dia.csv` hacia SQLite, creando dos tablas:

- `stg_kpi_endpoint_dia` (staging)
- `fct_kpi_endpoint_dia` (copia directa desde staging)

### Flujo principal
1. **CSV Input**: lectura de `out/kpi_por_endpoint_dia.csv`.
2. **Tipificación**: asignación de tipos adecuados:
   - fecha (`Date`)
   - enteros (`Integer`)
   - decimales (`Number`)
3. **Validación básica (sanidad)**:
   - descarta filas con `requests_total <= 0`
   - descarta filas con `p90_elapsed_ms < avg_elapsed_ms`
4. **Salida**:
   - inserta en `stg_kpi_endpoint_dia` (opcionalmente con “Vaciar tabla” para idempotencia)
   - copia desde `stg_kpi_endpoint_dia` a `fct_kpi_endpoint_dia` con “Vaciar tabla” (idempotencia)

> Importante: si las tablas no existen, se crean ejecutando el DDL generado desde el botón **SQL** en los pasos *Table Output*.


## Transformación: `t_check_kpi.ktr` (Validación post-carga)

### Objetivo
Validar consistencia post-carga: que el número de filas cargadas coincida con la suma de códigos de estado HTTP.

Condición requerida:
- COUNT(*) = SUM(success_2xx + client_4xx + server_5xx)

### Implementación (resumen)
- **Table Input** consulta `fct_kpi_endpoint_dia` y obtiene:
  - `filas = COUNT(*)`
  - `total_status = SUM(success_2xx + client_4xx + server_5xx)` (con COALESCE para nulos)
- **Calculator** calcula `diff = filas - total_status`
- **Filter Rows** evalúa `diff = 0`
  - TRUE: validación OK (termina normalmente)
  - FALSE: se fuerza el error (por ejemplo con `Modified Java Script Value` usando `throw`) para que el Job detecte fallo


## Job: `j_daily_kpi.kjb` 

### Objetivo (según consigna 2.2)
1. Ejecutar la transformación `t_load_kpi.ktr`.
2. Ejecutar una verificación posterior (SQL / Table Exists) para asegurar la consistencia de la carga.
3. Registrar en un log el resultado (OK/ERROR) y cualquier error.

### Flujo del Job
1. **Start**
2. **Transformation**: ejecuta `t_load_kpi.ktr`
3. **Transformation**: ejecuta `t_check_kpi.ktr` (verificación post-carga)
4. **Logging**:
   - rama OK → `Write to log` (mensaje de éxito) → `Success`
   - rama ERROR → `Write to log` (mensaje de error) → `Abort`

> Nota: en esta implementación, la verificación por SQL se realiza en `t_check_kpi.ktr` debido a limitaciones de algunas versiones de PDI donde el job entry SQL no expone resultados para evaluación. La lógica queda igualmente conforme a la consigna (validación post-carga mediante SQL).


## Resultado esperado

- Se cargan tablas:
  - `stg_kpi_endpoint_dia`
  - `fct_kpi_endpoint_dia`
- El Job finaliza:
  - OK si `COUNT(*) = SUM(success_2xx + client_4xx + server_5xx)`
  - ERROR si la validación falla o hay problemas de carga
- Se registran mensajes en el log del Job (Write to log).



## Entregables

- `etl_pdi/t_load_kpi.ktr`
- `etl_pdi/t_check_kpi.ktr`
- `etl_pdi/j_daily_kpi.kjb`

---

# Generación de reporte HTML – generar_reporte.py
Este script lee out/kpi_por_endpoint_dia.csv y genera un reporte HTML con una tabla y dos gráficos.
Qué hace:

- Carga el CSV con pandas.
- Genera gráficos con matplotlib y los guarda en el mismo directorio del reporte: 
   - requests.png: barra horizontal con requests totales por endpoint (endpoint_base).
   - p90_por_endpoint.png: barra con el promedio de p90_elapsed_ms por endpoint.

- Renderiza el reporte HTML utilizando la plantilla templates/reporte.html, reemplazando placeholders por contenido dinámico: 
- {{{TABLA_KPI}}} → tabla HTML del dataframe
- {{{IMG_REQUESTS}}} → `requests.png`
- {{{IMG_P90}}} → `p90_por_endpoint.png`

Ejecución:
```bash
python generar_reporte.py --input out/kpi_por_endpoint_dia.csv --output out/report/kpi_diar

```


Salidas generadas (en `out/report/`):

- `kpi_diario.html`
- `requests.png`
- `p90_por_endpoint.png`
