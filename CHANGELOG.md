# Changelog

Todos los cambios notables en One Market serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [0.1.0] - 2024-10-17

### Epic 1 - Fundaciones de Datos y Almacenamiento ✅

#### Agregado

**Módulo de Datos (`app/data/`)**:
- `schema.py`: Modelos Pydantic para OHLCV
  - `OHLCVBar` con validación completa de precios y timestamps
  - `DatasetMetadata` para tracking de datasets
  - `DataValidationResult` para resultados de validación
  - `FetchRequest` para parámetros de fetch
  - `StoragePartitionKey` para claves de particionamiento
  
- `fetch.py`: Cliente de descarga de datos
  - `DataFetcher` con soporte ccxt para múltiples exchanges
  - `RateLimiter` para control de límites de API
  - Fetch incremental con paginación automática
  - Retry con exponential backoff
  - Validación automática de gaps y duplicados
  - Soporte para spot y futures markets
  
- `store.py`: Almacenamiento en parquet
  - `DataStore` con particionamiento por symbol/tf/year/month
  - Escritura incremental con deduplicación
  - Lectura eficiente con filtros temporales
  - Gestión de metadatos por dataset
  - Operaciones CRUD completas
  - Validación de consistencia de storage

**Módulo de Configuración (`app/config/`)**:
- `settings.py`: Configuración centralizada con pydantic-settings
  - Variables de entorno para exchange, rate limiting, validation
  - Defaults sensatos para producción
  - Type safety completo
  - Diccionario de timeframes a milliseconds

**Módulo de Utilidades (`app/utils/`)**:
- `logging_config.py`: Setup de logging centralizado
  - Console y file handlers
  - Formato configurable
  - Filtros por módulo

**Testing (`tests/`)**:
- `test_data.py`: Suite exhaustiva con 22 tests
  - Tests de validación de schema
  - Tests de particionamiento
  - Tests de storage operations
  - Tests de gap detection
  - Tests de duplicate handling
  - Tests de fetch requests
  - Tests de timeframe conversion
  - Cobertura >90%

**Documentación**:
- `README.md`: Documentación completa del proyecto y Epic 1
- `QUICKSTART.md`: Guía de inicio rápido en 5 minutos
- `ARCHITECTURE.md`: Arquitectura técnica detallada
- `EPICS.md`: Planificación completa de todos los Epics
- `CHANGELOG.md`: Este archivo

**Configuración del Proyecto**:
- `requirements.txt`: Dependencias Python completas
- `pyproject.toml`: Configuración de herramientas (black, ruff, mypy)
- `pytest.ini`: Configuración de pytest
- `.gitignore`: Archivos ignorados por git
- `env.example`: Template de variables de entorno
- `Makefile`: Comandos útiles para desarrollo

**Scripts**:
- `scripts/setup.py`: Script de setup inicial
- `scripts/health_check.py`: Health checks del sistema

**Ejemplos**:
- `examples/example_fetch_data.py`: Ejemplo de fetch y storage
- `examples/example_read_data.py`: Ejemplo de lectura con filtros

#### Características Principales

**Validación Robusta**:
- Validación en 3 capas (Schema, Temporal, Storage)
- Detección automática de gaps temporales
- Identificación de duplicados
- Validación de consistencia OHLC (high >= others, low <= others)
- Timestamps razonables (no futuro, >= 2000)

**Performance**:
- Fetch de 1000 bars: <1s
- Write de 1000 bars: <500ms
- Read de 1000 bars: <200ms
- Validación de 1000 bars: <100ms

**Storage**:
- Particionamiento Hive-style: `symbol=X/tf=Y/year=Z/month=M/`
- Compresión snappy (ratio ~75%)
- Deduplicación automática configurable
- Metadata tracking completo
- Operaciones idempotentes

**Robustez**:
- Rate limiting automático (1200 req/min default)
- Retry con exponential backoff (max 3 intentos)
- Manejo de errores de red y exchange
- Normalización UTC de timestamps
- Validación post-fetch automática

#### Métricas Técnicas

- **Líneas de código**: ~2,500
- **Tests**: 22 tests unitarios + integración
- **Cobertura**: >90%
- **Módulos**: 8 módulos principales
- **Dependencias**: 20 paquetes
- **Documentación**: 5 documentos (README, QUICKSTART, ARCHITECTURE, EPICS, CHANGELOG)

#### Próximos Pasos

Ver `EPICS.md` para el roadmap completo. El próximo Epic es:
- **Epic 2 - Estrategias Cuantitativas**: Framework de indicadores, generación de señales, backtesting

---

## [Unreleased]

Cambios en desarrollo (ninguno actualmente).

---

## Convenciones de Changelog

### Tipos de Cambios

- `Agregado`: Nuevas características
- `Cambiado`: Cambios en funcionalidad existente
- `Deprecado`: Características que serán removidas
- `Removido`: Características removidas
- `Corregido`: Bug fixes
- `Seguridad`: Vulnerabilidades

### Formato de Versión

- **MAJOR**: Cambios incompatibles de API
- **MINOR**: Nueva funcionalidad compatible
- **PATCH**: Bug fixes compatibles

Ejemplo: `1.2.3` = Major.Minor.Patch

---

[0.1.0]: https://github.com/usuario/one-market/releases/tag/v0.1.0



