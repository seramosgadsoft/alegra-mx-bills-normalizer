# Contributing to Alegra MX Bills Normalizer

¡Gracias por tu interés en contribuir a este proyecto!

## 🔧 Configuración del entorno de desarrollo

1. Clona el repositorio
2. Crea un entorno virtual: `python3 -m venv venv`
3. Activa el entorno: `source venv/bin/activate`
4. Instala dependencias: `pip install -r requirements.txt`
5. Copia y configura: `cp config.example.json config.json`

## 📝 Guías de estilo

### Python
- Sigue PEP 8
- Usa type hints cuando sea posible
- Documenta funciones con docstrings
- Nombres de variables en español o inglés consistente por módulo
- Usa logging en lugar de print() para mensajes

### Git commits
- Mensajes en español o inglés (consistente con el proyecto)
- Formato: `tipo: descripción breve`
- Tipos: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

Ejemplo:
```
feat: agregar soporte para nuevos impuestos
fix: corregir cálculo de retenciones
docs: actualizar README con ejemplos
```

## 🧪 Testing

Ejecuta los tests antes de hacer commit:
```bash
python test_components.py
```

## 📋 Proceso de contribución

1. Crea una nueva rama: `git checkout -b feature/mi-nueva-caracteristica`
2. Haz tus cambios
3. Haz commit de tus cambios
4. Push a tu rama: `git push origin feature/mi-nueva-caracteristica`
5. Abre un Pull Request

## 🐛 Reportar bugs

Al reportar un bug, incluye:
- Descripción clara del problema
- Pasos para reproducir
- Comportamiento esperado vs comportamiento actual
- Logs relevantes
- Versión de Python y dependencias

## 💡 Sugerir mejoras

Las sugerencias son bienvenidas. Abre un issue describiendo:
- El problema que resuelve tu sugerencia
- Cómo propones implementarlo
- Alternativas consideradas

## ⚠️ Importante

- **NUNCA** incluyas credenciales reales en commits
- Verifica que `config.json` esté en `.gitignore`
- No incluyas datos sensibles en los tests
- Asegúrate de que tus cambios no rompan funcionalidad existente

## 📞 Contacto

Para preguntas o dudas, contacta al equipo de desarrollo.
