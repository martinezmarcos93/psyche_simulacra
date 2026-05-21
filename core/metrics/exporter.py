from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .emergence import DayMetrics

_DEFAULT_DIR = "data/metrics"
_FLUSH_EVERY = 10   # días entre flushes automáticos


class MetricsExporter:
    """
    Persiste las métricas de emergencia en disco.
    - Serie temporal: data/metrics/emergence_series.csv
    - Resumen agregado: data/metrics/emergence_summary.json
    """

    def __init__(self, output_dir: str = _DEFAULT_DIR) -> None:
        self._dir      = Path(output_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._csv_path = self._dir / "emergence_series.csv"
        self._buffer:  list[DayMetrics] = []
        self._headers_written = self._csv_path.exists() and self._csv_path.stat().st_size > 0

    def record(self, metrics: "DayMetrics") -> None:
        self._buffer.append(metrics)

    def flush(self) -> None:
        if not self._buffer:
            return
        rows = [asdict(m) for m in self._buffer]
        with open(self._csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            if not self._headers_written:
                writer.writeheader()
                self._headers_written = True
            writer.writerows(rows)
        self._buffer.clear()

    def export_summary(self) -> Path | None:
        """Genera emergence_summary.json con estadísticas agregadas de toda la serie."""
        self.flush()
        if not self._csv_path.exists():
            return None
        with open(self._csv_path, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        if not rows:
            return None

        def col_stats(key: str) -> dict:
            vals = [float(r[key]) for r in rows if r.get(key) not in (None, "")]
            if not vals:
                return {}
            mean = sum(vals) / len(vals)
            std  = (sum((v - mean) ** 2 for v in vals) / len(vals)) ** 0.5
            return {
                "mean":  round(mean, 6),
                "std":   round(std, 6),
                "min":   round(min(vals), 6),
                "max":   round(max(vals), 6),
                "final": round(vals[-1], 6),
            }

        summary = {
            "n_days":         len(rows),
            "kl_mean":        col_stats("kl_mean"),
            "kl_max":         col_stats("kl_max"),
            "vfe_global":     col_stats("vfe_global"),
            "vfe_tribe_mean": col_stats("vfe_tribe_mean"),
            "imi":            col_stats("imi"),
            "n_alive":        col_stats("n_alive"),
            "n_tribes":       col_stats("n_tribes"),
            "n_structures":   col_stats("n_structures"),
        }

        out = self._dir / "emergence_summary.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        return out
