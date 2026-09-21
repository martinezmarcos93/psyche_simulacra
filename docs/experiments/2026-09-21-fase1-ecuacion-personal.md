# Experimento: Fase 1 de la Ecuación Personal (`InterpretiveFilter`) — cierre del gate de aceptación

**Fecha:** 2026-09-21
**Commit base:** fusión `xperiment → main` (`1678701`) + completado de `attributed_cause`/`moral_judgment` (ver `DEVELOPMENT_LOG.md`)
**Roadmap:** `src/ROADMAP_ECUACION_PERSONAL.md`, criterio de aceptación de Fase 1

---

## Hipótesis

El roadmap declara: activar `InterpretiveFilter` (y opcionalmente `MentalVault`)
debería producir una **divergencia cultural mediblemente mayor** entre tribus,
porque cada agente empieza a interpretar el mismo estímulo físico de forma
idiosincrática en vez de reaccionar de forma homogénea.

Criterio de aceptación explícito del roadmap:

```
[ Fase 1 ] → correr con flag activo → medir KL/MIG/VFE
        │
   ¿Divergencia cultural mediblemente mayor?  ──NO→ revisar operadores antes de seguir
        │ SÍ
   TEST FILOSÓFICO (ver docs/EMERGENCE.md) → si pasa, proceder a Fase 2
```

## Variables

- **Independiente**: condición — `OFF` (ambos flags apagados) / `FILTER`
  (`INTERPRETIVE_FILTER_ENABLED=1`) / `FILTER+VAULT` (+ `MENTAL_VAULT_ENABLED=1`).
- **Dependientes**: `kl_mean_q4`, `kl_per_tribe_q4`, `mig_q4`, `imi_q4` (divergencia
  arquetípica); `behavioral_kl_q4`, `field_kl_q4` (divergencia conductual/de campo —
  instrumento "camino c", pensado específicamente para detectar lo que el filtro
  mueve primero); `valence_std_q4`, `arousal_std_q4` (dispersión afectiva
  idiosincrática); `worldview_coh_q4` (coherencia del `MentalVault`, solo con vault
  ON); `final_alive` (control de mortalidad diferencial).
- **Controles**: mismo `seed` entre las 3 condiciones de una réplica (arnés
  diseñado para esto — "Mismo seed → mismas condiciones iniciales → la única
  diferencia es la ecuación personal"), mismo archivo de escenario
  (`data/seeds/rich_culture_100.yaml`), 100 agentes iniciales.

## Método

- **Arnés**: `scripts/ab_interpretive.py`, modo headless (sin BD, narrativa LLM ni
  Obsidian) — clock + `WorldCore` + `AgentCore` desnudos. Verificado ~0.5 s/día
  simulado con 100 agentes (muy por debajo del ~1 min/día del modo completo que
  cita el README — esa cifra es del modo con narrativa/UI, no del modelo en sí).
- **Duración principal**: 300 días (el default del arnés), agregando métricas
  sobre el **último cuartil** (días ≈225-300) para evitar el transitorio de
  formación de tribus.
- **Réplicas**: 5 semillas (42, 43, 44, 45, 46) × 3 condiciones = 15 corridas.
  Esto es una extensión respecto al diseño original del arnés (que corría una
  sola semilla a mano) — se agregaron réplicas porque una sola semilla no
  permite distinguir "el filtro cambió algo" de "esta semilla en particular dio
  ese número".
- **Chequeo adicional de arranque lento**: 1 semilla (42) × 3 condiciones × 600
  días, para descartar que el efecto necesite más tiempo en acumular vocabulario
  emergente antes de manifestarse (el préstamo de `narrative_frame`/
  `moral_judgment` depende de que ya haya símbolos cristalizados, lo cual no pasa
  en los primeros días).
- **Análisis**: comparación pareada por semilla (`FILTER - OFF`, `FILTER+VAULT -
  OFF`), no solo promedios de grupo — la variabilidad entre semillas es grande
  (ver más abajo) y el diseño del arnés (mismo seed entre condiciones) existe
  específicamente para permitir el pareo.

## Resultados

### Datos crudos

`data/metrics/ab_interpretive_fase1.jsonl` (15 líneas, una por corrida) y
`data/metrics/ab_interpretive_fase1_long.jsonl` (600 días, seed 42).

### Promedios de grupo (5 semillas, 300 días)

| Métrica | OFF | FILTER | FILTER+VAULT |
|---|---:|---:|---:|
| `kl_mean_q4` | 0.1035 | 0.1005 | 0.0813 |
| `mig_q4` | 0.4258 | 0.4109 | 0.4501 |
| `imi_q4` | 0.3199 | 0.2978 | 0.2711 |
| `behavioral_kl_q4` | 10.410 | 9.533 | 10.039 |
| `field_kl_q4` | 2.021 | 2.087 | 1.885 |
| `n_tribes_q4` | 19.6 | 14.7 | 19.0 |
| `final_alive` (control) | 79.6 | 79.8 | 74.0 |

### Diferencias pareadas por semilla (la comparación que importa)

| Métrica | media(FILTER−OFF) | sd | media(FILTER+VAULT−OFF) | sd |
|---|---:|---:|---:|---:|
| `kl_mean_q4` | −0.0031 | 0.0414 | −0.0221 | 0.0727 |
| `mig_q4` | −0.0270 | 0.0812 | +0.0110 | 0.0958 |
| `imi_q4` | −0.0214 | 0.0986 | −0.0482 | 0.1119 |
| `behavioral_kl_q4` | −0.8381 | 1.0187 | −0.3714 | 1.6938 |
| `field_kl_q4` | −0.0588 | 0.2898 | −0.0808 | 0.4168 |

En **ninguna** métrica de divergencia la media pareada es positiva y grande
respecto a su desviación estándar entre semillas — el efecto, si existe, no
supera el ruido de muestra a n=5. `mig_q4` en FILTER+VAULT es la única media
positiva, y su sd (0.096) es casi 9× la media (0.011): no es un hallazgo, es
ruido.

### Corrida larga (600 días, seed 42 — descarta arranque lento)

`worldview_coh_q4` con vault ON llega a niveles comparables a los de 300 días
(0.5-0.86 en las corridas cortas) y las métricas de divergencia arquetípica/
conductual no muestran una tendencia creciente hacia el día 600 respecto al día
300 para la misma semilla — no hay evidencia de que el efecto "tarde en
aparecer".

### Métricas afectivas (control de que el filtro efectivamente hace algo)

`valence_std_q4` y `arousal_std_q4` son **0.0 exactas** en OFF (estructural: sin
`PerceivedEvent` no hay valence que dispersar) y consistentemente > 0 con el
filtro ON (0.12-0.21 para valence). Esto confirma que el filtro **sí** está
produciendo interpretación idiosincrática real a nivel individual — el problema
no es que el filtro no haga nada, es que esa idiosincrasia no se traduce en
divergencia **entre tribus** medible con este instrumento, a esta escala.

## Interpretación

**El gate de aceptación de la Fase 1, tal como está escrito, NO se cumple.**
No hay evidencia de que activar `InterpretiveFilter` (con o sin `MentalVault`)
produzca una divergencia cultural, conductual o arquetípica entre tribus mayor
que sin él, a 300-600 días con 100 agentes y el peso de canal actual
(`_WEIGHT_INTERPRETIVE = 0.15`).

Esto **no es lo mismo que decir que la implementación está mal** — el test
filosófico (`docs/EMERGENCE.md` §2) confirma que el mecanismo es limpio: no hay
ningún símbolo inyectado por diseño, y la idiosincrasia individual (valence/
arousal dispersos) es real y medible. Hipótesis abiertas, sin resolver en esta
sesión, sobre por qué no escala a divergencia inter-tribal:

1. **Peso de canal insuficiente**: 0.15 sobre 6 canales puede ser demasiado bajo
   frente al peso arquetípico (0.30) para mover la aguja a nivel de tribu — el
   colapso conductual sigue dominado por la psicología estable del agente, no
   por su interpretación momento a momento.
2. **El préstamo diluye la divergencia, no la amplifica**: `narrative_frame` y
   `moral_judgment` solo pueden nombrar lo que YA es compartido (cristalizado en
   el campo), así que por diseño tienden a converger a lo común de la tribu, no
   a diferenciar. La verdadera fuente de idiosincrasia (`valence`/`arousal`) no
   pasa por préstamo, pero su peso en el colapso es bajo (ver punto 1).
3. **Poder estadístico insuficiente**: n=5 semillas es bajo frente a la
   variabilidad natural entre corridas (sd comparable o mayor a la media en casi
   todas las métricas) — no se puede descartar un efecto real pero pequeño sin
   más réplicas (ver "Trabajo futuro").
4. **La divergencia ya es alta sin el filtro**: las tribus en `rich_culture_100`
   ya divergen fuertemente por deriva de bioma y clustering social (mecanismos
   preexistentes, R5-R7); el filtro puede estar añadiendo variación intra-tribu
   más que inter-tribu, que ninguna de las métricas actuales separa
   explícitamente.

## Test filosófico

Ver `docs/EMERGENCE.md` §§2-3 para la auditoría completa. Resultado: **pasa**.
Ningún operador de `InterpretiveFilter`, `MentalVault` o `collapse_state` asigna
contenido simbólico directamente; todo préstamo está gateado por la existencia
previa de vocabulario cristalizado en otro sistema (campo colectivo, memoria
causal propia del agente, o mitología ya consolidada), y esa condición se
verifica con tests explícitos (`test_sin_campo_no_hay_frame`,
`test_sin_asociacion_causal_propia_no_hay_atribucion`,
`test_sin_mito_moral_compatible_no_hay_juicio`).

## Decisión

Siguiendo la propia rama del roadmap ("NO → revisar operadores antes de
seguir"), **no se declara la Fase 1 validada empíricamente**, aunque sí
**completa e implementada correctamente**. Dado que Fase 2 (`MentalVault`) ya
estaba construida antes de esta sesión —decisión tomada explícitamente en el
propio roadmap, pese a que Fase 1 sola no pasaba su gate arquetípico original,
razón por la cual se instrumentó el "camino c"— y que ese mismo instrumento
tampoco muestra el efecto esperado, la recomendación técnica es:

- **No activar los flags por defecto** (se mantienen OFF; el comportamiento de
  toda corrida existente permanece byte-idéntico).
- **No seguir ajustando pesos a ciegas** para forzar el resultado — eso violaría
  el principio de la propia auditoría filosófica (ajustar un parámetro hasta que
  una métrica se mueva, sin entender el mecanismo, es "tuning para mover una
  métrica", explícitamente lo que el roadmap prohíbe en otro contexto).
- **Registrar la Fase 1/2 como implementadas, auditadas y experimentalmente
  inconclusas/negativas a esta escala** — no como fracaso, sino como resultado
  científico válido: la hipótesis del roadmap, tal como estaba formulada, no se
  sostuvo con la evidencia recogida.

## Limitaciones de este experimento

- 100 agentes, un solo archivo de escenario (`rich_culture_100.yaml`).
- 5 semillas es un n pequeño para las magnitudes de varianza observadas; un
  efecto de tamaño similar al de la variable de control (`final_alive`, que sí
  varía fuertemente entre semillas por causas no relacionadas al filtro) podría
  quedar enmascarado.
- No se separó divergencia intra-tribu de inter-tribu explícitamente (hipótesis
  4 arriba) — requeriría una métrica nueva, no instrumentada en esta sesión.
- El modo headless omite narrativa LLM; si el filtro tuviera un efecto principal
  vía cómo se *narra* la experiencia (no cómo se *actúa*), este arnés no lo
  vería.

## Trabajo futuro (no ejecutado en esta sesión, por alcance)

- Repetir con n≥15-20 semillas para poder estadístico real (factible: cada
  corrida de 300 días tarda ~150s headless, 20 semillas × 3 condiciones ≈ 2.5h).
- Instrumentar divergencia intra- vs. inter-tribu por separado.
- Probar con `_WEIGHT_INTERPRETIVE` más alto (ej. 0.30, igualando al canal
  arquetípico) como experimento de sensibilidad — documentando explícitamente
  que es una prueba de sensibilidad y no un ajuste final "porque sí".
- Escenarios con más agentes/tribus (el `rich_culture_100` con clustering cada
  30 días puede tener pocas tribus efectivas para que KL/MIG sean estables).
