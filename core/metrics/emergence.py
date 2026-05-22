from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

_N_BINS = 5  # bins para discretizar arquetipos en el cálculo de MIG

if TYPE_CHECKING:
    from core.agents.agent_core import AgentCore
    from core.social.tribe_manager import TribeManager
    from core.social.collective_field import CollectiveField
    from core.world.culture_engine import CultureEngine

_EPSILON = 1e-9

# Atributos del ArchetypeVector en el orden canónico (12 dimensiones)
_ARCH_ATTRS: tuple[str, ...] = (
    "self_", "persona", "sombra", "anima_animus",
    "heroe", "sabio", "trickster", "madre",
    "padre", "nino_divino", "gobernante", "rebelde",
)


@dataclass
class DayMetrics:
    """Snapshot de métricas de emergencia para un día simulado."""
    dia: int
    # KL divergencia entre distribuciones arquetípicas tribales
    kl_mean: float          # media de los KL pairwise entre tribus
    kl_max: float           # máximo KL (par más divergente)
    # Variational Free Energy proxy (entropía del campo colectivo)
    vfe_global: float       # entropía del campo inconsciente global
    vfe_tribe_mean: float   # entropía media de los campos locales tribales
    # Índice de Modularidad de Información (IMI) — R² arquetípico-tribal
    imi: float              # fracción de varianza arquetípica explicada por tribu (0..1)
    # Mean Information Gain (MIG) — información mutua normalizada tribu↔arquetipos
    mig: float              # media de I(z_k; v)/H(z_k) sobre 12 dims (0..1)
    # Demografía y cultura
    n_alive: int
    n_tribes: int
    n_structures: int


class EmergenceMetrics:
    """
    Calcula métricas científicas de emergencia colectiva en cada día simulado.

    Las métricas validan que el sistema produce divergencia cultural real —
    no sólo ruido aleatorio — a través de tres lentes complementarias:
      - KL divergence: ¿cuán distintas son las psicologías tribales?
      - VFE proxy: ¿cuánta incertidumbre porta el inconsciente colectivo?
      - IMI: ¿cuánta varianza psicológica está explicada por membresía tribal?
    """

    def compute_day(
        self,
        dia:              int,
        agents:           dict,
        tribe_manager:    "TribeManager",
        collective_field: "CollectiveField",
        culture_engine:   "CultureEngine | None" = None,
    ) -> DayMetrics:
        alive  = {aid: a for aid, a in agents.items() if a.is_alive}
        tribes = tribe_manager.tribes

        tribe_dists            = self._tribe_archetype_distributions(alive, tribes)
        kl_mean, kl_max        = self._pairwise_kl(tribe_dists)
        vfe_global             = self._field_entropy(collective_field)
        vfe_tribe_mean         = self._mean_tribe_entropy(tribe_manager, tribes)
        imi                    = self._imi(alive, tribes)
        mig                    = self._mig(alive, tribes)
        n_structures           = len(culture_engine.structures) if culture_engine else 0

        return DayMetrics(
            dia=dia,
            kl_mean=kl_mean,
            kl_max=kl_max,
            vfe_global=vfe_global,
            vfe_tribe_mean=vfe_tribe_mean,
            imi=imi,
            mig=mig,
            n_alive=len(alive),
            n_tribes=len(tribes),
            n_structures=n_structures,
        )

    # ── Distribuciones ────────────────────────────────────────────────────────

    def _tribe_archetype_distributions(
        self, alive: dict, tribes: dict[str, list[str]]
    ) -> dict[str, list[float]]:
        """Retorna dict[tribe_id → vector 12-dim normalizado] (suma a 1)."""
        result: dict[str, list[float]] = {}
        for tribe_id, member_ids in tribes.items():
            members = [alive[aid] for aid in member_ids if aid in alive]
            if not members:
                continue
            raw = [
                sum(getattr(a.archetypes, attr, 0.0) for a in members) / len(members)
                for attr in _ARCH_ATTRS
            ]
            total = sum(raw) + _EPSILON
            result[tribe_id] = [v / total for v in raw]
        return result

    # ── KL Divergence ─────────────────────────────────────────────────────────

    def _kl_divergence(self, p: list[float], q: list[float]) -> float:
        """Divergencia KL simétrica: (KL(P||Q) + KL(Q||P)) / 2."""
        def _one_dir(a: list[float], b: list[float]) -> float:
            return sum(
                a[i] * math.log((a[i] + _EPSILON) / (b[i] + _EPSILON))
                for i in range(len(a))
            )
        return (_one_dir(p, q) + _one_dir(q, p)) / 2.0

    def _pairwise_kl(self, tribe_dists: dict[str, list[float]]) -> tuple[float, float]:
        """Media y máximo de los KL pairwise entre todas las tribus."""
        tids = list(tribe_dists.keys())
        if len(tids) < 2:
            return 0.0, 0.0
        kl_vals: list[float] = []
        for i in range(len(tids)):
            for j in range(i + 1, len(tids)):
                kl_vals.append(
                    self._kl_divergence(tribe_dists[tids[i]], tribe_dists[tids[j]])
                )
        return sum(kl_vals) / len(kl_vals), max(kl_vals)

    # ── Variational Free Energy proxy ─────────────────────────────────────────

    def _field_entropy(self, field: "CollectiveField") -> float:
        """Entropía de Shannon sobre los símbolos del campo colectivo (0..log N)."""
        vals = list(field.symbols.values())
        if not vals:
            return 0.0
        total = sum(vals) + _EPSILON
        probs = [v / total for v in vals]
        return -sum(p * math.log(p + _EPSILON) for p in probs)

    def _mean_tribe_entropy(self, tribe_manager: "TribeManager", tribes: dict) -> float:
        """Entropía media de los campos colectivos locales de cada tribu."""
        fields = [
            tribe_manager.local_fields.get(tid)
            for tid in tribes
        ]
        valid = [lf for lf in fields if lf is not None]
        if not valid:
            return 0.0
        return sum(self._field_entropy(lf) for lf in valid) / len(valid)

    # ── Índice de Modularidad de Información (IMI) ────────────────────────────

    def _imi(self, alive: dict, tribes: dict[str, list[str]]) -> float:
        """
        Fracción de la varianza arquetípica total explicada por membresía tribal.
        Inspirado en el índice de Jain-Dubes y el MIG de disentanglement.
        IMI ≈ 0 → la tribu no explica nada; IMI ≈ 1 → identidades tribales perfectas.
        """
        if len(tribes) < 2 or not alive:
            return 0.0

        agent_tribe: dict[str, str] = {
            aid: tid
            for tid, mids in tribes.items()
            for aid in mids
        }

        ratios: list[float] = []
        for attr in _ARCH_ATTRS:
            # Solo agentes con tribu asignada
            vals = [
                getattr(a.archetypes, attr, 0.0)
                for a in alive.values()
                if agent_tribe.get(a.id) is not None
            ]
            if len(vals) < 2:
                continue
            mean_all  = sum(vals) / len(vals)
            total_var = sum((v - mean_all) ** 2 for v in vals) / len(vals)
            if total_var < _EPSILON:
                continue

            # Varianza intra-tribu (pooled)
            within_sum = 0.0
            n_counted  = 0
            for tid, mids in tribes.items():
                t_vals = [
                    getattr(alive[aid].archetypes, attr, 0.0)
                    for aid in mids if aid in alive
                ]
                if len(t_vals) < 2:
                    continue
                t_mean    = sum(t_vals) / len(t_vals)
                within_sum += sum((v - t_mean) ** 2 for v in t_vals)
                n_counted  += len(t_vals)

            if n_counted == 0:
                continue
            within_var  = within_sum / n_counted
            between_var = total_var - within_var
            ratios.append(max(0.0, between_var / total_var))

        return sum(ratios) / len(ratios) if ratios else 0.0

    # ── Mean Information Gain (MIG) ───────────────────────────────────────────

    def _mig(self, alive: dict, tribes: dict[str, list[str]]) -> float:
        """
        Mean Information Gain: información mutua normalizada entre membresía
        tribal y valores arquetípicos. Inspirado en Chen et al. (2018).

        Para cada dimensión arquetípica k:
            I(z_k; v) = H(z_k) - H(z_k | v)
            MIG_k     = I(z_k; v) / H(z_k)    si H(z_k) > 0, else 0

        MIG = media de MIG_k sobre las 12 dimensiones.

        MIG ≈ 0 → la tribu no aporta información sobre los arquetipos.
        MIG ≈ 1 → la tribu determina completamente los arquetipos (máx. disentanglement).

        Implementación: discretizamos en _N_BINS bins de ancho uniforme [0, 1].
        """
        if len(tribes) < 2 or not alive:
            return 0.0

        # Mapa agent_id → tribe_id
        agent_tribe: dict[str, str] = {
            aid: tid
            for tid, mids in tribes.items()
            for aid in mids
            if aid in alive
        }
        tribe_ids   = list(tribes.keys())
        n_total     = len(agent_tribe)
        if n_total == 0:
            return 0.0

        # Proporción de agentes por tribu p(v=t)
        tribe_counts = {
            tid: sum(1 for aid in mids if aid in alive)
            for tid, mids in tribes.items()
        }

        mig_vals: list[float] = []

        for attr in _ARCH_ATTRS:
            # Discretizar valores en _N_BINS bins
            vals = {
                aid: min(int(getattr(a.archetypes, attr, 0.0) * _N_BINS), _N_BINS - 1)
                for aid, a in alive.items()
                if agent_tribe.get(aid) is not None
            }
            if not vals:
                continue

            # H(z_k) — entropía marginal del arquetipo k
            bin_counts: list[int] = [0] * _N_BINS
            for b in vals.values():
                bin_counts[b] += 1
            h_zk = _entropy(bin_counts, n_total)
            if h_zk < _EPSILON:
                continue

            # H(z_k | v) — entropía condicional dado tribu
            h_zk_given_v = 0.0
            for tid in tribe_ids:
                n_t = tribe_counts.get(tid, 0)
                if n_t == 0:
                    continue
                t_bins: list[int] = [0] * _N_BINS
                for aid, mids in [(a, tribes[tid]) for a in tribes[tid]]:
                    if aid in vals:
                        t_bins[vals[aid]] += 1
                h_zk_given_v += (n_t / n_total) * _entropy(t_bins, n_t)

            mi = max(0.0, h_zk - h_zk_given_v)
            mig_vals.append(mi / h_zk)

        return sum(mig_vals) / len(mig_vals) if mig_vals else 0.0


def _entropy(counts: list[int], total: int) -> float:
    """Entropía de Shannon de una distribución discreta dada como conteos."""
    if total == 0:
        return 0.0
    h = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            h -= p * math.log(p + _EPSILON)
    return h
