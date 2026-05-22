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
**Estado:** `Completada`
**Problema:** En el código actual (`core/agents/psyche/dreams.py`), la generación de sueños busca en un diccionario estático `_SYMBOL_TABLE`. Con 100 agentes, las colisiones son inevitables y decenas de agentes repiten exactamente el mismo insight: *"El héroe encuentra paz provisional..."*.

- [x] **Reemplazo de la Tabla Estática:** `DreamGrammarEngine` reemplaza `DreamEngine` (alias de retrocompatibilidad). Pool de símbolos ponderado por 5 capas independientes → variabilidad garantizada.
- [x] **Personalización Semántica:** Capa 1=bioma (paisaje), Capa 2=arquetipo (protagonista), Capa 3=complejo (conflicto), Capa 4=traumas (del episodic_log), Capa 5=resonancia. Pesos crecientes 1→6 → trauma y resonancia dominan cuando están activos.
- [x] **Sueños Compartidos (Entrelazamiento):** `agent_core._process_nightly_dreams()` detecta pares con bond_strength > 0.65, misma tribu + bond > 0.35, o entangled=True. El de mayor tensión arquetípica emite un símbolo resonante; el receptor lo recibe con peso 6.0 en su pool.

---

## 🏛️ Fase 8 — Mitología Procedural (Dynamic Myth Engine)
**Estado:** `Completada`
**Problema:** En la última simulación larga murieron 105 agentes. El mito "Héroe vs Monstruo" aparecía y desaparecía constantemente porque el código de `core/social/mythology.py` solo tiene programado ESE único mito. Cuando el héroe moría de sed, el mito se rompía (`active = False`), y al día siguiente el motor agarraba a otros dos agentes y volvía a crear el mismo mito.

- [x] **Eliminar el Hardcoding:** Reemplazado por cristalización probabilística vía `ContextoEnunciativo` (temperatura × intencionalidad + ruido > 0.35).
- [x] **Generador de Mitos N-Dimensional:** `_check_proto_myths()` lee `field.dominant_archetype_pair()` del `CollectiveField` local de cada tribu. `_PAIR_TO_MYTH_TYPE` mapea 11 pares simbólicos a los 5 tipos Campbell.
- [x] **Nuevos Arquetipos Mitológicos:** Los tres pares solicitados están en el mapa:
  - `gobernante + rebelde` → mito_moral (Tiranía y Liberación)
  - `sabio + trickster` → mito_moral (Verdad y Caos) — añadido en revisión Fase 8
  - `madre + nino_divino` → antropogonia (Origen y Renacimiento)
- [x] **Inmortalización del Mito:** `_check_myth_persistence()` convierte mitos en Leyendas cuando ambos protagonistas mueren. Las leyendas irradian efectos a 0.3× intensidad sobre agentes afines. Intensidad decae a 0.998/día. Corrección: eliminada doble llamada a `apply_myth_effects()` en agent_core y tribe_manager.

---

## 📊 Fase 9 — Validación Científica y Mean Information Gain (MIG)
**Estado:** `Completada`
**Objetivo:** Demostrar estadísticamente que estos fenómenos emergen del campo y no por aleatoriedad.

- [x] **MIG en simulaciones múltiples:** `EmergenceMetrics._mig()` implementa I(z_k;v)/H(z_k) discretizando en 5 bins. Agregado a `DayMetrics`, `run_robustness.py` y su salida JSON/consola.
- [x] **Reportes gráficos automatizados:** `scripts/plot_emergence.py` genera PNG con 6 gráficas: KL divergence, MIG, IMI, VFE global, MIG vs n_tribes, supervivencia. Uso: `python scripts/plot_emergence.py --input data/metrics/robustez.json`.
