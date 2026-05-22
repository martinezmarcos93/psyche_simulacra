# 🗺️ PSYCHE SIMULACRA: ROADMAP v2.0

Este roadmap se ha actualizado tras el exitoso test de estrés de 8 horas con 100 agentes. El motor de físicas, tribus y cultura material funciona perfectamente, pero la escala masiva reveló cuellos de botella semánticos en la capa narrativa y mitológica que deben resolverse.

---

## 🎯 Fase 6 — Integración de Inferencia Local (Ollama)
**Estado:** `Completada`
**Objetivo:** Autonomía total del motor de inferencia narrativa sin depender de APIs externas, garantizando que el entorno corra de forma local y gratuita.

- [x] **Daemon de Ollama:** `core/narrative/daemon.py` — `OllamaDaemon().setup()` invocado automáticamente al inicio de `run_simulation.py` y `visualizer.py`. Arranca `ollama serve` como proceso desacoplado si el puerto 11434 no responde.
- [x] **Gestor de Modelos:** `ensure_model()` verifica vía `/api/tags` si el modelo configurado está instalado; ejecuta `ollama pull` si falta.
- [x] **Llamadas Asíncronas:** Ya implementado en `NarratorEngine` (Fase 3): `queue.Queue` + hilo de fondo `NarratorWorker` — el `SimulationClock` no se bloquea.

---

## 🧠 Fase 7 — Motor de Sueños Generativos
**Estado:** `Pendiente`
**Problema:** En el código actual (`core/agents/psyche/dreams.py`), la generación de sueños busca en un diccionario estático `_SYMBOL_TABLE`. Con 100 agentes, las colisiones son inevitables y decenas de agentes repiten exactamente el mismo insight: *"El héroe encuentra paz provisional..."*.

- [ ] **Reemplazo de la Tabla Estática:** Eliminar `_SYMBOL_TABLE` y crear una clase `DreamGrammarEngine` o conectarlo al LLM (Ollama).
- [ ] **Personalización Semántica:** El sueño debe construirse tomando en cuenta el bioma del agente, sus traumas pasados (memoria episódica de encuentros con otros agentes) y sus complejos.
- [ ] **Sueños Compartidos (Entrelazamiento):** Crear una regla donde solo los agentes de la misma Tribu o fuertemente "entrelazados" (bond_strength cuántico alto) puedan experimentar sincronicidad (soñar con símbolos casi idénticos la misma noche).

---

## 🏛️ Fase 8 — Mitología Procedural (Dynamic Myth Engine)
**Estado:** `Pendiente`
**Problema:** En la última simulación larga murieron 105 agentes. El mito "Héroe vs Monstruo" aparecía y desaparecía constantemente porque el código de `core/social/mythology.py` solo tiene programado ESE único mito. Cuando el héroe moría de sed, el mito se rompía (`active = False`), y al día siguiente el motor agarraba a otros dos agentes y volvía a crear el mismo mito.

- [ ] **Eliminar el Hardcoding:** Quitar el `if field.symbols.get("heroe") > 0.75 and field.symbols.get("sombra") > 0.65`.
- [ ] **Generador de Mitos N-Dimensional:** El motor debe mirar el `CollectiveField` local de la tribu y encontrar el par de arquetipos con mayor carga. 
- [ ] **Nuevos Arquetipos Mitológicos:**
  - `Gobernante vs Rebelde` → El Mito de la Tiranía y la Liberación.
  - `Sabio vs Trickster` → El Mito de la Verdad y el Caos.
  - `Madre vs Niño Divino` → El Mito del Origen y el Renacimiento.
- [ ] **Inmortalización del Mito:** Si los agentes protagonistas del mito mueren, el mito NO debe caducar inmediatamente. Se convierte en una "Leyenda" de la tribu que persiste y sigue dando bonificaciones a los seguidores de ese arquetipo, pasando a formar parte de la Cultura Material y Oral de la tribu.

---

## 📊 Fase 9 — Validación Científica y Mean Information Gain (MIG)
**Estado:** `En Progreso` (Script: `run_robustness.py`)
**Objetivo:** Demostrar estadísticamente que estos fenómenos emergen del campo y no por aleatoriedad.

- [ ] Analizar las divergencias usando la métrica MIG en simulaciones múltiples.
- [ ] Automatizar reportes gráficos para publicar los resultados.
