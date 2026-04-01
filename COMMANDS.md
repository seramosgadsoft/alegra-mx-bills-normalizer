# Comandos Rápidos (Quick Reference)

Esta guía de referencia rápida contiene los comandos más comunes para trabajar con el proyecto.

## 🚀 Setup Inicial

```bash
# Clonar e instalar
git clone <repository-url>
cd alegra-mx-bills-normalizer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp config.example.json config.json
# Editar config.json con tus credenciales
```

## ▶️ Ejecución

```bash
# Activar entorno virtual (siempre primero)
source venv/bin/activate  # macOS/Linux
# o
venv\Scripts\activate  # Windows

# Modo TXT (procesamiento con UUIDs)
python main.py --mode txt
python main.py --mode txt --file mi_archivo.txt

# Modo Excel (procesamiento desde spreadsheet)
python main.py --mode excel --file "NIVELACION CHAZKI MX.xlsx"

# Modo Providers (creación de proveedores)
python main.py --mode providers --file DRIVERS.xlsx
```

## 🧪 Testing y Debug

```bash
# Ejecutar tests
python test_components.py

# Inspeccionar archivo Excel
python inspect_excel.py

# Analizar factura individual
python invoice_analyzer.py

# Ver logs
tail -f mexico_normalization.log

# Ver logs en tiempo real con filtro
tail -f mexico_normalization.log | grep "ERROR"
```

## 📦 Gestión de Dependencias

```bash
# Actualizar dependencias
pip install --upgrade -r requirements.txt

# Agregar nueva dependencia
pip install <paquete>
pip freeze > requirements.txt

# Verificar dependencias instaladas
pip list
```

## 🔄 Git

```bash
# Ver estado
git status

# Agregar cambios
git add .
git commit -m "descripción del cambio"
git push

# Crear nueva rama
git checkout -b feature/nueva-caracteristica

# Cambiar de rama
git checkout main

# Ver historial
git log --oneline

# Ver diferencias
git diff
```

## 📊 Reportes

```bash
# Los reportes se generan automáticamente en:
# reports/processing_report_YYYYMMDD_HHMMSS.{json,csv,html}

# Ver último reporte en terminal
cat reports/processing_report_*.json | tail -1

# Abrir último reporte HTML
open reports/processing_report_*.html  # macOS
# o
xdg-open reports/processing_report_*.html  # Linux
```

## 🔧 Configuración

```bash
# Editar configuración principal
nano config.json  # o usa tu editor preferido

# Ver configuración (sin mostrar credenciales)
python -c "import json; print(json.dumps(json.load(open('config.json')), indent=2))" | grep -v "password\|secret\|key"
```

## 🧹 Limpieza

```bash
# Limpiar archivos de cache de Python
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete

# Limpiar logs
rm -f *.log

# Limpiar reportes antiguos (CUIDADO: borra todos los reportes)
rm -rf reports/*.json reports/*.csv reports/*.html
```

## 🔍 Búsqueda y Análisis

```bash
# Buscar UUID específico en logs
grep "UUID-AQUI" mexico_normalization.log

# Contar facturas procesadas exitosamente hoy
grep "SUCCESS" mexico_normalization.log | grep "$(date +%Y-%m-%d)" | wc -l

# Ver errores del día
grep "ERROR" mexico_normalization.log | grep "$(date +%Y-%m-%d)"

# Listar archivos XML disponibles
find bills/ -name "*.xml" | wc -l
```

## 📈 Monitoreo

```bash
# Monitorear ejecución en tiempo real
python main.py --mode excel | tee output.log

# Contar líneas de código
find . -name "*.py" -not -path "./venv/*" -exec wc -l {} + | tail -1
```

## 💾 Backup

```bash
# Backup de configuración (sin credenciales)
cp config.example.json config.backup.example.json

# Backup de código (sin datos sensibles)
git archive --format=zip --output=../backup-$(date +%Y%m%d).zip HEAD
```

## 🆘 Solución Rápida de Problemas

```bash
# Reinstalar todo desde cero
deactivate  # si el venv está activo
rm -rf venv/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Verificar versión de Python
python --version  # Debe ser 3.8+

# Verificar que las dependencias estén instaladas
pip check

# Limpiar y reiniciar
rm -f *.log
python main.py --mode excel
```

## 📝 Notas

- Siempre activa el entorno virtual antes de ejecutar comandos Python
- Los reportes se generan automáticamente después de cada ejecución
- config.json nunca debe subirse a Git (está en .gitignore)
- Para procesar un rango específico de filas, edita DEFAULT_START_ROW y DEFAULT_MAX_ROWS en core/excel_loader.py

---

**Tip**: Guarda este archivo en tus marcadores para acceso rápido a los comandos comunes.
