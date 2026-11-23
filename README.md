# OSS Pulse

**Open Source Maintenance Intelligence**

OSS Pulse analiza repositorios públicos de GitHub para ayudar a sus mantenedores a entender su salud técnica y comunitaria, identificar trabajo que necesita atención y priorizar acciones. El objetivo del MVP es producir un informe explicable y compartible, con evidencia y cobertura visibles.

> Understand the health of your open source project. Discover what needs attention. Keep your community thriving.

Proyecto independiente, no afiliado oficialmente a GitHub ni a OpenSSF.

## Estado

Fase 1 en desarrollo. La CLI y `POST /api/v1/analyze` ya pueden obtener datos públicos y generar un informe JSON inicial. La web conecta con la API y muestra el informe. Se marca como insuficiente la cobertura inferior al 50 %; las dimensiones sin datos completos quedan como no evaluables. La API conserva informes en memoria temporal, todavía no en PostgreSQL.

## Stack

- `backend/`: Python, FastAPI y CLI sobre el mismo núcleo.
- `apps/web/`: Next.js y TypeScript.
- PostgreSQL para snapshots en la fase de persistencia.
- GitHub REST API detrás de un cliente centralizado.

Consulta [arquitectura](docs/architecture.md), [metodología de scoring](docs/scoring-methodology.md), [API](docs/api.md) y [roadmap](docs/roadmap.md).

## Requisitos

Python 3.11+, Node.js 20.9+ y npm. Docker Desktop solo para PostgreSQL local.

## Desarrollo local

Backend (PowerShell):
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
uvicorn app.main:app --app-dir backend --reload
```
API: `http://127.0.0.1:8000`; documentación: `/docs`.

Análisis desde terminal:
```powershell
oss-pulse https://github.com/owner/repository --output report.json
```
También puedes ejecutar `python -m app.cli https://github.com/owner/repository` desde la raíz. Los repositorios públicos funcionan sin conectar una cuenta. Para aumentar el límite de GitHub, copia `.env.example` a `.env` y añade `GITHUB_TOKEN` con acceso de solo lectura a repositorios públicos; mantenlo privado.

Web (en `apps/web`):
```powershell
npm install
npm run dev
```
Abrir `http://localhost:3000`.

PostgreSQL: copia `.env.example` a `.env` y ejecuta `docker compose up -d postgres`.

## Principios

- Scoring transparente, versionado y con cobertura explícita.
- Ausencia de datos no equivale a cero.
- Reglas deterministas con evidencia.
- No ejecutar código de repositorios analizados.
- Sin cuentas ni tokens personales en el MVP. El token de servidor es opcional y privado.
- Fechas en UTC; analizadores independientes de red, base de datos e interfaz.

Lee [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) y [SECURITY.md](SECURITY.md). Licencia MIT: [LICENSE](LICENSE).
