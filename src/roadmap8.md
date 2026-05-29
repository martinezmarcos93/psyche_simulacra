# Roadmap 8.0 — Economía Emergente: Surplus, Poder y Clases

**Rama de trabajo:** `economy` — merge a `main` al completar bloque H.

**Construye sobre:** Roadmap 7 (generaciones, memoria cultural, estructuras, deidades)  
y los roles sociales existentes (big_man, anciano, cazador_focal).

**Objetivo:** tras 3000–6000 días, una simulación produce naturalmente:
- ≥ 2 clases económicas diferenciadas (Gini acumulado > 0.3)
- ≥ 1 episodio de redistribución ritual por big_man
- ≥ 1 crisis de escasez que catalice evento cultural (mito, tabú o schism)
- ≥ 3 deudas activas entre agentes de tribus distintas
- ≥ 1 especialización económica emergente (artesano o comerciante)

**Filosofía de diseño:** la economía no es un sistema de puntos.
Es una estructura de poder simbólico que determina quién puede satisfacer
sus necesidades, quién depende de quién, y cómo eso moldea la psique colectiva.
Ningún fenómeno económico (class, deuda, monopolio) debe estar hardcodeado:
debe emerger de las interacciones individuales acumuladas.

---

## Bloque A — Inventario y surplus ✦ baja complejidad

> Sin surplus no hay economía. Sin economía no hay poder.
> Este bloque es el sustrato de todo lo demás.

### A1 — Campo `inventory` en Agent

- Añadir `inventory: dict[str, float]` al agente (default `{}`).
  Claves: `"comida"`, `"agua"`, `"material"` (madera/piedra/fibra del entorno).
- Al ejecutar `RECOLECTAR` o `CAZAR` con éxito:
  - Si la necesidad ya está satisfecha (hambre < 0.30 y sed < 0.20),
    el excedente va al inventario en vez de consumirse de inmediato.
  - Límite de inventario: 20 unidades por recurso (modela capacidad de carga).
- `inventory` serializable en `to_dict` / `from_dict`.

### A2 — Decaimiento pasivo del inventario

- Comida: pierde 0.15 unidades/día (putrefacción).
- Agua: pierde 0.08 unidades/día (evaporación).
- Material: no decae.
- Si el inventario llega a 0 en un recurso crítico y las necesidades suben,
  el agente busca ese recurso con prioridad máxima.

### A3 — Surplus como señal social

- Si un agente tiene inventario total > 8 unidades durante ≥ 7 días,
  sus bonds entrantes aumentan +0.008/día (el que tiene más, atrae más).
- Registrar en CulturalMemory de la tribu evento `"surplus_agente"` cuando
  el inventario supera 15 unidades por primera vez.

---

## Bloque B — Reciprocidad y don ✦ baja-media complejidad

> La economía arcaica no es comercio: es don. El don crea obligación.
> La obligación es la primera forma de deuda.

### B1 — Acción `DAR_RECURSO`

- Nueva `ActionType.DAR_RECURSO` con `target_id` y `resource` y `amount`.
- Un agente la selecciona cuando:
  - Su inventario del recurso > 6 unidades, **Y**
  - Hay un agente co-ubicado con necesidad crítica (hambre > 0.70 o sed > 0.80), **O**
  - Bond con ese agente > 0.60 y la tribu lleva ≥ 3 días sin un `DAR`.
- Al ejecutar: transfiere `amount` (1–3 unidades) del donante al receptor.
- El receptor satisface parcialmente su necesidad si la tiene, o acumula en inventario.

### B2 — Efecto del don en vínculos y complejos

- Donante: bond con receptor +0.06; ansiedad −0.03; arquetipo `madre`/`padre` +0.002.
- Receptor: bond con donante +0.10; arquetipo `inferioridad` −0.004 si era crítico.
- Si el receptor nunca devuelve nada en 30 días: donante acumula "deuda percibida"
  (`_deuda_percibida: dict[agent_id, float]`). Cada día sin pago += 0.01.

### B3 — Registro cultural del don

- Cada acto de don entre agentes de tribus distintas → evento `"don_intertribal"`
  en CulturalMemory de ambas tribus.
- Si el mismo par dona/recibe ≥ 5 veces → evento `"alianza_economica"` y
  bond permanente mínimo de 0.40 entre ellos.

---

## Bloque C — big_man como redistribuidor ✦ media complejidad

> En la literatura etnográfica, el big_man legitima su autoridad redistribuyendo.
> Ya existe el rol. Ahora le damos comportamiento económico real.

### C1 — big_man acumula y redistribuye

- El `big_man` activo de una tribu ejecuta `DAR_RECURSO` con prob. 0.25/día
  hacia cualquier miembro con necesidad > 0.50, independientemente del bond.
- Su `legitimidad` (campo ya existente en SocialRole) sube +0.02 por cada
  acto de redistribución, baja −0.01/día sin redistribuir.
- Si `legitimidad < 0.20` durante 10 días: el rol queda vacante → detección
  de nuevo candidato (lógica ya existente).

### C2 — Ritual de redistribución colectivo

- Si el big_man tiene inventario total > 12 unidades Y la tribu lleva ≥ 5 días
  con myth_pressure > 0.40: ejecuta "redistribución ritual" (distribuye todo
  su inventario equitativamente entre los miembros presentes).
- Efectos: myth_pressure tribal −0.30; humor promedio +0.15; evento
  `"redistribucion_ritual"` en CulturalMemory (intensidad 0.75).
- El ritual puede cristalizar proto-mito tipo `"teogonia"` si myth_pressure
  era > 0.60 antes del acto.

### C3 — Monopolio simbólico

- Si el big_man controla > 60% del inventario total de la tribu durante
  ≥ 15 días: activar complejo `"poder"` en él y complejo `"inferioridad"`
  en los miembros con menos del 5% del inventario total.
- Registrar evento `"concentracion_recursos"` — input potencial para
  proto-mito tipo `"escatologia"` (el rey que cae).

---

## Bloque D — Deuda y dependencia ✦ media complejidad

> La deuda crea asimetría de poder antes que cualquier moneda.
> El deudor no puede abandonar al acreedor: ahí nace la jerarquía.

### D1 — Sistema de deuda (`DebtLedger`)

- Nuevo módulo `core/social/debt.py` con `DebtLedger`:
  - Registra `(deudor_id, acreedor_id, recurso, monto, dia_origen)`.
  - `add_debt()`, `pay_debt()`, `outstanding_debts(agent_id)`.
  - Serializable.
- La deuda se crea cuando:
  - Un agente recibe un don de otro y su `_deuda_percibida` hacia ese agente > 0.25.
  - Un big_man hace una redistribución ritual: todos los receptores quedan
    con deuda simbólica de 0.5 unidades de "material" hacia él.

### D2 — Efectos psicológicos de la deuda

- Deudor: arquetipo `inferioridad` +0.003/día por deuda pendiente;
  ansiedad +0.005/día si deuda > 3 unidades total.
- Acreedor: arquetipo `gobernante` +0.002/día por deuda entrante;
  bonds entrantes del deudor hacia él no pueden bajar de 0.20.
- Si la deuda supera 8 unidades y el deudor no puede pagar:
  evento `"deuda_impagable"` → complejo `"abandono"` o `"culpa"` activado.

### D3 — Pago y liberación

- El agente deudor elige `DAR_RECURSO` con target = acreedor cuando tiene surplus.
- Al pagar: deuda reduce; complejo `"inferioridad"` baja −0.02; bond con
  acreedor +0.04 (la liberación fortalece el vínculo).
- Si el acreedor muere antes de cobrar: la deuda se hereda al linaje
  (vía `LineageGraph` ya existente) o se cancela si no hay heredero.
  Evento `"deuda_cancelada_por_muerte"` en CulturalMemory.

---

## Bloque E — Diferenciación de clases ✦ media complejidad

> Las clases no se declaran. Emergen de quién tiene inventario,
> quién tiene deuda, y quién controla el conocimiento valioso.

### E1 — Score económico de agente

- Calcular diariamente `economic_score` de cada agente:
  ```
  score = (inventario_total × 0.4)
        + (bonds_entrantes_promedio × 5.0)
        + (conocimientos_únicos × 3.0)
        − (deuda_pendiente × 0.6)
  ```
- No persistir el score: calcularlo on-demand desde los datos existentes.

### E2 — Clases emergentes (cuartiles tribales)

- Una vez por clustering (cada `DAYS_UNTIL_CLUSTERING` días), calcular
  los cuartiles del `economic_score` dentro de cada tribu:
  - Q1 (bottom 25%): `clase = "subsistencia"` → complejo `"inferioridad"` boost.
  - Q2–Q3 (middle 50%): `clase = "medio"` → sin efecto adicional.
  - Q4 (top 25%): `clase = "prominente"` → arquetipo `"gobernante"` boost +0.003/día.
- Persistir `clase_economica: str` en el agente (to_dict / from_dict).

### E3 — Movilidad de clase

- Si un agente sube de `"subsistencia"` a `"medio"`: evento en CulturalMemory
  `"ascenso_economico"` (intensidad 0.50); bond con todos los miembros del
  mismo nivel nuevo +0.03.
- Si un agente baja a `"subsistencia"`: activar complejo `"abandono"` con
  intensidad 0.40; beast de complejo `"inferioridad"`.
- Un agente de clase `"prominente"` durante ≥ 30 días puede candidatearse
  a `big_man` aunque no sea el de mayor redistribución.

---

## Bloque F — Crisis de escasez y colapso ✦ alta complejidad

> La escasez real prueba si la economía generó resiliencia o fragilidad.
> Una crisis bien modelada destruye vínculos, crea mitos y puede fracturar tribus.

### F1 — Escasez acumulativa

- Si el `ResourceSystem` del hex donde vive una tribu tiene `comida < 10%`
  del máximo Y `agua < 15%` durante ≥ 10 días: declarar
  `escasez_activa = True` para esa tribu.
- Durante escasez: `DAR_RECURSO` requiere inventario > 8 (umbral más alto);
  el big_man NO redistribuye hasta que su inventario > 10.
- Agentes con `clase = "subsistencia"` tienen prob. de muerte 2× mayor.

### F2 — Respuestas emergentes a la crisis

Sin programar la solución, monitorear si emergen naturalmente:
- **Migración**: ansiedad > 0.75 → acción `EXPLORAR` con prioridad máxima.
- **Competencia intertribal**: un agente puede intentar `RECOLECTAR` en hex
  de otra tribu (si hay recursos). Genera `_register_tribal_attack` si lo hace.
- **Solidaridad**: si hay big_man activo con legitimidad > 0.70, puede iniciar
  don hacia tribus hermanas (bond intertribal > 0.55).

### F3 — Evento de colapso económico

- Si la escasez dura ≥ 20 días Y la tribu pierde > 30% de sus miembros
  (muerte o migración): evento `"colapso_economico"` en CulturalMemory
  (intensidad 1.0).
- Efectos: myth_pressure tribal +0.50; todos los complejos activos se
  intensifican ×1.5; proto-mito `"escatologia"` con umbral reducido al 50%.
- El vault recibe entrada en `Cronica.md` con descripción del colapso.

---

## Bloque G — Especialización económica emergente ✦ alta complejidad

> La especialización es la segunda función del surplus: libera tiempo
> de subsistencia y permite que algunos agentes hagan solo una cosa bien.

### G1 — Nuevo rol: `artesano`

- Emerge cuando un agente tiene:
  - Inventario de `material` > 8 unidades durante ≥ 10 días, **Y**
  - Conocimiento (`KnowledgeSystem`) de `tecnica_constructiva` o `curacion`, **Y**
  - `clase = "prominente"` o `"medio"`.
- Efecto del rol: el agente construye estructuras (CultureEngine) con cooldown
  reducido al 50%; sus construcciones generan `humor_d` ×1.5.
- El rol es reconocido con `SocialRole(tipo="artesano", ...)`.

### G2 — Nuevo rol: `comerciante`

- Emerge cuando un agente ejecuta ≥ 5 `DAR_RECURSO` hacia agentes de tribus
  distintas en ≤ 30 días Y tiene bonds con ≥ 3 tribus distintas > 0.45.
- Efecto del rol: su prob. de `DAR_RECURSO` se dobla; puede iniciar don
  sin necesitar co-ubicación (radio extendido a 5 hexes).
- Cada acto de comercio del `comerciante` da al campo tribal +0.04 en
  `lf.symbols["gobernante"]` (el comerciante construye poder simbólico).

### G3 — Legitimidad por desempeño

- `artesano`: su `legitimidad` sube +0.015 por estructura construida;
  baja −0.02/día si lleva > 15 días sin construir nada.
- `comerciante`: su `legitimidad` sube +0.02 por intercambio intertribal;
  baja −0.01/día sin intercambios.
- Si `legitimidad < 0.15`: rol vacante (igual que big_man ya existente).

---

## Bloque H — Observabilidad económica ✦ baja-media complejidad

> No se puede evaluar lo que no se ve. Este bloque hace la economía
> legible en NiceGUI y en el vault.

### H1 — Panel "Pulso Económico" en tab Resumen

Añadir junto al Pulso Cultural (F1 del R7) 4 métricas económicas:
- Gini estimado (distribución de inventarios en la tribu con más agentes)
- Deudas activas totales
- Redistribuciones por big_man esta sesión
- Ratio agentes en subsistencia / total

### H2 — Tab "Economía" en el inspector de agentes

En el inspector de agente existente, añadir sección:
- Inventario actual (comida / agua / material)
- Clase económica y score
- Deudas pendientes (deudor y acreedor)
- Dones dados y recibidos esta sesión

### H3 — Exportar economía al vault

- En `obsidian/writer.py`: nuevo método `write_economia(tribe_manager, dia)`.
- Genera `vault/Colectivo/Economia.md` cada 100 días con:
  - Tabla de clases por tribu
  - Top 5 deudas activas
  - Eventos económicos recientes de CulturalMemory
  - Score Gini por tribu

### H4 — `scripts/eval_economy.py`

Similar a `eval_culture.py` — carga checkpoint más reciente y produce:
- Gini por tribu
- Deudas activas y su antigüedad
- N redistribuciones / N días
- Ratio de especialización (artesanos + comerciantes / total)
- Score 0–100

---

## Orden de implementación sugerido

```
A1 → A2 → A3      (inventario — prerequisito de todo)
B1 → B2 → B3      (reciprocidad — primera economía real)
C1 → C2 → C3      (big_man — usa roles existentes, alto impacto visible)
D1 → D2 → D3      (deuda — asimetría de poder)
E1 → E2 → E3      (clases — emergencia de estructura social)
H1 → H2           (observabilidad temprana — permite evaluar lo anterior)
F1 → F2 → F3      (crisis — necesita todo lo anterior para ser significativa)
G1 → G2 → G3      (especialización — corona del sistema)
H3 → H4           (exportación y evaluador)
```

## Criterio de merge a main

Correr `scripts/eval_economy.py` sobre un checkpoint de 3000+ días con
`rich_culture_100.yaml`. El output debe mostrar:
- Gini promedio > 0.25 en al menos 2 tribus
- ≥ 1 redistribución ritual registrada en CulturalMemory
- ≥ 1 deuda activa con antigüedad > 100 días
- ≥ 1 rol `artesano` o `comerciante` activo

---

## Dependencias técnicas

| Ítem nuevo | Depende de |
|------------|-----------|
| `inventory` en Agent | `agent.py` to_dict / from_dict |
| `DAR_RECURSO` action | `WorldAction`, `ActionType` |
| `DebtLedger` | módulo nuevo `core/social/debt.py` |
| `clase_economica` en Agent | clustering diario existente |
| `artesano` / `comerciante` | `SocialRole` existente + `KnowledgeSystem` |
| `write_economia()` | `ObsidianWriter` existente |
| Panel Pulso Económico | refs de NiceGUI existentes |

## Notas de diseño

- **No introducir moneda en R8.** El surplus + don + deuda es suficiente para
  producir complejidad económica real. La moneda puede venir en R9 si la
  reciprocidad directa satura.
- **El inventario reemplaza el surplus implícito** que ahora se pierde. Los
  agentes que recolectan en exceso no "desperdician" — acumulan.
- **big_man ya existe.** No reescribirlo. Solo añadir comportamiento económico
  sobre el rol ya definido.
- **DebtLedger es el único módulo nuevo.** Todo lo demás son extensiones
  de código existente (Agent, AgentCore, WorldAction, SocialRole, Writer).
