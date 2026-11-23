# Metodología de scoring

## Principio

El Health Score resume señales observables; no certifica calidad ni mide popularidad. Cada informe incluye fecha, metodología, cobertura, dimensiones evaluables y evidencia. Lo desconocido es `not_evaluable`, nunca cero.

## Pesos

| Dimensión | Peso |
|---|---:|
| Maintenance | 30 % |
| Community | 25 % |
| Development | 20 % |
| Documentation | 15 % |
| Sustainability | 10 % |

Las dimensiones no calculables se omiten; pesos restantes se renormalizan para el score. `coverage` suma los pesos originales evaluables.

## Indicadores

- **Maintenance (30 %):** respuesta a PR (30 %), edad de PR abiertos (25 %), respuesta a issues (25 %), actividad de mantenimiento (20 %).
- **Community (25 %):** contribuidores externos activos (30 %), diversidad (25 %), nuevos participantes (25 %), interacción de mantenedores (20 %). Evitar penalizar automáticamente proyectos pequeños.
- **Development (20 %):** CI (25 %), tests detectables (30 %), configuración de desarrollo (20 %), workflows (25 %). Tests presentes no significa cobertura o éxito.
- **Documentation (15 %):** README (30 %), licencia (25 %), CONTRIBUTING (25 %), documentación adicional (20 %).
- **Sustainability (10 %):** concentración de contribuciones (40 %), tendencia de actividad (35 %), continuidad de releases (25 %). Interpretación conservadora.

## Detecciones iniciales

`PR001` sin actividad ≥30 días; `PR002` ≥60; `IS001` issue sin respuesta ≥14 días; `IS002` ≥30; `CM001` concentración elevada; `DV001` sin CI detectable; `DV002` sin tests detectables; `DC001` sin CONTRIBUTING; `DC002` sin licencia; `SU001` caída significativa de actividad; `SU002` ausencia reciente de releases (informativo). Excluir drafts, bloqueos y espera del autor de PR stale cuando sea posible. Umbrales centralizados.

Todo hallazgo guarda código, categoría, severidad, explicación, evidencia fechada, recomendación y URL de origen. No declarar abandono por una señal aislada.

Prioridad interna: `P = 0.50 I + 0.30 U + 0.20 C`, impacto, urgencia y confianza entre 0 y 100. No es el Health Score.

| Score | Clasificación |
|---:|---|
| 85–100 | Excellent |
| 70–84 | Healthy |
| 50–69 | Needs Attention |
| 30–49 | At Risk |
| 0–29 | Critical |

Bandas orientativas a calibrar. Los informes retienen versión del motor para mantener la interpretación histórica.

Un score con menos de 50 % de cobertura se clasifica como `Insufficient Data`; se conserva el valor ponderado para mostrar las señales disponibles, pero no se presenta como una clasificación fiable del proyecto.

## Señales en la primera versión del motor

En `0.1.0-alpha`, Maintenance usa edad mediana de PR abiertos, issues abiertos sin comentarios y fecha del último push. Community necesita PRs observados para calcular diversidad/participación. Development y Documentation se limitan a presencia detectable en el árbol del branch por defecto. Sustainability necesita datos completos de commits y una release publicada con fecha. Si la paginación se limita o el árbol de GitHub está truncado, la dimensión correspondiente no se incluye en score ni cobertura. Estas señales iniciales aún no implementan todos los indicadores y pesos internos descritos arriba.
