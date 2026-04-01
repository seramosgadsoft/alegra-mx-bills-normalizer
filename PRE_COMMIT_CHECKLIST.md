# ✅ Checklist Pre-Commit

Usa este checklist antes de hacer tu primer push a GitHub.

## 📋 Verificación de Archivos

### ✅ Archivos que DEBEN estar en el repositorio:
- [ ] `.gitignore` - creado y configurado
- [ ] `.editorconfig` - configuración de editor
- [ ] `README.md` - documentación completa
- [ ] `SETUP_GIT.md` - guía de inicialización
- [ ] `CONTRIBUTING.md` - guía de contribución  
- [ ] `CHANGELOG.md` - historial de cambios
- [ ] `COMMANDS.md` - referencia rápida de comandos
- [ ] `LICENSE` - licencia del proyecto
- [ ] `requirements.txt` - dependencias Python
- [ ] `config.example.json` - plantilla de configuración
- [ ] `main.py` - punto de entrada
- [ ] Directorio `core/` con todos los módulos
- [ ] Directorio `models/` con modelos de datos
- [ ] Directorio `services/` con servicios
- [ ] Directorio `utils/` con utilidades
- [ ] Archivos de soporte: `test_components.py`, `inspect_excel.py`, etc.

### ❌ Archivos que NO deben estar (verificar .gitignore):
- [ ] `config.json` - ⚠️ CONTIENE CREDENCIALES
- [ ] `config_qa.json` - ⚠️ CONTIENE CREDENCIALES  
- [ ] `token.pickle` - credenciales OAuth
- [ ] `*.log` - archivos de log
- [ ] `mexico_normalization.log`
- [ ] `venv/` - entorno virtual
- [ ] `__pycache__/` - cache de Python
- [ ] `bills/` - archivos XML de facturas
- [ ] `reports/` - reportes generados
- [ ] `*.xlsx` - archivos de datos Excel
- [ ] `DRIVERS.xlsx`
- [ ] `NIVELACION CHAZKI MX.xlsx`
- [ ] `uuids.txt` - lista de UUIDs

## 🔍 Comandos de Verificación

```bash
# 1. Ver qué archivos serán incluidos en el commit
git status

# 2. Revisar archivos ignorados (NO deben aparecer en git status)
git status --ignored | grep -E "config.json|uuids.txt|bills/|reports/"

# 3. Verificar que .gitignore funciona
git check-ignore config.json  # Debe mostrar: config.json
git check-ignore bills/        # Debe mostrar: bills/

# 4. Ver diferencias de archivos nuevos
git diff --cached

# 5. Simular commit (sin hacerlo realmente)
git commit --dry-run
```

## 🔒 Verificación de Seguridad

### Buscar credenciales accidentales:
```bash
# Buscar posibles passwords en archivos rastreados
git grep -i "password" -- '*.py' '*.json' '*.md'

# Buscar API keys
git grep -i "api_key\|apikey" -- '*.py' '*.json' '*.md'

# Buscar tokens
git grep -i "token\|secret" -- '*.py' '*.json' '*.md'
```

**Resultado esperado**: Solo deben aparecer referencias a `config.example.json` o en comentarios/documentación, NUNCA valores reales.

## 📝 Pre-Commit Final

```bash
# 1. Asegúrate de estar en la rama correcta
git branch  # Debería mostrar * main

# 2. Ver resumen de cambios
git status

# 3. Agregar archivos (si no lo has hecho)
git add .

# 4. Ver qué será incluido en el commit
git diff --cached --name-status

# 5. Verificar archivos staged
git ls-files --cached

# 6. Crear commit
git commit -m "Initial commit: Alegra MX Bills Normalizer

- Sistema de normalización de facturas mexicanas
- Integración con API de Alegra
- Soporte para procesamiento desde Excel, XML y lista de UUIDs
- Generación de reportes en JSON, CSV y HTML
- Gestión de proveedores
- Documentación completa"

# 7. Verificar commit local
git log --oneline -1

# 8. Ver archivos en el commit
git show --name-only HEAD
```

## 🚀 Push a GitHub

```bash
# 1. Verificar remote
git remote -v

# Si no tienes remote configurado:
# git remote add origin https://github.com/TU_USUARIO/alegra-mx-bills-normalizer.git

# 2. Asegurar que estás en main
git branch -M main

# 3. Push
git push -u origin main

# 4. Verificar en GitHub que todo se subió correctamente
# Ir a: https://github.com/TU_USUARIO/alegra-mx-bills-normalizer
```

## ⚠️ Si encuentras problemas

### Problema: `config.json` está en git status
**Solución:**
```bash
# Remover del staging area (NO borra el archivo)
git rm --cached config.json
git commit -m "Remove config.json from git tracking"
```

### Problema: Archivos grandes (.xlsx) ya están staged
**Solución:**
```bash
# Remover del staging
git rm --cached "NIVELACION CHAZKI MX.xlsx"
git rm --cached "DRIVERS.xlsx"
git rm --cached -r bills/
git rm --cached -r reports/
git commit -m "Remove data files from git tracking"
```

### Problema: Ya hice push con archivos sensibles
**Solución URGENTE:**
1. Rotar TODAS las credenciales inmediatamente
2. Usar `git filter-branch` o BFG Repo-Cleaner para limpiar historial
3. Ver `SETUP_GIT.md` para instrucciones detalladas

## ✅ Verificación Post-Push

Después de hacer push, verifica en GitHub:

1. [ ] El README.md se ve correctamente
2. [ ] `config.json` NO está en el repositorio
3. [ ] No hay archivos `.xlsx` de datos
4. [ ] No hay archivos en `bills/` o `reports/`
5. [ ] El archivo `config.example.json` SÍ está presente
6. [ ] Todos los archivos Python están presentes
7. [ ] Los directorios `core/`, `models/`, `services/`, `utils/` están completos

## 🎉 ¡Listo!

Si todos los checks están ✅, tu repositorio está listo para:
- Compartir con otros desarrolladores
- Colaborar en equipo
- Implementar CI/CD
- Desplegar en producción

---

**Última revisión**: Antes de cada push importante, revisa este checklist.
