import os
import yaml

class ObsidianReader:
    """Reads and parses YAML frontmatter from Obsidian vault markdown files.
    
    This enables external vault modifications or manual configurations to be synchronized 
    back into the core Python simulation.
    """
    def __init__(self, vault_path: str = "vault"):
        self.vault_path = vault_path
        self.personas_path = os.path.join(vault_path, "Personas")

    def parse_frontmatter(self, file_path: str) -> dict:
        """Parses the YAML frontmatter from a markdown file.
        
        Args:
            file_path: The absolute or relative path to the markdown file.
            
        Returns:
            A dictionary containing the parsed YAML data, or empty dict if invalid.
        """
        if not os.path.exists(file_path):
            return {}
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except IOError:
            return {}
            
        # Frontmatter must start with ---
        if not content.startswith("---"):
            return {}
            
        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}
            
        yaml_content = parts[1]
        try:
            return yaml.safe_load(yaml_content) or {}
        except Exception:
            return {}

    def read_agent(self, agent_id: str) -> dict:
        """Reads a specific agent's frontmatter from vault/Personas/{agent_id}.md.
        
        Args:
            agent_id: The ID of the agent (e.g. 'kairos').
            
        Returns:
            A dictionary of parsed frontmatter properties.
        """
        file_path = os.path.join(self.personas_path, f"{agent_id}.md")
        return self.parse_frontmatter(file_path)

    def read_all_agents(self) -> dict[str, dict]:
        """Reads all agents' frontmatter from vault/Personas/.
        
        Returns:
            A dictionary mapping agent_id -> parsed frontmatter dict.
        """
        agents_data = {}
        if not os.path.exists(self.personas_path):
            return agents_data
            
        try:
            for filename in os.listdir(self.personas_path):
                if filename.endswith(".md"):
                    agent_id = filename[:-3]
                    data = self.read_agent(agent_id)
                    if data:
                        agents_data[agent_id] = data
        except OSError:
            pass
        return agents_data
