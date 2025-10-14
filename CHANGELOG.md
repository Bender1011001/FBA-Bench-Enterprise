# Changelog

All notable changes to FBA-Bench Enterprise will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Enhanced DB session lifecycle using `scoped_session` for thread-safety and `expire_on_commit=False`.
- Implemented canonical dependency exports from `api/dependencies.py` for standardized imports.
- Introduced a CI workflow in `.github/workflows/ci.yml` for automated testing and linting of Python backend and Node.js frontends.
- Added `.dockerignore` to exclude development artifacts and temporary files from Docker builds.
- Established baseline documentation: `SECURITY.md`, `CONTRIBUTING.md`, and `CHANGELOG.md`.
- Created `.env.example` to guide environment variable setup for development and deployment.

### Changed
- Strengthened database session management with `SessionLocal.remove()` in `get_db()`'s finally block.

### Fixed
- N/A

### Removed
- N/A

### Security
- Updated dependency management and CI checks to improve security posture.

### Deprecated
- N/A

### Breaking Changes
- N/A

---

## [1.0.0] - YYYY-MM-DD

*(This section would be populated with the first release version and date. For now, we are focusing on setting up the project for release.)*

### Added
- Initial release of FBA-Bench Enterprise.
- Core features for JWT authentication, SQLite stability improvements, and Pydantic v2 integration.
- Stripe compatibility for payment processing.
- Performance shims and optimizations.

### Changed
- N/A

### Fixed
- N/A

### Removed
- N/A

### Security
- N/A

### Deprecated
- N/A

### Breaking Changes
- N/A