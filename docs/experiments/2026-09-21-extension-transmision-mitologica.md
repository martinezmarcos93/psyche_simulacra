# Extensión de `on_social_transmission` a más tipos de encuentro — resultado y hallazgo de ritmo

**Fecha:** 2026-09-21
**Contexto:** ítem "Prioridad media" del handoff `docs/handoffs/2026-09-21.md` §7 —
extender la conexión de `MythologyEngine.on_social_transmission()` (ver
`docs/experiments/2026-09-21-fase1-ecuacion-personal.md` §4 del handoff para el
bug original) a `conflicto_explotacion` y `cooperacion_pura`, además del
`choque_violento` ya conectado.

## Cambio implementado

`core/social/interaction.py::resolve_encounter()` ahora llama a
`mythology_engine.on_social_transmission(collective_field)` en las tres ramas
más intensas del motor de encuentros:

- `choque_violento` (competencia-competencia) — ya conectado en la sesión anterior.
- `conflicto_explotacion` (cooperación vs. competencia) — nuevo.
- `cooperacion_pura` (cooperación-cooperación) — nuevo.

No se tocó `manipulacion` (ambigua moralmente, no mencionada en el pending item).

Tests de regresión: `tests/test_social.py::test_cooperacion_pura_transmite_al_proto_mito`
y `::test_conflicto_explotacion_transmite_al_proto_mito`.

## Hallazgo: el ritmo ya estaba roto antes de este cambio

Se midió el ritmo de cristalización con `scripts/diag_mythology_pace.py`
(headless, semilla 42, `rich_culture_100.yaml`, 300 días), comparando la línea
base (solo `choque_violento`, el fix de la sesión anterior tal como quedó en
`main`) contra la extensión de hoy (los tres tipos):

| Configuración | Primer mito cristalizado | Mitos cristalizados a día 300 | Proto-mitos activos a día 300 |
|---|---|---|---|
| Solo `choque_violento` | día 2 | 3 | 0 |
| + `conflicto_explotacion` + `cooperacion_pura` | día 2 | 3 | 0 |

**La extensión de hoy no produjo ninguna diferencia medible.** Ambas
configuraciones saturan casi instantáneamente: 3 mitos cristalizados para el
día 2, y ningún proto-mito nuevo se forma después de eso en toda la ventana de
300 días observada.

Esto revela que la hipótesis original del pending item — "pocos tipos de
encuentro alimentando la transmisión" — no era la causa del problema real.
Incluso con un solo tipo de encuentro conectado, el ritmo de cristalización ya
es **~30-60x más rápido** que el objetivo del Roadmap 7 (3000-6000 días → ≥3
mitos/leyendas): llega al mismo número objetivo en 2 días en vez de miles. El
techo de "3" no es un límite de variedad de pares arquetípicos disponibles
(hay ~20 combinaciones posibles en `_PAIR_TO_MYTH_TYPE`), sino que después del
estallido inicial de presión mítica del campo, `contexto_enunciativo().probabilidad_cristalizacion()`
deja de superar `_PROTO_MYTH_THRESHOLD` (0.25) — no nacen más proto-mitos, sin
importar cuántas transmisiones ocurran, porque no hay proto-mitos a los que
transmitir.

## Decisión

Consultado el usuario sobre cómo calibrar (subir umbrales, revertir la
extensión, o dejarlo así y seguir con otros pendientes): se decidió **dejar el
cambio de hoy aplicado tal cual** (más variedad de causas no hace daño, aunque
tampoco resolvió el problema de ritmo) y **no calibrar las constantes ahora**
— queda como trabajo pendiente explícito para una sesión futura dedicada.

## Pendiente para una sesión futura

- Recalibrar `_COHERENCE_TO_CRYSTALLIZE` / `_COHERENCE_PER_TRANSMISSION`
  (`core/social/mythology.py`) y/o `_PROTO_MYTH_THRESHOLD` para acercar el
  ritmo a la escala de miles de días del Roadmap 7 original, en vez de
  decenas. Requiere decidir primero qué ritmo narrativo se desea (esto es una
  decisión de diseño/contenido, no solo técnica).
- Investigar por qué no se forman nuevos proto-mitos después del estallido
  inicial — puede ser un problema separado e independiente del ritmo de
  transmisión (la presión mítica del campo decae y no vuelve a acumularse lo
  suficiente, o el pool de agentes vivos cambia el `dominant_archetype_pair()`
  de forma que ya no genera contexto suficiente).
- `scripts/diag_mythology_pace.py` (nuevo, esta sesión) queda disponible para
  repetir esta medición contra cualquier recalibración futura.
