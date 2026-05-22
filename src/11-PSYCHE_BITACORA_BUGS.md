# Bitácora de Bugs y Soluciones

Este documento sirve como registro histórico de los bugs más crípticos y complejos encontrados durante el desarrollo de **PSYCHE SIMULACRA**, junto con su análisis y resolución. Esto permite mantener un entendimiento claro de cómo interactúan las capas biológicas, psicológicas y del entorno.

---

## Bug #001: El Éxodo hacia el Vacío (Inanición Masiva)

**Síntoma:**
Al correr simulaciones largas (ej. 1000 días simulados), invariablemente todos los agentes terminaban muriendo por inanición o deshidratación, sin importar la abundancia inicial de recursos en su zona de origen.

**Análisis:**
El error no residía en la tasa de regeneración de recursos ni en las rutinas de alimentación, sino en la **Mecánica de Exploración (`_explore_action`)**.
1. Cuando un agente no encuentra recursos en su hexágono actual (porque los ha agotado temporalmente o porque es un bioma árido), la supervivencia sobreescribe su rutina y lo obliga a explorar (`_find_food_action` hace fallback a `_explore_action`).
2. La función `_explore_action` elegía una dirección aleatoria y actualizaba `self.posicion = target`.
3. **El problema:** No existía validación de los límites del mapa (una grilla estática de 80x60). Con el tiempo, la caminata aleatoria llevaba a los agentes a superar el borde (`q < 0`, `q >= 80`, `r < 0`, `r >= 60`).
4. Al salir del mapa, el agente entraba en coordenadas donde `TerrainGrid` no tenía celdas y `WorldCore` no generaba recursos. Al no haber recursos en el vacío, el agente volvía a explorar eternamente, adentrándose más en la nada hasta morir.

**Solución:**
Se implementó un `bounds checking` (validación de límites) en `_explore_action` dentro de `core/agents/agent.py`. Ahora, antes de elegir una dirección, el agente filtra las opciones inválidas. Si se encuentra en un borde, solo seleccionará direcciones que lo devuelvan hacia el interior de la isla (la grilla válida).

**Impacto:**
Los agentes ahora permanecen confinados al entorno simulado. Cuando agotan los recursos en el borde, se ven obligados a regresar hacia zonas previamente exploradas o a competir por el espacio, lo que reactiva la dinámica social y frena las muertes ilógicas por inanición, permitiendo a la simulación avanzar años sin colapsar por este motivo geométrico.

---

## Bug #002: El Letargo Sediento (Desbalance Metabólico)

**Síntoma:**
Aún tras solucionar el éxodo al vacío (Bug #001), simulaciones largas mostraban una extinción total cerca del día 100. Todos los agentes morían de `deshidratacion` y algunos de `inanicion`.

**Análisis:**
El análisis numérico del metabolismo en `core/agents/needs.py` y `core/agents/agent.py` reveló dos problemas fatales:
1. **Rendimiento de Recursos Mínimo:** La acción de beber agua consumía 1 hora (1 tick), pero el agua recolectada (`0.20` unidades) multiplicada por `_AGUA_POR_BEBER` (`0.60`) apenas saciaba un `12%` de la sed. Dado que la sed aumentaba `68%` por día, el agente requería agotar múltiples hexágonos enteros diariamente solo para sobrevivir, deforestando la isla de agua virtualmente al instante.
2. **Fatiga Acumulativa (Letargo):** El decaimiento de fatiga al dormir (`0.045` por tick) era insuficiente para compensar la fatiga ganada despiertos (`0.035` por tick). En 4 días, la fatiga superaba el umbral crítico de supervivencia (`0.80`). Al intentar resolver la fatiga, el agente "descansaba" en lugar de beber agua. Al permanecer despierto, la fatiga seguía aumentando y la sed se volvía mortal.

**Solución:**
1. Se ajustó `_FATIGA_RECOVER_SLEEP` en `needs.py` a `0.075` para que 8 horas de sueño restauren por completo el cansancio de 16 horas de actividad.
2. Se reajustaron drásticamente los factores de conversión metabólicos en `agent.py`: `_COMIDA_POR_RECOLECTA = 4.0`, `_COMIDA_POR_CAZA = 8.0` y `_AGUA_POR_BEBER = 5.0`.

**Impacto:**
Ahora una recolección exitosa de agua o comida sacia la necesidad en un 80-100%, permitiendo al agente hidratarse/alimentarse rápidamente y destinar el resto de sus horas del día a socializar, explorar o mantener el fuego, habilitando la verdadera emergencia social y permitiendo la supervivencia más allá de cientos de días.

---

## Bug #003: Colisión Hídrica Inicial (Muertes en Cluster — Días 10–27 y 200–700)

**Síntoma:**
En la Simulación 02 (8 horas, 27.675 días simulados), 69 de 105 muertes (65.7%) fueron por deshidratación. El primer cluster ocurrió entre los días 10–27 (10 muertos en el primer mes) y el segundo entre los días 200–700 (~40 muertos). El motor reportaba resource_pressure promedio de 0.038 — el mundo tenía agua más que suficiente.

**Análisis:**
Se identificaron tres causas compuestas que actuaban simultáneamente:

1. **Búsqueda de agua ciega al hex actual** (`core/agents/agent.py`, `_find_water_action()`):
   La función solo verificaba recursos en el hexágono en el que el agente ya estaba parado. Si no había agua allí (threshold `> 0.1`), el fallback era `_explore_action()`, que movía al agente a un hex vecino **sin intentar beber en ese nuevo hex hasta el siguiente tick**. El agente gastaba ticks moviéndose en lugar de beber.

2. **Competencia masiva por el mismo hex de agua** (`data/seeds/initial_personas.yaml`):
   Los 100 agentes fundadores inician todos en el mismo hex `[40, 30]`. Ese bioma tiene `agua_lluvia` capeada en `0.60`. Con 100 agentes compitiendo simultáneamente, solo ~3 podían beber por tick. El resto acumulaba sed sin posibilidad de saciarla.

3. **Schedule infra-dotado para agua** (`core/agents/schedule.py`):
   El schedule default asignaba **solo 1 hora/día** (hora 6) a `buscar_agua`, contra 8 horas para `buscar_alimento`. La sed acumula ~0.68/día; con 1 hora efectiva de búsqueda y competencia por recursos, el balance era insostenible para la mayoría.

El cluster secundario (días 200–700) se explica por el mismo bug amplificado por el modificador estacional: en invierno la regeneración de agua baja a 20% (`_REGEN_MOD["invierno"] = 0.20`), haciendo que los hexes habituales queden secos y los agentes no logren encontrar agua en radio inmediato.

**Solución:**
1. `_find_water_action()` ampliada para buscar agua en los **6 hexágonos vecinos** si el hex actual está seco, moviéndose directamente al primero con agua disponible en lugar de explorar aleatoriamente.
2. Schedule default ajustado: se agrega hora 7 como segunda hora de `buscar_agua` (total: 2 horas/día para agua, manteniendo 7 para alimento).

**Impacto:**
Los agentes con sed crítica ahora tienen un radio de búsqueda activa de agua en lugar de quedarse varados en hexes secos. El cluster de días 10–27 debería desaparecer (la competencia por el hex inicial se resuelve porque los agentes se dispersan hacia hexes vecinos con agua). El cluster de invierno debería atenuarse significativamente.
