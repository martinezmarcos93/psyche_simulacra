# Experimento: repetición del A/B de Fase 1 con mayor poder estadístico (n=15)

**Fecha:** 2026-09-21 (sesión de continuación, rama `feature/ecuacion-personal-continuacion`)
**Referencia:** `docs/experiments/2026-09-21-fase1-ecuacion-personal.md` (experimento original, n=5)
**Motivación:** ese experimento dejó abierto explícitamente, en su sección
"Trabajo futuro", que n=5 semillas es insuficiente para distinguir "no hay
efecto" de "el efecto es real pero pequeño frente a la varianza entre
semillas" — la propia desviación estándar entre semillas superaba, en casi
todas las métricas, a la media de la diferencia pareada.

Este documento **no reemplaza** el original — lo extiende con más réplicas y
una métrica nueva (`behavioral_intra_q4`, ver `commit 575a9d8`) que el
experimento original no tenía disponible.

---

## Hipótesis

Sin cambios respecto al experimento original: activar `InterpretiveFilter`
(y opcionalmente `MentalVault`) debería producir una divergencia cultural
mediblemente mayor entre tribus. Adicionalmente, esta repetición evalúa una
hipótesis específica que quedó abierta (hipótesis 4 del documento original):
que el filtro aumenta la variación **intra-tribu** sin separar tribus entre
sí — invisible para `behavioral_kl_mean` solo, ahora visible con
`behavioral_intra_tribe_dispersion`.

## Variables

Las mismas del experimento original, más:
- `behavioral_intra_q4` (nueva): entropía normalizada [0,1] de la acción
  conductual dentro de cada tribu, promediada sobre el último cuartil.

## Método

- Mismo arnés (`scripts/ab_interpretive.py`), misma duración (300 días,
  agregación sobre el último cuartil), mismo escenario
  (`data/seeds/rich_culture_100.yaml`, 100 agentes).
- **Réplicas**: 15 semillas (42-56) × 3 condiciones (OFF / FILTER /
  FILTER+VAULT) = 45 corridas. Elegido n=15 (extremo inferior del rango
  n≥15-20 sugerido) por restricción de hardware real: esta máquina tiene 2
  núcleos lógicos: cada corrida de 300 días toma ~150-470s según contención,
  y correr en paralelo con otro cómputo (la calibración de mitología de esta
  misma sesión) degrada el throughput de ambos ~3x — se optó por correr todo
  en secuencia y priorizar completar n=15 sobre no completar n=20.
- Análisis: comparación pareada por semilla, igual que el experimento
  original (mismo diseño del arnés lo permite).
- Datos crudos: `data/metrics/ab_interpretive_fase1_n15_2026-09-21.jsonl`
  (gitignored, igual convención que el experimento original).

## Resultados

**Corrida en curso al momento de escribir este documento** — se completa esta
sección con los datos reales cuando termine (45/45 corridas). No se
completan números por adelantado.

## Interpretación y decisión

Pendiente de resultados.
