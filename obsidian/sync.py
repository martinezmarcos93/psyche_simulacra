from obsidian.reader import ObsidianReader
from obsidian.writer import ObsidianWriter

class ObsidianSync:
    """Orchestrates bidirectional synchronization between the Python simulation and the Obsidian vault.
    
    Acts as the main API for the simulation loop to persist daily updates into the vault,
    and load manual frontmatter configurations on demand.
    """
    def __init__(self, vault_path: str = "vault"):
        self.vault_path = vault_path
        self.reader = ObsidianReader(vault_path)
        self.writer = ObsidianWriter(vault_path)

    def sync_day(
        self,
        dia: int,
        agents: dict,
        social_network,
        collective_field,
        mythology_engine,
        death_log:     list,
        tribe_manager = None,
    ) -> None:
        """Saves the end-of-day simulation state to the Obsidian vault markdown documents."""
        # 1. Write each agent's individual markdown note (Personas/{agent_id}.md)
        for agent in agents.values():
            self.writer.write_agent(agent, social_network)

        # 2. Write global unconscious collective field state (Colectivo/Inconsciente_Colectivo.md)
        self.writer.write_collective_field(collective_field)

        # 3. Write myth crystallization states (Colectivo/Mitologia.md)
        self.writer.write_mythology(mythology_engine, agents)

        # 4. Write simulation event and death log timeline (Meta/Simulacion_Log.md)
        self.writer.write_simulation_log(death_log, dia)

        # 5. Write per-tribe files (Tribus/{tribe_id}.md)
        if tribe_manager is not None:
            self.writer.write_tribes(tribe_manager, agents, dia)

    def sync_from_vault(self, agents: dict) -> None:
        """Reads frontmatters from the vault and updates agent psychological parameters or traits.
        
        This enables external manual modifications in Obsidian to feed back into the Python simulation.
        
        Args:
            agents: A dictionary of active agent instances in Python.
        """
        vault_data = self.reader.read_all_agents()
        for agent_id, data in vault_data.items():
            if agent_id in agents:
                agent = agents[agent_id]
                
                # Update basic metadata
                if "nombre" in data:
                    agent.nombre = str(data["nombre"])
                if "rol" in data:
                    agent.rol = str(data["rol"])
                if "edad" in data:
                    agent.edad = int(data["edad"])
                if "sexo" in data:
                    agent.sexo = str(data["sexo"])
                if "is_alive" in data:
                    agent.is_alive = bool(data["is_alive"])
                if "humor" in data:
                    agent.humor = float(data["humor"])
                if "energia" in data:
                    agent.energia = float(data["energia"])
                if "ansiedad" in data:
                    agent.ansiedad = float(data["ansiedad"])
                
                # Update needs
                if "needs" in data and isinstance(data["needs"], dict):
                    needs_data = data["needs"]
                    if "hambre" in needs_data:
                        agent.needs.hambre = float(needs_data["hambre"])
                    if "sed" in needs_data:
                        agent.needs.sed = float(needs_data["sed"])
                    if "fatiga" in needs_data:
                        agent.needs.fatiga = float(needs_data["fatiga"])
                    if "sociabilidad" in needs_data:
                        agent.needs.sociabilidad = float(needs_data["sociabilidad"])
                        
                # Update archetypes
                if "arquetipos" in data and isinstance(data["arquetipos"], dict):
                    arch_data = data["arquetipos"]
                    for arch_name, arch_val in arch_data.items():
                        val_name = "self_" if arch_name == "self" else arch_name
                        if hasattr(agent.archetypes, val_name):
                            setattr(agent.archetypes, val_name, float(arch_val))
