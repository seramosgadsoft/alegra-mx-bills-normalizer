# Guía de Inicialización de Git

Esta guía te ayudará a inicializar el repositorio Git y hacer tu primer commit.

## 🚀 Pasos para el primer commit

### 1. Inicializar el repositorio Git

```bash
cd /Users/sergioalejandroramosgrajales/Documents/ADSOFT/PROJECTS/CHAZKI/alegra-mx-bills-normalizer
git init
```

### 2. Verificar archivos que serán incluidos

Revisa qué archivos **NO** serán incluidos (están en .gitignore):
```bash
git status --ignored
```

Verifica qué archivos **SÍ** serán incluidos:
```bash
git status
```

### 3. Configurar Git (si aún no lo has hecho)

```bash
git config --global user.name "Tu Nombre"
git config --global user.email "tu-email@ejemplo.com"
```

### 4. Agregar archivos al staging

```bash
git add .
```

### 5. Verificar lo que será incluido en el commit

```bash
git status
```

**IMPORTANTE**: Verifica que los siguientes archivos **NO** aparezcan en la lista:
- ❌ `config.json` (contiene credenciales)
- ❌ `config_qa.json` (contiene credenciales)
- ❌ `uuids.txt` (datos de entrada)
- ❌ `*.xlsx` (archivos de datos)
- ❌ `bills/` (archivos XML de facturas)
- ❌ `reports/` (reportes generados)
- ❌ `venv/` (entorno virtual)
- ❌ `*.log` (archivos de log)

**Deben aparecer**:
- ✅ `.gitignore`
- ✅ `README.md`
- ✅ `config.example.json`
- ✅ `requirements.txt`
- ✅ `main.py`
- ✅ Todos los archivos en `core/`, `models/`, `services/`, `utils/`
- ✅ Archivos de script Python (`test_components.py`, etc.)

### 6. Crear el primer commit

```bash
git commit -m "Initial commit: Alegra MX Bills Normalizer

- Sistema de normalización de facturas mexicanas
- Integración con API de Alegra
- Soporte para procesamiento desde Excel, XML y lista de UUIDs
- Generación de reportes en JSON, CSV y HTML
- Gestión de proveedores
"
```

### 7. Crear el repositorio en GitHub

1. Ve a [GitHub](https://github.com) y haz login
2. Haz clic en el botón "+" en la esquina superior derecha
3. Selecciona "New repository"
4. Llena los campos:
   - **Repository name**: `alegra-mx-bills-normalizer`
   - **Description**: "Sistema automatizado para la normalización y carga de facturas mexicanas al sistema Alegra"
   - **Visibility**: Selecciona "Private" si contiene información sensible de la empresa
   - **NO** marques "Initialize this repository with a README" (ya tenemos uno)

### 8. Conectar tu repositorio local con GitHub

Una vez creado el repositorio en GitHub, ejecuta:

```bash
# Agrega el remote
git remote add origin https://github.com/TU_USUARIO/alegra-mx-bills-normalizer.git

# O si usas SSH:
git remote add origin git@github.com:TU_USUARIO/alegra-mx-bills-normalizer.git

# Verifica que se agregó correctamente
git remote -v
```

### 9. Subir el código a GitHub

```bash
# Para la rama principal (main):
git branch -M main
git push -u origin main
```

### 10. Verificación final

1. Ve a tu repositorio en GitHub
2. Verifica que todos los archivos estén presentes
3. **IMPORTANTE**: Verifica que `config.json` **NO** esté en el repositorio
4. Lee el README.md en GitHub para asegurarte de que se vea correctamente

## 🔒 Seguridad

### ⚠️ Si accidentalmente subes archivos sensibles:

Si por error subes `config.json` u otro archivo con credenciales:

1. **ROTAR INMEDIATAMENTE** todas las credenciales expuestas
2. Remover el archivo del historial de Git:

```bash
# Remover archivo del historial
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch config.json" \
  --prune-empty --tag-name-filter cat -- --all

# Forzar push (¡CUIDADO!)
git push origin --force --all
```

3. Considera usar herramientas como [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/) para limpiar el historial

## 📝 Comandos útiles post-setup

### Agregar cambios futuros
```bash
git add .
git commit -m "Descripción del cambio"
git push
```

### Ver el estado actual
```bash
git status
```

### Ver el historial de commits
```bash
git log --oneline
```

### Crear una nueva rama
```bash
git checkout -b nombre-de-rama
```

### Cambiar entre ramas
```bash
git checkout main
git checkout nombre-de-rama
```

## 🎯 Checklist final

Antes de hacer push, verifica:

- [ ] `.gitignore` está configurado correctamente
- [ ] `config.json` **NO** está en el repositorio
- [ ] `config.example.json` **SÍ** está en el repositorio
- [ ] README.md está completo y claro
- [ ] `requirements.txt` incluye todas las dependencias
- [ ] No hay datos sensibles en el código
- [ ] No hay archivos Excel o XML de datos reales
- [ ] El repositorio es privado (si contiene lógica de negocio sensible)

## 📚 Recursos adicionales

- [Git Documentation](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)
- [Removing sensitive data from a repository](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)

---

¡Listo! Tu repositorio está preparado para trabajar en equipo. 🎉
