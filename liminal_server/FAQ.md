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

**¿Cómo conecto dos PCs en casas distintas? (método recomendado: ngrok)**

ngrok crea un túnel TCP desde internet hasta tu puerto 8765 sin tocar el router. Es la forma más simple de conectar dos PCs en redes distintas.

**Instalación de ngrok (solo PC-A, una vez):**
1. Crear cuenta gratuita en [https://ngrok.com](https://ngrok.com)
2. Descargar el ejecutable para tu sistema operativo
3. En Windows: descomprimir y poner `ngrok.exe` en una carpeta del PATH (ej: `C:\Windows\System32`) — o agregar la carpeta donde está al PATH del sistema
4. Autenticar: `ngrok authtoken <tu-token>` (el token aparece en el dashboard de ngrok al loguearte)

**Uso (flujo completo):**

**PC-A (hosteador):**
1. `python main.py` → abrir el Observatorio NiceGUI → **Nueva simulación** o **Continuar**.
2. Antes de iniciar, marcar **Zona Liminal** en el launcher, dejar Host en `localhost`.
3. Al iniciar, el servidor arranca en background y el tab **Liminal** aparece en el Observatorio.
4. Obtener la IP local (ej: `192.168.1.10`) y compartirla junto con el puerto `8765`.
   Con ngrok: `ngrok tcp 8765` → compartir el host y puerto que muestra ngrok.

**PC-B (el amigo):**
1. `python main.py` → abrir el Observatorio NiceGUI → **Nueva simulación** o **Continuar**.
2. Antes de iniciar, marcar **Zona Liminal**; poner en **Host** la IP/host del hosteador y el **Puerto** correcto.
3. Iniciar — el cliente se conecta al servidor remoto (no lanza proceso local).

**¿Cómo conecto dos PCs en la misma red local?**

Si ambas PCs están en el mismo WiFi o LAN, no hace falta ngrok ni port forwarding:
- PC-A: activar Zona Liminal con Host `localhost`. Obtener IP local (ej: `192.168.1.10`).
- PC-B: activar Zona Liminal con Host = IP de PC-A, Puerto `8765`.

**¿Cómo sé si la conexión funcionó?**

En el tab **Liminal** del Observatorio NiceGUI verás el badge **Activo** y el nombre de la simulación conectada en la lista de sims.

**¿Qué pasa si una simulación se desconecta?**

Los agentes que estaban en la zona liminal quedan "flotando" hasta que el servidor los elimina por timeout (o cuando la sim se reconecta). El servidor tolera desconexiones — las demás simulaciones siguen funcionando.

**¿Se puede correr el servidor y la simulación en la misma PC?**

Sí. Para desarrollo y pruebas, marcar Zona Liminal con Host `localhost`. El servidor se lanza automáticamente en background al iniciar la simulación.

**¿Cuál es el orden correcto de ejecución?**

```
PC-A (launcher NiceGUI)              PC-B (launcher NiceGUI)
──────────────────────────           ──────────────────────────
1. python main.py                    1. python main.py
2. Marcar Zona Liminal               2. Marcar Zona Liminal
   Host: localhost                      Host: <IP de PC-A>
3. Iniciar sim →                     3. Iniciar sim →
   servidor arranca en bg               cliente conecta a PC-A
   tab Liminal aparece                  tab Liminal aparece
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
4. El agente aparece en el tab **Liminal** del Observatorio NiceGUI.
5. Todas las simulaciones conectadas reciben un broadcast `agent_arrived`.

**¿El agente puede volver a su simulación?**

Sí. Tras 60 ticks liminales (~2 minutos) el servidor envía automáticamente al agente de vuelta a su simulación de origen. El agente reaparece en el hexágono del portal con un cooldown de 48 ticks para evitar reentrada inmediata. Los encuentros vividos en el liminal quedan grabados y afectan sus arquetipos, memoria episódica y próximo ciclo de sueños.

**¿Los agentes en el liminal siguen envejeciendo, teniendo hambre, etc.?**

No. Al estar `in_liminal = True`, el AgentCore de PSYCHE SIMULACRA los salta completamente. Sus necesidades no se actualizan, no envejecen, no pueden morir. Es suspensión biológica total.

**¿Qué recursos tiene la Zona Liminal? ¿Pueden comer o beber los agentes ahí?**

Ninguno. La Zona Liminal no tiene agua, comida, fauna, clima ni ningún recurso. Los agentes en suspensión no los necesitan. El espacio tiene 5 biomas puramente visuales (`vacío`, `nebulosa`, `cristalino`, `sombra`, `aurora`) que dan identidad estética al mapa pero no producen ni consumen nada. Es un espacio de tránsito, no de supervivencia.

**¿Mis agentes y los de mi amigo pueden verse entre sí?**

En el tab **Liminal** del Observatorio sí — aparecen como puntos con colores distintos según su simulación de origen. La interacción directa entre agentes de distintas sims está planificada para Fase 6.

---

## Técnico

**¿Qué versión de Python necesito?**

Python 3.11 o superior (compatible con PSYCHE SIMULACRA).

**¿El servidor necesita GPU?**

No. El servidor es headless (no tiene rendering). Cualquier máquina sirve.

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
