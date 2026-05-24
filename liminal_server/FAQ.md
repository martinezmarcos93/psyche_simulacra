# FAQ — LIMINAL ZONE

Preguntas frecuentes sobre el servidor de interconexión.

---

## General

**¿Qué es la Zona Liminal?**

Es un espacio hexagonal compartido donde agentes de distintas simulaciones PSYCHE SIMULACRA pueden encontrarse. No es una simulación en sí misma: no tiene recursos, clima, ni dinámicas propias. Es un escenario de tránsito — un espacio "entre mundos".

**¿Cuántas simulaciones pueden conectarse simultáneamente?**

No hay límite técnico en la versión actual. En la práctica, con dos PCs y port forwarding, funciona de forma estable. Para más nodos, se recomienda un VPS con IP fija.

**¿El servidor puede alterar mis agentes o mi simulación?**

No. El servidor solo recibe y redistribuye eventos. Cada simulación es soberana — el servidor no puede modificar el estado interno de ninguna simulación.

---

## Red y Conexión

**¿Cómo conecto dos PCs en casas distintas?**

1. El hosteador abre `python main.py` en la raíz de PSYCHE SIMULACRA → opción `[5]` para iniciar el servidor.
2. El hosteador abre el puerto 8765 (TCP) en su router con port forwarding hacia su IP local.
3. El que se conecta abre `python main.py` → opción `[7]` e ingresa la IP pública del hosteador.
4. Verificar que el firewall de Windows no bloquee el puerto 8765.

Alternativa manual si no se usa el launcher:
- Hosteador: `cd liminal_server && python main.py`
- Cliente: `python scripts/visualizer.py --liminal --liminal-host <IP_PUBLICA_HOSTEADOR>`

**¿Cómo sé si la conexión funcionó?**

En la ventana Pygame del servidor verás el nombre de la simulación conectada en el sidebar derecho. En PSYCHE SIMULACRA, el HUD mostrará "Liminal: CONECTADO".

**¿Qué pasa si una simulación se desconecta?**

Los agentes que estaban en la zona liminal quedan "flotando" hasta que el servidor los elimina por timeout (o cuando la sim se reconecta). El servidor tolera desconexiones — las demás simulaciones siguen funcionando.

**¿Se puede correr el servidor y la simulación en la misma PC?**

Sí. Para desarrollo y pruebas, todo corre en localhost. Desde `main.py`:
- Opción `[5]` inicia el servidor en una ventana nueva.
- Opción `[6]` conecta el visualizador a localhost:8765.

**¿Cuál es el orden correcto de ejecución?**

```
PC-A (hosteador)                    PC-B (cliente)
────────────────                    ──────────────
1. Correr simulación                1. Correr simulación
2. Iniciar servidor (opción 5)
3. Conectar visualizador (op. 6)    2. Conectar visualizador (op. 7)
                                       → ingresar IP de PC-A
```

El servidor **debe estar activo** antes de que alguien intente conectarse. Las simulaciones pueden estar corriendo antes, durante o después de que el servidor arranque — son independientes.

---

## Agentes y Portal

**¿Dónde aparece el portal hexagonal en el mapa?**

La posición se calcula a partir del seed de la simulación, así siempre está en el mismo lugar en cada sesión. Está ubicado a ~18 hexágonos del centro (zona de spawn), por lo que los agentes necesitan explorar para encontrarlo.

**¿Qué pasa cuando un agente entra al portal?**

1. El agente desaparece del mapa local de PSYCHE SIMULACRA.
2. Se envía un evento `agent_enter` al servidor con los datos psicológicos del agente.
3. El servidor asigna una posición en el mapa liminal y confirma con `agent_placed`.
4. El agente aparece en la ventana Pygame del servidor.
5. Todas las simulaciones conectadas reciben un broadcast `agent_arrived`.

**¿El agente puede volver a su simulación?**

No en la versión actual (Fase 3). El retorno está planificado para Fase 7.

**¿Los agentes en el liminal siguen envejeciendo, teniendo hambre, etc.?**

No. Al estar `in_liminal = True`, el AgentCore de PSYCHE SIMULACRA los salta completamente. Sus necesidades no se actualizan, no envejecen, no pueden morir. Es suspensión biológica total.

**¿Qué recursos tiene la Zona Liminal? ¿Pueden comer o beber los agentes ahí?**

Ninguno. La Zona Liminal no tiene agua, comida, fauna, clima ni ningún recurso. Los agentes en suspensión no los necesitan. El espacio tiene 5 biomas puramente visuales (`vacío`, `nebulosa`, `cristalino`, `sombra`, `aurora`) que dan identidad estética al mapa pero no producen ni consumen nada. Es un espacio de tránsito, no de supervivencia.

**¿Mis agentes y los de mi amigo pueden verse entre sí?**

En la ventana Pygame del servidor sí — aparecen como puntos con colores distintos según su simulación de origen. La interacción directa entre agentes de distintas sims está planificada para Fase 6.

---

## Técnico

**¿Qué versión de Python necesito?**

Python 3.11 o superior (compatible con PSYCHE SIMULACRA).

**¿El servidor necesita GPU?**

No. Pygame usa renderizado CPU. Para el servidor, cualquier máquina sirve.

**¿Qué pasa si la versión de protocolo no coincide?**

El servidor rechaza la conexión con un mensaje de error indicando el mismatch de versiones. Ambas partes deben usar la misma `PROTOCOL_VERSION` definida en `config.py`.

**¿El mapa liminal es igual para todos?**

Sí. El mapa liminal se genera con `WORLD_SEED = 0` (configurable en `config.py`). Todos los participantes ven el mismo mapa porque el servidor es la única fuente de verdad.

**¿Puedo cambiar el puerto?**

Sí, editando `SERVER_PORT` en `config.py` o usando `python main.py --port XXXX`.

---

## Futuro

**¿Qué sigue después de conectar las dos simulaciones?**

Ver el roadmap en `README.md`. El próximo hito es la transmisión de eventos simbólicos: un mito nacido en SIM A altera los sueños de los agentes en SIM B.

**¿Habrá alguna vez combate o guerra entre civilizaciones?**

Está en el roadmap (Fase futura), pero no es prioritario. La filosofía del proyecto prioriza resonancia cultural sobre conflicto físico.
