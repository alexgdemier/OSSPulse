# Arquitectura

## Flujo

```text
URL GitHub → validador → cliente GitHub → datos normalizados → analizadores
           → scoring + detecciones → recomendaciones → informe JSON / API → web
```

La primera entrega recorre el flujo desde terminal y devuelve JSON. API y web reutilizarán los mismos servicios. PostgreSQL conservará snapshots cuando llegue la persistencia.

## Límites

- `integrations/github`: llamadas, paginación, timeouts y errores GitHub.
- `schemas`: modelos normalizados, independientes de respuestas crudas.
- `analyzers`: métricas por dimensión, sin HTTP.
- `scoring`: dimensiones evaluables y cobertura, sin dependencias de API/DB/UI.
- `detection` e `insights`: reglas deterministas con evidencia y enlaces.
- `services`: orquestación y construcción de informes.
- `api/v1` y `cli`: adaptadores del núcleo a HTTP y terminal.
- `apps/web`: presentación, sin duplicar reglas.

## Decisiones

Monorepo; backend Python compartido por CLI y FastAPI. PostgreSQL local con Compose. Fechas UTC y versión metodológica en cada informe. Señales desconocidas no reciben cero. REST API primero; token de servidor opcional, nunca tokens personales de visitantes. No se ejecuta contenido del repositorio.

## Seguridad

Validar host/ruta GitHub y rechazar URLs arbitrarias o redirecciones a redes privadas. Centralizar límites, paginación, caché y rate limits. Limitar respuestas, no registrar secretos y escapar contenido en HTML.
