# Validación de la instrumentación intra-tribu vs. inter-tribu

**Fecha:** 2026-09-21
**Contexto:** pending item de `docs/handoffs/2026-09-21.md` §7 — instrumentar
si el `InterpretiveFilter` aumenta la variación *dentro* de una tribu (invisible
a `behavioral_kl_mean`/`valence_std`/`arousal_std` globales tal como estaban
definidos) en vez de *entre* tribus. Implementado en
`core/metrics/emergence.py` (`behavioral_entropy_intra_mean`,
`valence_std_intra/inter`, `arousal_std_intra/inter`) y validado acá con datos
reales, no solo tests unitarios.

## Método

`scripts/ab_sweep.py --seeds 100-109 --days 300 --conditions OFF,FILTER`
(10 semillas, condición FILTER_VAULT omitida para acotar el tiempo de corrida
— no es la comparación relevante para este ítem). Resultado crudo en
`data/metrics/ab_intra_inter_n10.jsonl` (gitignored).

## Resultado (FILTER − OFF, pareado por semilla, n=10)

| Métrica | delta_mean | n_pos/n_neg |
|---|---|---|
| behavioral_kl_q4 (inter-tribu, ya existía) | -1.243 | 3/7 |
| behavioral_entropy_intra_q4 (nueva) | -0.026 | 4/6 |
| valence_std_intra_q4 (nueva) | **+0.088** | **10/0** |
| valence_std_inter_q4 (nueva) | **+0.102** | **10/0** |
| arousal_std_intra_q4 (nueva) | **+0.023** | **10/0** |
| arousal_std_inter_q4 (nueva) | **+0.029** | **10/0** |

(Consistente con la corrida n=20 de
`docs/experiments/2026-09-21-fase1-ecuacion-personal-n20.md`: `behavioral_kl_q4`
baja de forma consistente con el filtro ON.)

## Interpretación

La hipótesis que motivó este ítem —que la idiosincrasia subía *solo* dentro de
cada tribu, invisible al instrumento anterior— **no se confirma tal cual**.
Tanto `valence_std_intra` como `valence_std_inter` suben de forma perfectamente
consistente (10/10 semillas cada una); lo mismo para arousal. El filtro separa
afectivamente a los agentes **tanto dentro de su propia tribu como entre
tribus distintas** — no es un fenómeno puramente intra-tribu.

Lo que sí queda claro con este instrumento es un **desacople entre afecto y
conducta**: mientras la dispersión afectiva (valence/arousal) sube de forma
sólida en las cuatro descomposiciones, la entropía conductual *dentro* de cada
tribu (`behavioral_entropy_intra_q4`) no muestra dirección consistente
(4 positivas / 6 negativas — ruido), y la divergencia conductual *entre*
tribus (`behavioral_kl_q4`) baja de forma consistente. Es decir: el filtro
cambia mucho cómo los agentes *sienten* el mismo estímulo, pero eso no se
traduce en un cambio consistente de qué *hacen* (individual o
agregadamente).

**Hipótesis de mecanismo (no probada, para una sesión futura):** en
`collapse_state()` (`core/agents/quantum/collapse.py`), el canal interpretativo
pesa 0.15 frente a 0.30 (arquetipo) + 0.25 (complejo) + 0.20 (rasgo) = 0.75 de
señal que el filtro no toca. La conducta observable sigue estando dominada por
canales que el filtro no modifica; el filtro mueve mucho el afecto subjetivo
(`valence`/`arousal`, que se leen directo de `PerceivedEvent`) pero tiene poco
margen para mover la acción final. Esto es consistente con (y ayuda a explicar)
por qué el gate de aceptación original — divergencia *arquetípica/conductual*
— no se cumple: el mecanismo, tal como está pesado, es mucho más un
"instrumento de afecto individual" que un "instrumento de divergencia
conductual/cultural". El experimento de sensibilidad de peso
(`docs/experiments/2026-09-21-sensibilidad-peso.md`) es la prueba natural de
esta hipótesis: si subir `_WEIGHT_INTERPRETIVE` mueve `behavioral_kl`/`imi`/`mig`
en una dirección consistente, la hipótesis gana fuerza; si no, el mecanismo de
préstamo en sí (no el peso) es la causa.

## Decisión

La instrumentación queda incorporada de forma permanente a `EmergenceMetrics`
(no es un experimento de un solo uso). No cambia la decisión de no activar los
flags por defecto — pero deja un instrumento reusable y una hipótesis concreta
y falsable para la próxima vez que se revise la Ecuación Personal.
