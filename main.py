#!/usr/bin/env python3
"""main.py — Llave maestra de PSYCHE SIMULACRA."""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Confirm, Prompt
    from rich.table import Table
    from rich import box
except ImportError:
    print("ERROR: instalar 'rich' antes de usar el launcher:")
    print("  pip install rich")
    sys.exit(1)

DB_PATH         = ROOT / "data" / "db" / "simulation.db"
CHECKPOINTS_DIR = ROOT / "data" / "checkpoints"
ARCHIVE_DIR     = ROOT / "data" / "archive"
VAULT_DIR       = ROOT / "vault"
SEEDS_DIR       = ROOT / "data" / "seeds"
SEEDS_FILE      = SEEDS_DIR / "initial_personas.yaml"
VISUALIZER      = ROOT / "scripts" / "visualizer.py"
DASHBOARD       = ROOT / "dashboard" / "app.py"


# ── Estado ────────────────────────────────────────────────────────────────────

def _read_state() -> dict | None:
    candidates = sorted(CHECKPOINTS_DIR.glob("checkpoint_*.json"), reverse=True)
    if not candidates:
        return None
    try:
        with open(candidates[0], encoding="utf-8") as f:
            data = json.load(f)
        agents_list = data.get("agentes", {}).get("agents", [])
        total = len(agents_list)
        alive = sum(1 for a in agents_list if a.get("is_alive", False))
        return {
            "dia":       data.get("dia_simulado", 0),
            "vivos":     alive,
            "total":     total,
            "timestamp": data.get("timestamp_real", "")[:19].replace("T", " "),
        }
    except Exception:
        return None


# ── Archivo ───────────────────────────────────────────────────────────────────

def _next_archive_name() -> str:
    """Devuelve 'Simulacion_01', 'Simulacion_02', etc. según las que ya existan."""
    import re
    existing = [
        d.name for d in ARCHIVE_DIR.iterdir()
        if d.is_dir() and re.fullmatch(r"Simulacion_\d+", d.name)
    ] if ARCHIVE_DIR.exists() else []
    nums = [int(n.split("_")[1]) for n in existing] if existing else [0]
    return f"Simulacion_{max(nums) + 1:02d}"


def _archive(state: dict) -> Path:
    """Copia DB, checkpoints y vault a data/archive/Simulacion_XX/."""
    dest = ARCHIVE_DIR / _next_archive_name()
    dest.mkdir(parents=True, exist_ok=True)

    # Base de datos
    if DB_PATH.exists():
        db_dest = dest / "db"
        db_dest.mkdir()
        shutil.copy2(DB_PATH, db_dest / DB_PATH.name)
        for ext in ("-wal", "-shm"):
            wal = Path(str(DB_PATH) + ext)
            if wal.exists():
                shutil.copy2(wal, db_dest / wal.name)

    # Checkpoints
    if CHECKPOINTS_DIR.exists():
        cp_dest = dest / "checkpoints"
        cp_dest.mkdir()
        for f in CHECKPOINTS_DIR.glob("checkpoint_*.json"):
            shutil.copy2(f, cp_dest / f.name)

    # Vault de Obsidian
    if VAULT_DIR.exists():
        shutil.copytree(VAULT_DIR, dest / "vault", dirs_exist_ok=True)

    # Meta del archivo
    with open(dest / "meta.json", "w", encoding="utf-8") as f:
        json.dump({
            "dia_final":    state["dia"],
            "vivos":        state["vivos"],
            "total":        state["total"],
            "archivado_en": datetime.now().isoformat(),
        }, f, indent=2, ensure_ascii=False)

    return dest


# ── Helpers de UI ─────────────────────────────────────────────────────────────

def _count_agents(yaml_path: Path) -> int:
    """Devuelve el número de agentes en un archivo YAML de semillas."""
    try:
        import yaml as _yaml
        with open(yaml_path, encoding="utf-8") as f:
            data = _yaml.safe_load(f)
        return len(data.get("agents", []))
    except Exception:
        return 0


def _select_seeds_file(console: Console) -> Path:
    """Muestra los archivos de semillas disponibles y devuelve el elegido."""
    candidates = sorted(SEEDS_DIR.glob("*.yaml"))
    if not candidates:
        return SEEDS_FILE
    if len(candidates) == 1:
        return candidates[0]

    console.print("\n[bold]Archivos de semillas disponibles:[/bold]")
    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    t.add_column(style="bold cyan", width=4)
    t.add_column()
    t.add_column(style="dim")
    for i, f in enumerate(candidates):
        n = _count_agents(f)
        t.add_row(f"[{i + 1}]", f.name, f"{n} agentes")
    console.print(t)

    choice = Prompt.ask(
        "Seleccionar semillas",
        choices=[str(i + 1) for i in range(len(candidates))],
        default="1",
        console=console,
    )
    return candidates[int(choice) - 1]


def _ask_days(console: Console, default: str = "0") -> int | None:
    """Devuelve None para 'hasta extinción', o el número de días."""
    raw = Prompt.ask(
        "Días a simular [dim](0 = hasta extinción total)[/dim]",
        default=default,
        console=console,
    )
    try:
        d = int(raw)
        return None if d <= 0 else d
    except ValueError:
        return None


def _ask_n_agents(console: Console, yaml_path: Path) -> int | None:
    """Pregunta cuántos agentes usar; devuelve None si se usa el YAML tal cual."""
    default_n = _count_agents(yaml_path)
    raw = Prompt.ask(
        f"Número de agentes [dim](0 = usar YAML tal cual, actualmente {default_n})[/dim]",
        default="0",
        console=console,
    )
    try:
        n = int(raw)
        return None if n <= 0 or n == default_n else n
    except ValueError:
        return None


def _generate_seeds(console: Console, n: int, seed: int) -> Path:
    """Genera un YAML de semillas con N agentes usando generate_personas.py."""
    out = SEEDS_DIR / f"_session_{n}ag_{seed}s.yaml"
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "generate_personas.py"),
        "--n", str(n),
        "--seed", str(seed),
        "--output", str(out),
    ]
    console.print(f"[cyan]Generando {n} agentes (seed={seed})...[/cyan]")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        console.print(f"[red]Error generando agentes:[/red]\n{result.stderr}")
        raise RuntimeError("generate_personas.py falló")
    console.print(f"[green]Semillas generadas:[/green] {out.name}")
    return out


def _ask_narrative_config(console: Console) -> tuple[bool, str]:
    """Pregunta si activar la narrativa LLM y qué modelo usar.
    Devuelve (enabled, model_name)."""
    enabled = Confirm.ask(
        "¿Activar narrativa LLM (Ollama)?  [dim]requiere Ollama instalado[/dim]",
        default=True,
        console=console,
    )
    model = "llama3.2"
    if enabled:
        model = Prompt.ask(
            "Modelo Ollama",
            default=os.environ.get("OLLAMA_MODEL", "llama3.2"),
            console=console,
        )
    return enabled, model


def _print_result(console: Console, runner) -> None:
    vivos = runner.alive_count
    total = len(runner.agents.agents)
    dia   = runner.current_dia
    if vivos == 0:
        console.print(f"\n[bold red]EXTINCIÓN TOTAL[/bold red] en el Día {dia}.")
    else:
        console.print(
            f"\n[green]Checkpoint guardado.[/green]  "
            f"Día [bold]{dia}[/bold] · Vivos: [bold]{vivos}[/bold]/{total}"
        )


# ── Acciones ──────────────────────────────────────────────────────────────────

def _action_terminal(console: Console) -> None:
    n_days = _ask_days(console)
    label  = "hasta extinción total" if n_days is None else f"{n_days} días"
    console.print(f"\n[dim]Corriendo {label}... (Ctrl+C para pausar y guardar)[/dim]\n")

    from core.simulation import SimulationRunner
    runner = SimulationRunner.resume(
        db_path        = str(DB_PATH),
        checkpoint_dir = str(CHECKPOINTS_DIR),
    )
    try:
        runner.run(n_days=n_days)
    except KeyboardInterrupt:
        pass
    _print_result(console, runner)


def _action_pygame(console: Console) -> None:
    n_days  = _ask_days(console, default="200")
    raw_fps = Prompt.ask("FPS de visualización", default="10", console=console)
    try:
        fps = max(1, int(raw_fps))
    except ValueError:
        fps = 10

    args = [
        sys.executable, str(VISUALIZER),
        "--resume",
        "--fps", str(fps),
        "--days", str(n_days or 0),
    ]
    console.print(f"\n[dim]Abriendo Pygame a {fps} fps...[/dim]\n")
    subprocess.run(args)


def _action_dashboard(console: Console) -> None:
    args = [sys.executable, "-m", "streamlit", "run", str(DASHBOARD)]

    if sys.platform == "win32":
        subprocess.Popen(
            ["cmd", "/k"] + args,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
    else:
        subprocess.Popen(args, start_new_session=True)

    console.print(
        "[green]Dashboard iniciado.[/green]  "
        "Abrí [bold cyan]http://localhost:8501[/bold cyan] en tu navegador."
    )
    console.print("[dim](Para detenerlo cerrá la ventana de terminal del dashboard)[/dim]")


def _action_new(console: Console, state: dict | None) -> None:
    if state:
        console.print()
        console.print(Panel(
            f"[yellow]Simulación activa en el Día {state['dia']}[/yellow]\n"
            f"[bold]{state['vivos']}[/bold] / {state['total']} agentes vivos\n\n"
            f"Se archivará automáticamente antes de iniciar la nueva.",
            border_style="yellow",
            padding=(0, 2),
        ))
        if not Confirm.ask("\n¿Confirmar nueva simulación?", default=False, console=console):
            console.print("[dim]Cancelado.[/dim]")
            return

        console.print("[cyan]Archivando simulación anterior...[/cyan]")
        archive_path = _archive(state)
        console.print(f"[green]Archivada en:[/green] {archive_path.relative_to(ROOT)}\n")

    seeds_path = _select_seeds_file(console)
    console.print(f"[dim]Semillas: {seeds_path.name}[/dim]")

    raw_seed = Prompt.ask("Semilla aleatoria", default="42", console=console)
    try:
        seed = int(raw_seed)
    except ValueError:
        seed = 42

    # ── Número de agentes ──────────────────────────────────────────────────────
    n_override = _ask_n_agents(console, seeds_path)
    if n_override is not None:
        seeds_path = _generate_seeds(console, n_override, seed)

    # ── Narrativa LLM ──────────────────────────────────────────────────────────
    narrative_on, llm_model = _ask_narrative_config(console)
    os.environ["NARRATIVE_ENABLED"] = "1" if narrative_on else "0"
    os.environ["OLLAMA_MODEL"]      = llm_model

    n_days = _ask_days(console, default="0")
    console.print("\n[yellow]Iniciando nueva simulación...[/yellow]\n")

    from core.simulation import SimulationRunner
    runner = SimulationRunner.new_session(
        seed_file      = str(seeds_path),
        seed           = seed,
        db_path        = str(DB_PATH),
        checkpoint_dir = str(CHECKPOINTS_DIR),
    )
    label = "hasta extinción total" if n_days is None else f"{n_days} días"
    console.print(f"[dim]Corriendo {label}... (Ctrl+C para pausar)[/dim]\n")
    try:
        runner.run(n_days=n_days)
    except KeyboardInterrupt:
        pass
    _print_result(console, runner)


# ── Loop principal ────────────────────────────────────────────────────────────

def main() -> None:
    console = Console()

    while True:
        console.clear()
        state     = _read_state()
        has_vivos = state is not None and state["vivos"] > 0

        # Cabecera
        if state:
            if state["vivos"] == 0:
                info = f"[bold red]EXTINCIÓN TOTAL[/bold red]  Día {state['dia']:,} · 0 / {state['total']} agentes vivos"
            else:
                info = (
                    f"Día [bold cyan]{state['dia']:,}[/bold cyan] · "
                    f"[bold]{state['vivos']}[/bold] / {state['total']} agentes vivos · "
                    f"[dim]{state['timestamp']}[/dim]"
                )
        else:
            info = "[yellow]Sin simulación activa  —  no hay checkpoints[/yellow]"

        console.print(Panel(
            info,
            title="[bold magenta]✦  PSYCHE SIMULACRA[/bold magenta]",
            border_style="magenta",
            padding=(0, 2),
        ))
        console.print()

        # Menú
        t = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        t.add_column(style="bold cyan", width=4)
        t.add_column()

        if has_vivos:
            t.add_row("[1]", "Continuar en terminal  [dim](máxima velocidad)[/dim]")
            t.add_row("[2]", "Continuar en Pygame    [dim](tiempo real, con mapa)[/dim]")
        else:
            t.add_row("[dim][1][/dim]", "[dim]Continuar en terminal  (sin agentes vivos)[/dim]")
            t.add_row("[dim][2][/dim]", "[dim]Continuar en Pygame    (sin agentes vivos)[/dim]")

        t.add_row("[3]", "Abrir Dashboard Streamlit  [dim](lectura, no corre la simulación)[/dim]")

        if state:
            t.add_row("[4]", "[red]Nueva simulación[/red]  [dim](archiva la anterior antes de borrar)[/dim]")
        else:
            t.add_row("[4]", "[yellow]Primera simulación[/yellow]")

        t.add_row("[5]", "Salir")
        console.print(t)
        console.print()

        choice = Prompt.ask(
            "Opción",
            choices=["1", "2", "3", "4", "5"],
            console=console,
        )

        if choice == "1":
            if has_vivos:
                _action_terminal(console)
            else:
                console.print("[dim]No hay agentes vivos para continuar.[/dim]")
            input("\nPresioná Enter para volver al menú...")

        elif choice == "2":
            if has_vivos:
                _action_pygame(console)
            else:
                console.print("[dim]No hay agentes vivos para continuar.[/dim]")
                input("\nPresioná Enter para volver al menú...")

        elif choice == "3":
            _action_dashboard(console)
            input("\nPresioná Enter para volver al menú...")

        elif choice == "4":
            _action_new(console, state)
            input("\nPresioná Enter para volver al menú...")

        elif choice == "5":
            console.print("\n[dim]Hasta pronto.[/dim]")
            break


if __name__ == "__main__":
    main()
