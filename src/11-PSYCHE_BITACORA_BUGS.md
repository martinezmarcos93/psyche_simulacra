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
