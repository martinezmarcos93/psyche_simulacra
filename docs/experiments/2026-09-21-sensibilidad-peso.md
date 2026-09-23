# Sensibilidad de `_WEIGHT_INTERPRETIVE` (0.15 → 0.30)

**Fecha:** 2026-09-21
**Contexto:** pending item de `docs/handoffs/2026-09-21.md` §7 — "como
experimento de sensibilidad explícito, no como ajuste final". Motivado
también por la hipótesis de mecanismo abierta en
`docs/experiments/2026-09-21-intra-inter.md`: ¿el canal interpretativo pesa
tan poco (0.15 de 1.0) frente a arquetipo+complejo+rasgo (0.75) que no
alcanza a mover la conducta, aunque sí mueve el afecto subjetivo?

## Método

`scripts/ab_sweep.py --seeds 100-109 --days 300 --conditions OFF,FILTER --weight 0.30`
— mismas 10 semillas que `docs/experiments/2026-09-21-intra-inter.md`
(comparación directa entre pesos, misma condición y mismo escenario), doblando
`INTERPRETIVE_WEIGHT` de 0.15 (default) a 0.30 (igualando al peso del canal
arquetípico). Resultado crudo en `data/metrics/ab_sensibilidad_peso_n10.jsonl`
(gitignored).

## Resultado — comparación weight=0.15 vs. weight=0.30 (mismas 10 semillas, FILTER-OFF)

| Métrica | delta_mean @0.15 | delta_mean @0.30 | n_pos/n_neg @0.15 | n_pos/n_neg @0.30 |
|---|---|---|---|---|
| kl_mean_q4 | +0.001 | -0.007 | 6/4 | 4/6 |
| mig_q4 | -0.035 | **-0.092** | 4/6 | **1/9** |
| imi_q4 | +0.019 | -0.052 | 5/5 | 5/5 |
| **behavioral_kl_q4** | -1.243 | **-2.031** | 3/7 | **0/10** |
| field_kl_q4 | +0.376 | +0.282 | 7/3 | 7/3 |
| valence_std_q4 | +0.140 | +0.134 | 10/0 | 10/0 |
| arousal_std_q4 | +0.053 | +0.057 | 10/0 | 10/0 |
| behavioral_entropy_intra_q4 | -0.026 | +0.011 | 4/6 | 5/5 |

## Interpretación

**La hipótesis "el peso es demasiado bajo para que se note en la conducta"
queda refutada, no confirmada.** Si el peso fuera el factor limitante,
doblarlo debería acercar `behavioral_kl_q4`/`mig_q4` hacia el efecto
*positivo* que predice el roadmap, o al menos reducir la magnitud del efecto
en la dirección contraria. Ocurre lo opuesto:

- `behavioral_kl_q4` pasa de "mayormente negativo" (3/10 positivas) a
  **completamente negativo** (0/10 positivas) — las tribus se vuelven **más**
  parecidas entre sí en su mezcla de acciones al subir el peso, no menos.
- `mig_q4` pasa de ruido sin dirección clara (4/6) a **consistentemente
  negativo** (1/9) — la tribu explica *menos* información sobre los
  arquetipos individuales, no más, cuando el canal interpretativo pesa más.

La dispersión afectiva individual (`valence_std`/`arousal_std`) no cambia de
forma apreciable entre los dos pesos (+0.140→+0.134, +0.053→+0.057) — señal de
que ya está saturada por otros factores (posiblemente `_MAX_ARCH_DELTA` u
otros topes) y no es sensible a este parámetro en el rango probado.

**Conclusión revisada:** el problema no es que el canal interpretativo pese
poco. El mecanismo en sí —tal como está diseñado, préstamo de vocabulario
gateado por cristalización— parece empujar sistemáticamente hacia la
homogeneización conductual entre tribus cuando se le da más peso, no hacia la
divergencia. Esto es un resultado más fuerte que "no hay efecto": es
"hay un efecto, y va en la dirección opuesta a la predicha, y se profundiza al
subir el peso". No se investigó el mecanismo causal exacto en esta sesión
(requeriría inspeccionar `collapse_state()` con instrumentación adicional o
trazar decisiones agente por agente) — queda como pregunta abierta.

## Decisión

No se toca `_WEIGHT_INTERPRETIVE` por defecto (sigue en 0.15). Subirlo no
ayuda a cumplir el gate de aceptación del roadmap — lo aleja más. Este
resultado cierra la vía de "quizás con más peso alcanza" como explicación del
gate no cumplido; la explicación pendiente es del mecanismo mismo, no de su
magnitud.
