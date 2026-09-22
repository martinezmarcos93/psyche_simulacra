# Repetición del experimento A/B de la Fase 1 con n=20 semillas

**Fecha:** 2026-09-21
**Contexto:** pending item de `docs/handoffs/2026-09-21.md` §7 — repetir
`docs/experiments/2026-09-21-fase1-ecuacion-personal.md` con n≥15-20 semillas
en vez de las 5 originales, porque con n=5 no se podía distinguir "no hay
efecto" de "el efecto es real pero pequeño frente a la varianza entre
semillas".

## Método

- **Arnés**: `scripts/ab_sweep.py` (nuevo esta sesión) — orquesta
  `scripts/ab_interpretive.py` como subproceso por cada combinación
  (semilla, condición), en paralelo (4 workers, 1 por core).
- **Semillas**: 42-61 (20 semillas), 300 días cada una, `rich_culture_100.yaml`
  — mismo diseño que el experimento original, más semillas.
- **Condiciones**: `OFF` / `FILTER` / `FILTER_VAULT`, igual que antes.
- **Resultado crudo**: `data/metrics/ab_interpretive_fase1_n20.jsonl` (gitignored).
- **Una corrida falló**: seed=46, condición FILTER, por un bug real en
  `_field_divergence` (`IndexError` cuando dos tribus tienen campos locales
  con distinto número de símbolos conocidos) — encontrado y arreglado en el
  mismo commit que corrigió este experimento
  (`fix(metrics): field_kl_mean rompía con vocabularios...`). El análisis de
  FILTER queda con n=19 en vez de 20; FILTER_VAULT no se vio afectada (n=20).

## Resultado (deltas pareados por semilla, condición − OFF)

### FILTER − OFF (n=19)

| Métrica | delta_mean | delta_std | n_pos | n_neg |
|---|---|---|---|---|
| kl_mean_q4 (arquetípico) | +0.0051 | 0.034 | 11 | 8 |
| mig_q4 | -0.0610 | 0.114 | 8 | 11 |
| imi_q4 | -0.0151 | 0.122 | 10 | 9 |
| **behavioral_kl_q4** | **-1.9072** | 1.796 | **3** | **16** |
| field_kl_q4 | +0.1979 | 0.445 | 11 | 8 |
| **valence_std_q4** | **+0.1245** | 0.016 | **19** | **0** |
| **arousal_std_q4** | **+0.0594** | 0.008 | **19** | **0** |

### FILTER_VAULT − OFF (n=20)

| Métrica | delta_mean | delta_std | n_pos | n_neg |
|---|---|---|---|---|
| kl_mean_q4 (arquetípico) | +0.0058 | 0.038 | 11 | 9 |
| mig_q4 | -0.0475 | 0.093 | 8 | 12 |
| imi_q4 | -0.0042 | 0.122 | 11 | 9 |
| **behavioral_kl_q4** | **-1.4158** | 1.218 | **2** | **18** |
| field_kl_q4 | +0.4214 | 0.424 | 16 | 4 |
| **valence_std_q4** | **+0.1341** | 0.025 | **20** | **0** |
| **arousal_std_q4** | **+0.0580** | 0.008 | **20** | **0** |
| worldview_coh_q4 | +0.6803 | 0.159 | 20 | 0 |

## Interpretación

**El gate de aceptación original sigue sin cumplirse, ahora con mucho más
poder estadístico.** `kl_mean_q4`, `mig_q4` e `imi_q4` (las tres métricas de
divergencia *arquetípica* que define el criterio del roadmap) siguen sin
mostrar una dirección consistente: la mitad de las semillas suben, la mitad
bajan, con medias cercanas a cero frente al ruido entre semillas
(`delta_std` >> `delta_mean` en las tres). Con n=5 quedaba la duda de si esto
era "no hay efecto" o "efecto real tapado por varianza de semilla"; con n=19-20
y la misma falta de consistencia de signo, la duda queda mayormente cerrada:
**no hay divergencia arquetípica medible atribuible al filtro**, ni siquiera
con 4x las semillas.

**Hallazgo nuevo, inesperado y consistente: la divergencia conductual
INTER-tribu (`behavioral_kl_q4`) baja, no sube.** 16-18 de 19-20 semillas
muestran la misma dirección (negativa), con una magnitud grande relativa al
ruido. Esto es lo opuesto a lo que predecía el roadmap (se esperaba que el
filtro hiciera a las tribus más distintas entre sí en su mezcla de
cooperar/competir/aislar/manipular). Con n=5 este mismo delta ya apuntaba
negativo en el experimento original pero no se destacó como hallazgo porque
la muestra era demasiado chica para confiar en la dirección.

**La idiosincrasia afectiva individual (`valence_std`/`arousal_std`) es el
único efecto sólido, consistente y grande de los dos experimentos.** 19/19 y
20/20 semillas van en la misma dirección — esto es casi mecánico: cada agente
calcula su propia respuesta afectiva al mismo estímulo físico, así que la
dispersión entre individuos necesariamente sube cuando el filtro está ON. No
es evidencia de divergencia *cultural*, es la definición operacional del
mecanismo funcionando a nivel individual.

**Hipótesis para el hallazgo del `behavioral_kl` negativo** (no probada en
este experimento, ver "Pendiente" abajo): si la idiosincrasia que sube
(`valence_std`/`arousal_std`) ocurre principalmente *dentro* de cada tribu
(cada agente reacciona un poco distinto a lo mismo) en vez de *entre* tribus,
el promedio agregado de acciones de una tribu grande puede terminar
pareciéndose MÁS al de otra tribu (el ruido individual se cancela en el
agregado), no menos — homogeneizando `behavioral_kl_q4` en vez de aumentarlo.
Esto es exactamente la pregunta que motivó instrumentar
`behavioral_entropy_intra_mean`/`valence_std_intra`/`valence_std_inter` en
esta misma sesión (ver `docs/experiments/2026-09-21-intra-inter.md`), pero
esta corrida de n=20 no las capturó (arnés viejo).

## Decisión

Se sostiene la decisión de la sesión anterior: **no activar los flags por
defecto**. El gate de aceptación (divergencia arquetípica) no se cumple, y
ahora con evidencia mucho más sólida que antes. El hallazgo del
`behavioral_kl` negativo es interesante pero no cambia esa decisión — si
algo, refuerza que el mecanismo actual no produce el tipo de divergencia
cultural que buscaba el roadmap original.

## Limitaciones

- Los archivos de código (`core/metrics/emergence.py`,
  `scripts/ab_interpretive.py`) se editaron **mientras el barrido corría en
  background** (para agregar la instrumentación intra/inter del ítem 3 y
  arreglar el bug de `_field_divergence`). Como cada corrida de
  `ab_interpretive.py` es un subproceso que lee el archivo del disco al
  arrancar, es posible que algunas filas del jsonl crudo tengan campos
  adicionales (intra/inter) y otras no, según si el subproceso arrancó antes
  o después de cada edición. El análisis pareado reportado acá usa solo las
  8 métricas originales (presentes en todas las filas), así que el resultado
  de arriba no está afectado — pero el jsonl crudo no debe usarse para
  analizar las métricas intra/inter; para eso hace falta una corrida limpia
  posterior a estos commits (ver `docs/experiments/2026-09-21-intra-inter.md`).
- Mismo límite que el experimento original: 300 días, no descarta que el
  efecto necesite una escala temporal mucho mayor para manifestarse (la
  corrida de 600 días del experimento original tampoco lo mostró, pero no se
  repitió a 600 días con n=20 por costo de tiempo).
