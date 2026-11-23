# API v1

Base: `/api/v1`. El endpoint de análisis está disponible; los endpoints de historial quedan para la fase de persistencia.

| Método | Ruta | Propósito |
|---|---|---|
| GET | `/health` | Disponibilidad |
| POST | `/analyze` | Analizar URL GitHub |
| GET | `/repositories/{owner}/{repo}` | Último informe |
| GET | `/repositories/{owner}/{repo}/findings` | Hallazgos |
| GET | `/repositories/{owner}/{repo}/insights` | Recomendaciones |
| GET | `/reports/{report_id}` | Informe por ID |

Los informes incluyen ID, estado, repositorio, score, cobertura, clasificación, fecha UTC, dimensiones, hallazgos, recomendaciones y versión de metodología. Contrato documentado con OpenAPI.

`POST /analyze` recibe `{ "repository_url": "https://github.com/owner/repo" }` y devuelve el informe JSON completo. No requiere autenticación para repositorios públicos. Si la cobertura es inferior al 50 %, la clasificación es `Insufficient Data`.

Errores previstos: `400` URL inválida, `404` inexistente/inaccesible, `422` incompatible, `429` rate limit, `502` error de GitHub, `503` indisponibilidad. No exponer respuestas crudas de GitHub al cliente.
