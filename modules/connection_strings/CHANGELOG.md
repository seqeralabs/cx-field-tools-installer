# Changelog
All notable changes to this module will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-09-30

### Added
- `platform_db_tls` input (bool, default `false`). When `true`, the MySQL 8.x JDBC suffix connects with TLS: `?useSSL=true&trustServerCertificate=true&permitMysqlScheme=true` (encrypted; the server certificate isn't verified). When `false`, the suffix is unchanged from 2.0.0, so existing callers get identical output. See the installer's Design Decision 25.

## [2.0.0] - 2026-06 (installer 1.8.0)

### Changed
- Callers resolve user-facing flags into mode strings (`platform_security_mode`, `platform_db_deployment`, `platform_redis_deployment`, `studio_mode`, `wave_mode`) before calling the module. Value generation is split into dispatch tables, mode resolution, and final URL composition. See the installer's 1.8.0 CHANGELOG. 1.0.0 was removed.

## [1.0.0] - 2025-June-16

### Added
- Initial release of the connection_strings module
- Support for generating Tower and Swell database connection strings
- Support for generating Tower, Connect, and Wave-Lite Redis connection strings
- Support for both container and external database/Redis configurations
- Comprehensive documentation in README.md
