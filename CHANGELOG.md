# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Por agregar
- Sistema de retry configurable
- Validación mejorada de datos de entrada
- Soporte para más tipos de comprobantes fiscales
- Dashboard de monitoreo de procesamiento

## [1.0.0] - 2026-04-01

### Agregado
- Sistema de normalización de facturas mexicanas
- Tres modos de procesamiento: TXT, Excel y Providers
- Integración con API de Alegra México
- Análisis automático de archivos XML (CFDI)
- Procesamiento desde hojas de cálculo Excel
- Gestión de proveedores
- Generación de reportes en múltiples formatos (JSON, CSV, HTML)
- Búsqueda inteligente de archivos XML por UUID
- Sistema de logging detallado
- Manejo robusto de errores
- Configuración centralizada
- Documentación completa

### Características técnicas
- Arquitectura modular organizada en core, services, models y utils
- Type hints para mejor mantenibilidad
- Manejo de reintentos con exponential backoff
- Validación de datos de entrada
- Soporte para procesamiento por lotes
- Configuración flexible por modo de operación

[Unreleased]: https://github.com/tu-usuario/alegra-mx-bills-normalizer/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/tu-usuario/alegra-mx-bills-normalizer/releases/tag/v1.0.0
