# Handoff — 2026-09-23 (reinterpretación del receptor en el ciclo comunicacional)

Rama `feature/comunicacion-reinterpretacion-receptor`, creada desde `main`
actualizado (`860d2be`, que ya incluye el merge de
`experiment/ab-fase1-mas-semillas` y `feature/mitologia-mas-encuentros`).

## 1. Origen: análisis de una propuesta externa, reconciliada con el diseño existente

La sesión partió de una propuesta de "ciclo comunicacional completo"
(emisor→mensaje→canal→receptor→feedback) generada por otra IA sin acceso al
repo. Analizada contra el código real, tenía dos problemas de fondo:

- Violaba el principio Capa A / Capa B del proyecto
  (`src/02-PSYCHE_ORIGEN_INCONSCIENTE.md`): proponía un `MessageVector` con
  contenido simbólico rico transmitido directamente, cuando el contrato del
  proyecto (`InterpretiveFilter`, Ecuación Personal Fase 1) es que el
  vocabulario simbólico **nunca se inventa por mensaje** — solo se toma
  prestado de lo que ya cristalizó en el campo colectivo.
- Ignoraba que `InteractionEngine.resolve_encounter` ya es, en los hechos,
  un ciclo comunicacional implícito (colapso cuántico → matriz de
  resolución → vínculos/campo/mitología como feedback).

Reconciliar con Saussure (langue/parole — el mensaje solo puede referenciar
vocabulario ya cristalizado, patrón `_borrow_frame`/`_borrow_cause` que
`InterpretiveFilter` ya aplica) y Voloshinov (multiacentualidad — el mismo
signo puede tener acentos evaluativos opuestos según quién lo mire) llevó a
un diseño mucho más chico: **extender lo que ya existe, no reemplazarlo.**

El punto que el usuario identificó como el más valioso — y el que se
implementó esta sesión — es que la reinterpretación del mensaje por parte
del receptor debe estar condicionada por su conocimiento, sus intereses y
sus inclinaciones. Eso ya es exactamente lo que `InterpretiveFilter` hace
para estímulos del entorno; faltaba aplicarlo a los encuentros sociales.

## 2. Qué se implementó

### 2.1 `core/social/communication.py` (nuevo módulo)

Traduce el **rol** que tuvo un agente en un encuentro (`explotado`,
`explotador`, `choque_violento`, `manipulado_exitosamente`,
`manipulador_exitoso`, `manipulador_fracasado`, `manipulacion_resistida`,
`cooperacion_mutua`, `juego_mental_mutuo`) a un `Stimulus` físico —
categorías y magnitudes (`threat`/`benefit`), sin contenido simbólico — y
deja que el `InterpretiveFilter` del receptor haga el resto. El vínculo
previo con el otro agente (`SocialNetwork.get_bond`) modula la carga social
del estímulo (los "intereses" del receptor).

`_ROLE_PHYSICS` está calibrado proporcionalmente a los efectos "objetivos"
que `resolve_encounter` ya aplica a cada rol en cada rama — por eso víctima
y explotador del **mismo** encuentro (`conflicto_explotacion`) reciben
físicas de polaridad opuesta: es lo que permite que la reinterpretación
diverja aunque el hecho resuelto sea el mismo.

Apagado por defecto (`COMM_REINTERPRETATION_ENABLED`), mismo patrón que
`_INTERPRETIVE_FILTER_ENABLED` en `agent.py` — cero efecto sobre corridas
existentes.

### 2.2 `Agent.perceive_social_event()` (`core/agents/agent.py`)

Factoriza el patrón que `decide_action`/`_decide_via_collapse` ya usaban
dos veces para estímulos del entorno (interpretar → guardar
`last_perceived_event` → acumular a `MentalVault` si existe), para que
`communication.py` no necesite tocar `_interpretive_filter` directamente.

### 2.3 Wiring en `InteractionEngine.resolve_encounter`

Las 6 ramas de la matriz 4×4 que sí producen un encuentro (todas menos
aislamiento) llaman a `_reinterpret_pair` al final, con los roles
correspondientes a cada agente.

`_local_context()` resuelve el campo/mitología de la **propia tribu** del
agente (vía `tribe_manager.get_local_field`/`local_myths`) en vez del
global compartido, cuando existe — con fallback al global si no hay
`tribe_manager` o el agente no tiene tribu asignada.

### 2.4 Reconocimiento de Héroe/Monstruo por tribu (multiacentualidad)

El chequeo que existía en `resolve_encounter` (líneas ~153-176 antes del
cambio) consultaba un único `mythology_engine` global para decidir si A o B
era reconocido como Héroe o Monstruo. Ahora cada agente consulta la
mitología de **su propia tribu** (misma resolución que `_local_context`) —
el mismo agente puede ser Héroe para una tribu y no tener estatus mítico
(o ser el Monstruo) para otra que cristalizó un mito distinto sobre el
mismo par arquetípico. Sin `tribe_manager`, el comportamiento es
idéntico al anterior (ambos agentes consultan la misma mitología global).

## 3. Tests

23 tests nuevos:
- `tests/test_communication.py` (9): contrato Capa A del módulo, físicas
  opuestas por rol, activación de complejos, divergencia entre psiques.
- `tests/test_social.py` (14): wiring en `resolve_encounter` con el flag
  activado/desactivado, divergencia víctima/explotador vía el motor real,
  `_local_context` (3), reconocimiento de héroe por tribu (2).

Suite completa corrida dos veces (antes y después del cambio de
héroe/monstruo): **463 passed, 2 skipped** (mismos que ya estaban skipped
antes de esta rama), **1 deselected** (`ZeroDivisionError` de
`SimulationClock`, ya documentado y arreglado en `0bd0432` sobre
`feature/ecuacion-personal-continuacion`, aún no mergeado a `main` — no es
una regresión de esta rama). Cero fallos, cero regresiones.

## 4. Deliberadamente fuera de alcance

- No se tocó el texto de `episodic_log` para reflejar la reinterpretación
  subjetiva (hoy sigue siendo el mismo texto fijo por rama). El
  `PerceivedEvent` queda disponible en `last_perceived_event` y alimenta
  `MentalVault`/`complexes.activos`, pero no se renderiza a narrativa
  todavía.
- No se activó el flag por defecto — sigue siendo un experimento opt-in,
  igual que la Ecuación Personal Fase 1. Activarlo en una corrida real y
  medir su efecto (divergencia intra-tribu, tasa de "malentendidos"
  víctima/explotador, etc.) es el paso lógico siguiente si se quiere
  validar empíricamente antes de proponerlo como default.
- No se agregó un mecanismo explícito de "ruido de canal" ni de
  "metamensaje" (mencionados en el análisis de la sesión anterior) — se
  priorizó la pieza que el usuario identificó como más valiosa.

## 5. Pendiente de otras ramas (no tocado acá, contexto para no repetir)

- `feature/ecuacion-personal-continuacion`: A/B n=15 y calibración de
  mitología, mencionados en el handoff `2026-09-21-continuacion.md`, no
  parecen haberse cerrado en esa rama todavía (no se investigó en esta
  sesión). El fix del `ZeroDivisionError` (`0bd0432`) tampoco está en
  `main` — considerar mergearlo cuando se cierre esa rama.
