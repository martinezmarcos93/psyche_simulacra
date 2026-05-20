import os
import pytest
from core.agents.agent import Agent
from core.social.network import SocialNetwork
from core.social.collective_field import CollectiveField
from core.social.mythology import MythologyEngine
from core.time import TimePoint
from core.simulation import SimulationRunner
from obsidian.reader import ObsidianReader
from obsidian.writer import ObsidianWriter
from obsidian.sync import ObsidianSync

def test_obsidian_reader(tmp_path) -> None:
    # Create a temp vault folder structure
    vault_dir = tmp_path / "vault"
    personas_dir = vault_dir / "Personas"
    personas_dir.mkdir(parents=True)
    
    agent_file = personas_dir / "kairos.md"
    agent_file.write_text("""---
id: kairos
nombre: Kairos
rol: heroe
edad: 30
sexo: M
is_alive: true
posicion: [2, 3]
humor: 0.85
energia: 0.90
ansiedad: 0.15
needs:
  hambre: 0.10
  fatiga: 0.20
  sed: 0.05
  sociabilidad: 0.30
arquetipos:
  self: 0.80
  persona: 0.75
  sombra: 0.10
  anima_animus: 0.60
  heroe: 0.95
---
# Body content
""", encoding="utf-8")
    
    reader = ObsidianReader(vault_path=str(vault_dir))
    data = reader.read_agent("kairos")
    
    assert data["id"] == "kairos"
    assert data["nombre"] == "Kairos"
    assert data["rol"] == "heroe"
    assert data["posicion"] == [2, 3]
    assert data["needs"]["hambre"] == 0.10
    assert data["arquetipos"]["heroe"] == 0.95
    
    all_agents = reader.read_all_agents()
    assert "kairos" in all_agents
    assert all_agents["kairos"]["nombre"] == "Kairos"

def test_obsidian_writer(tmp_path) -> None:
    vault_dir = tmp_path / "vault"
    writer = ObsidianWriter(vault_path=str(vault_dir))
    
    # Create dummy agent and social network
    agent = Agent(agent_id="moros", nombre="Moros", posicion=(1, 5), rol="monstruo")
    agent.humor = 0.40
    agent.energia = 0.65
    agent.ansiedad = 0.70
    agent.needs.hambre = 0.50
    agent.needs.fatiga = 0.35
    agent.needs.sed = 0.12
    agent.needs.sociabilidad = 0.80
    agent.episodic_log.append("Día 1: Se sintió solo en la oscuridad.")
    agent.episodic_log.append("Día 2: Soñó con un abismo profundo.")
    
    network = SocialNetwork()
    network.add_agent("moros")
    network.add_agent("kairos")
    network.set_bond("moros", "kairos", 0.75)
    network.entangle("moros", "kairos")
    
    writer.write_agent(agent, network)
    
    agent_file = vault_dir / "Personas" / "moros.md"
    assert agent_file.exists()
    
    content = agent_file.read_text(encoding="utf-8")
    assert "id: moros" in content
    assert "nombre: Moros" in content
    assert "posicion: [1, 5]" in content
    assert "Día 1: Se sintió solo en la oscuridad." in content
    assert "⚛️ Entrelazado" in content
    assert "▓" in content

def test_collective_and_mythology_writing(tmp_path) -> None:
    vault_dir = tmp_path / "vault"
    writer = ObsidianWriter(vault_path=str(vault_dir))
    
    field = CollectiveField()
    field.symbols["heroe"] = 0.80
    field.symbols["sombra"] = 0.70
    field.emotional_pressure = 0.45
    
    writer.write_collective_field(field)
    
    collective_file = vault_dir / "Colectivo" / "Inconsciente_Colectivo.md"
    assert collective_file.exists()
    content = collective_file.read_text(encoding="utf-8")
    assert "🌌 Inconsciente Colectivo" in content
    assert "Heroe" in content
    assert "▓" in content
    
    mythology = MythologyEngine()
    mythology.active_myths.append({
        "name": "heroe_vs_monstruo",
        "active": True,
        "day_crystallized": 3,
        "hero_id": "kairos",
        "monster_id": "moros"
    })
    
    agents = {
        "kairos": Agent(agent_id="kairos", nombre="Kairos", posicion=(2, 3)),
        "moros": Agent(agent_id="moros", nombre="Moros", posicion=(1, 5))
    }
    
    writer.write_mythology(mythology, agents)
    
    mythology_file = vault_dir / "Colectivo" / "Mitologia.md"
    assert mythology_file.exists()
    content_myth = mythology_file.read_text(encoding="utf-8")
    assert "Mito Activo: Héroe vs Monstruo" in content_myth
    assert "[[kairos]]" in content_myth
    assert "[[moros]]" in content_myth

def test_sync_from_vault(tmp_path) -> None:
    vault_dir = tmp_path / "vault"
    sync = ObsidianSync(vault_path=str(vault_dir))
    
    # Write a modified file to vault
    personas_dir = vault_dir / "Personas"
    personas_dir.mkdir(parents=True)
    agent_file = personas_dir / "kairos.md"
    agent_file.write_text("""---
id: kairos
nombre: Kairos Modificado
rol: superheroe
edad: 32
sexo: M
is_alive: true
posicion: [4, 4]
humor: 0.99
energia: 0.99
ansiedad: 0.01
needs:
  hambre: 0.00
  fatiga: 0.00
  sed: 0.00
  sociabilidad: 0.00
arquetipos:
  heroe: 0.99
  sombra: 0.01
---
""", encoding="utf-8")
    
    agents = {
        "kairos": Agent(agent_id="kairos", nombre="Kairos Original", posicion=(2, 3))
    }
    
    sync.sync_from_vault(agents)
    
    assert agents["kairos"].nombre == "Kairos Modificado"
    assert agents["kairos"].rol == "superheroe"
    assert agents["kairos"].edad == 32
    assert agents["kairos"].humor == 0.99
    assert agents["kairos"].needs.hambre == 0.00
    assert agents["kairos"].archetypes.heroe == 0.99
    assert agents["kairos"].archetypes.sombra == 0.01

def test_simulation_integration_sync(tmp_path) -> None:
    db_path = tmp_path / "sim.db"
    cp_dir = tmp_path / "checkpoints"
    vault_dir = tmp_path / "vault"
    
    # Initialize from the seeds file
    runner = SimulationRunner.new_session(
        seed_file="data/seeds/initial_personas.yaml",
        seed=123,
        db_path=str(db_path),
        checkpoint_dir=str(cp_dir)
    )
    runner.obsidian_sync = ObsidianSync(vault_path=str(vault_dir))
    
    # Persist a day
    runner.clock._tick = 24
    tp = runner.clock.now
    runner._persist_day(tp)
    
    # Check all documents are generated
    assert (vault_dir / "Personas").exists()
    assert (vault_dir / "Colectivo" / "Inconsciente_Colectivo.md").exists()
    assert (vault_dir / "Colectivo" / "Mitologia.md").exists()
    assert (vault_dir / "Meta" / "Simulacion_Log.md").exists()
    
    # Read global log
    sim_log_content = (vault_dir / "Meta" / "Simulacion_Log.md").read_text(encoding="utf-8")
    assert "Bitácora Global de la Simulación" in sim_log_content
