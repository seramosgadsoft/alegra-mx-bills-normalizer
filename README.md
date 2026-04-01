# Alegra MX Bills Normalizer

Sistema automatizado para la normalización y carga de facturas mexicanas al sistema Alegra. El proyecto procesa facturas desde archivos XML y Excel, validándolas y subiéndolas automáticamente a través de la API de Alegra.

## 📋 Características

- **Múltiples modos de procesamiento:**
  - **TXT Mode**: Procesa facturas desde una lista de UUIDs con archivos XML correspondientes
  - **Excel Mode**: Procesa facturas directamente desde hojas de cálculo Excel
  - **Providers Mode**: Gestiona y crea proveedores en Alegra desde archivos Excel

- **Análisis inteligente de facturas**: Extracción automática de información fiscal mexicana (RFC, UUID, conceptos, impuestos)
- **Integración con Alegra API**: Creación automática de facturas y proveedores
- **Reportes detallados**: Generación de reportes en múltiples formatos (JSON, CSV, HTML)
- **Manejo robusto de errores**: Sistema de reintentos y logging detallado
- **Búsqueda de archivos XML**: Búsqueda recursiva en directorios organizados por mes

## 🚀 Instalación

### Prerrequisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Acceso a la API de Alegra
- Credenciales de servicios ADSOFT (opcional, según configuración)

### Configuración del entorno

1. **Clonar el repositorio:**
```bash
git clone <repository-url>
cd alegra-mx-bills-normalizer
```

2. **Crear y activar entorno virtual:**
```bash
python3 -m venv venv
source venv/bin/activate  # En macOS/Linux
# o
venv\Scripts\activate  # En Windows
```

3. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

4. **Configurar credenciales:**
```bash
cp config.example.json config.json
```

Edita `config.json` con tus credenciales reales:
- Información del cliente (RFC, emails, etc.)
- Credenciales de OAuth de Google (si usas OAuth)
- Endpoints y credenciales de servicios ADSOFT
- Configuración de Alegra

## 📁 Estructura del proyecto

```
alegra-mx-bills-normalizer/
├── main.py                 # Punto de entrada principal
├── config.json            # Configuración (NO incluir en git)
├── config.example.json    # Plantilla de configuración
├── requirements.txt       # Dependencias Python
├── uuids.txt             # Lista de UUIDs a procesar (modo TXT)
├── README.md             # Este archivo
│
├── core/                 # Módulos principales
│   ├── config_loader.py     # Carga de configuración
│   ├── uuid_loader.py       # Carga de UUIDs
│   ├── excel_loader.py      # Carga de datos desde Excel
│   ├── drivers_loader.py    # Carga de proveedores
│   ├── xml_file_searcher.py # Búsqueda de archivos XML
│   ├── invoice_processor.py # Procesamiento de facturas
│   └── provider_processor.py # Procesamiento de proveedores
│
├── models/               # Modelos de datos
│   └── models.py           # Definiciones de clases de datos
│
├── services/             # Servicios externos
│   ├── mexico_invoice_analyzer.py  # Análisis de facturas MX
│   ├── mexico_alegra_service.py    # Cliente API Alegra
│   ├── excel_adapter.py            # Adaptador Excel
│   └── webhook_service.py          # Webhooks
│
├── utils/                # Utilidades
│   └── report_generator.py  # Generación de reportes
│
├── bills/                # Archivos XML (organizados por mes)
│   ├── 01/
│   ├── 02/
│   └── ...
│
└── reports/              # Reportes generados
    └── processing_report_YYYYMMDD_HHMMSS.*
```

## 💻 Uso

### Modo 1: Procesamiento desde lista de UUIDs (TXT Mode)

Procesa facturas desde un archivo `uuids.txt` con sus correspondientes archivos XML.

1. Crear archivo `uuids.txt` con un UUID por línea:
```
550e8400-e29b-41d4-a716-446655440000
6ba7b810-9dad-11d1-80b4-00c04fd430c8
```

2. Organizar archivos XML en la carpeta `bills/` por mes:
```
bills/
  01/
    factura1.xml
  02/
    factura2.xml
```

3. Ejecutar:
```bash
python main.py --mode txt
# o especificar archivo:
python main.py --mode txt --file mi_archivo_uuids.txt
```

### Modo 2: Procesamiento desde Excel (Excel Mode)

Procesa facturas desde una hoja de cálculo Excel.

1. Preparar archivo Excel con las columnas requeridas:
   - UUID
   - Información de factura (proveedor, fecha, monto, etc.)

2. Ejecutar:
```bash
python main.py --mode excel --file "NIVELACION CHAZKI MX.xlsx"
```

**Configuración de rango de filas en `core/excel_loader.py`:**
```python
DEFAULT_START_ROW = 2     # Fila inicial (1-based, omite encabezados)
DEFAULT_MAX_ROWS = None   # None para procesar todo, o número específico
```

### Modo 3: Creación de Proveedores (Providers Mode)

Crea o actualiza proveedores en Alegra desde Excel.

1. Preparar archivo `DRIVERS.xlsx` con información de proveedores:
   - RFC
   - Nombre/Razón Social
   - Email
   - Otros datos del proveedor

2. Ejecutar:
```bash
python main.py --mode providers --file DRIVERS.xlsx
```

## 📊 Reportes

Los reportes se generan automáticamente en la carpeta `reports/` en tres formatos:

- **JSON**: `processing_report_YYYYMMDD_HHMMSS.json`
- **CSV**: `processing_report_YYYYMMDD_HHMMSS.csv`
- **HTML**: `processing_report_YYYYMMDD_HHMMSS.html` (visualización web)

Cada reporte incluye:
- Estado de procesamiento (SUCCESS, ERROR, etc.)
- ID de factura en Alegra
- Mensajes de error (si los hay)
- Fuente de datos (Excel, XML, o ambos)
- Timestamps y detalles de ejecución

## 🔧 Configuración avanzada

### Ajuste de límites de procesamiento

Edita el archivo correspondiente del módulo `core/`:

**Para Excel Mode** (`core/excel_loader.py`):
```python
DEFAULT_START_ROW = 118  # Fila de inicio
DEFAULT_MAX_ROWS = 290   # Número de filas a procesar
```

**Nota importante**: El sistema siempre procesa "una fila más" debido al offset de Excel (1-based indexing).

### Logging

Los logs se guardan en:
- Archivo: `mexico_normalization.log`
- Consola: salida estándar

Nivel de log configurable en `main.py`:
```python
logging.basicConfig(level=logging.INFO)  # Cambiar a DEBUG para más detalle
```

## 🛠️ Desarrollo

### Ejecutar tests
```bash
python test_components.py
```

### Inspeccionar archivos Excel
```bash
python inspect_excel.py
```

### Analizar facturas individuales
```bash
python invoice_analyzer.py
```

## ⚠️ Notas importantes

1. **Archivos sensibles**: Nunca subas `config.json` al repositorio. Usa `config.example.json` como plantilla.

2. **Índices de Excel**: Los números de fila en Excel son 1-based (la fila 1 es el encabezado).

3. **Procesamiento incremental**: El sistema siempre procesa "una fila más" de lo esperado por el offset de Excel.

4. **Estructura de carpetas**: Los archivos XML deben organizarse en carpetas numeradas por mes (01-12).

## 📝 Solución de problemas

### Error: "No valid UUIDs found"
- Verifica que `uuids.txt` tenga formato correcto (un UUID por línea)
- Asegúrate de que el archivo no esté vacío

### Error: "XML file not found"
- Verifica que los archivos XML estén en la carpeta `bills/` correcta
- Revisa que el nombre del archivo contenga el UUID

### Error de autenticación Alegra
- Verifica tus credenciales en `config.json`
- Asegúrate de tener permisos en la API de Alegra

### Error al cargar Excel
- Verifica que el archivo Excel existe y tiene el formato correcto
- Ajusta `DEFAULT_START_ROW` si es necesario

## 📄 Licencia

Este proyecto es de uso interno. Todos los derechos reservados.

## 👥 Contacto

Para soporte o preguntas, contacta a:
- Email de soporte: (configurado en `config.json`)

---

**Última actualización**: Abril 2026