import os

class ObsidianWriter:
    """Generates gorgeous, premium-styled markdown files in the Obsidian vault.

    Uses visual unicode progress bars (▓▓▓▓░░░░) and tables to represent agent states,
    social networks, the collective unconscious, active myths, and simulation logs.
    """
    def __init__(self, vault_path: str = "vault"):
        self.vault_path = vault_path
        self.personas_path = os.path.join(vault_path, "Personas")
        self.colectivo_path = os.path.join(vault_path, "Colectivo")
        self.meta_path = os.path.join(vault_path, "Meta")
        self.tribus_path = os.path.join(vault_path, "Tribus")

    def _ensure_dirs(self) -> None:
        """Creates the vault subdirectory structure if it doesn't exist."""
        os.makedirs(self.personas_path, exist_ok=True)
        os.makedirs(self.colectivo_path, exist_ok=True)
        os.makedirs(self.meta_path, exist_ok=True)
        os.makedirs(self.tribus_path, exist_ok=True)

    def generate_progress_bar(self, value: float, length: int = 10) -> str:
        """Generates a visual unicode progress bar.
        
        Args:
            value: Float between 0.0 and 1.0.
            length: Integer representing number of characters in the bar.
            
        Returns:
            A string containing the visual bar.
        """
        val = max(0.0, min(1.0, float(value)))
        filled = int(round(length * val))
        empty = length - filled
        return "▓" * filled + "░" * empty

    def write_agent(self, agent, social_network) -> None:
        """Generates and writes a premium stylized note for an agent: Personas/{agent_id}.md.
        
        Args:
            agent: Agent instance.
            social_network: SocialNetwork instance.
        """
        self._ensure_dirs()
        
        # 1. Frontmatter YAML
        frontmatter = [
            "---",
            f"id: {agent.id}",
            f"nombre: {agent.nombre}",
            f"rol: {agent.rol}",
            f"edad: {agent.edad}",
            f"sexo: {agent.sexo}",
            f"is_alive: {agent.is_alive}",
            f"posicion: [{agent.posicion[0]}, {agent.posicion[1]}]",
            f"humor: {agent.humor:.3f}",
            f"energia: {agent.energia:.3f}",
            f"ansiedad: {agent.ansiedad:.3f}",
            "needs:",
            f"  hambre: {agent.needs.hambre:.3f}",
            f"  fatiga: {agent.needs.fatiga:.3f}",
            f"  sed: {agent.needs.sed:.3f}",
            f"  sociabilidad: {agent.needs.sociabilidad:.3f}",
            f"arquetipo_dominante: {agent.arquetipo_dominante}",
            f"estado_conductual: {agent.estado_conductual or 'ninguno'}",
        ]
        
        # Add archetypes
        frontmatter.append("arquetipos:")
        for arch_name in ["self", "persona", "sombra", "anima_animus", "heroe", "sabio", "trickster", "madre", "padre", "nino_divino", "gobernante", "rebelde"]:
            val_name = "self_" if arch_name == "self" else arch_name
            val = getattr(agent.archetypes, val_name, 0.5)
            frontmatter.append(f"  {arch_name}: {val:.3f}")
            
        frontmatter.append("---")
        frontmatter_str = "\n".join(frontmatter) + "\n"

        # 2. Body Markdown
        vital_status = "🟢 Conectado / Vivo" if agent.is_alive else "💀 Desconectado / Fallecido"
        
        body = [
            f"# 👤 Persona: {agent.nombre}",
            "",
            f"> **Rol:** `{agent.rol}` | **Edad:** {agent.edad} | **Sexo:** {agent.sexo} | **Ubicación:** `{agent.posicion}`",
            f"> **Estado Vital:** **{vital_status}**",
            "",
            "---",
            "",
            "## 📊 Estado Psicobiológico",
            "",
            "### Capa Emocional",
            "| Métrica | Visual | Valor |",
            "| :--- | :---: | :---: |",
            f"| **Humor** | `[{self.generate_progress_bar(agent.humor)}]` | {agent.humor:.2f} |",
            f"| **Energía** | `[{self.generate_progress_bar(agent.energia)}]` | {agent.energia:.2f} |",
            f"| **Ansiedad** | `[{self.generate_progress_bar(agent.ansiedad)}]` | {agent.ansiedad:.2f} |",
            "",
            "### Necesidades Biológicas",
            "| Necesidad | Visual | Valor | Estado |",
            "| :--- | :---: | :---: | :--- |",
            f"| **Hambre** | `[{self.generate_progress_bar(agent.needs.hambre)}]` | {agent.needs.hambre:.2f} | {'⚠️ Alerta / Crítico' if agent.needs.hambre >= 0.8 else '🟢 Saciado'} |",
            f"| **Sed** | `[{self.generate_progress_bar(agent.needs.sed)}]` | {agent.needs.sed:.2f} | {'⚠️ Alerta / Crítico' if agent.needs.sed >= 0.8 else '🟢 Hidratado'} |",
            f"| **Fatiga** | `[{self.generate_progress_bar(agent.needs.fatiga)}]` | {agent.needs.fatiga:.2f} | {'⚠️ Alerta / Crítico' if agent.needs.fatiga >= 0.8 else '🟢 Descansado'} |",
            f"| **Sociabilidad** | `[{self.generate_progress_bar(agent.needs.sociabilidad)}]` | {agent.needs.sociabilidad:.2f} | {'⚠️ Aislado' if agent.needs.sociabilidad >= 0.8 else '🟢 Conectado'} |",
            "",
            "---",
            "",
            "## 🧠 Perfil Psicológico",
            "",
            "### Capa Jungiana: Vector de Arquetipos",
            "| Arquetipo | Fuerza | Barra Visual |",
            "| :--- | :---: | :--- |",
        ]

        # Add arquetipos with progress bars
        for arch_name in ["self", "persona", "sombra", "anima_animus", "heroe", "sabio", "trickster", "madre", "padre", "nino_divino", "gobernante", "rebelde"]:
            val_name = "self_" if arch_name == "self" else arch_name
            val = getattr(agent.archetypes, val_name, 0.5)
            bar = self.generate_progress_bar(val, length=12)
            arch_cap = arch_name.replace("_", " ").capitalize()
            body.append(f"| **{arch_cap}** | `{val:.3f}` | `{bar}` |")

        # Complexes
        body.extend([
            "",
            "### Complejos Activos",
            "| Complejo | Intensidad | Barra Visual | Estado |",
            "| :--- | :---: | :--- | :---: |"
        ])
        
        for cmp_name in ["abandono", "inferioridad", "poder", "culpa", "materno", "trascendencia"]:
            val = getattr(agent.complexes, cmp_name, 0.3)
            bar = self.generate_progress_bar(val, length=10)
            cmp_cap = cmp_name.capitalize()
            is_active = cmp_name in agent.complexes.activos
            status = "🔥 Activo" if is_active else "💤 Inactivo"
            body.append(f"| {cmp_cap} | `{val:.2f}` | `{bar}` | {status} |")

        # 3. Social Network
        body.extend([
            "",
            "---",
            "",
            "## 👥 Red Social e Interacciones",
            "",
            "### Vínculos Emocionales",
            "| Agente Relacionado | Vínculo | Visual Vínculo | Entrelazado |",
            "| :--- | :---: | :---: | :---: |"
        ])

        relations_found = False
        if social_network.graph.has_node(agent.id):
            for target_id in sorted(social_network.graph.successors(agent.id)):
                bond = social_network.get_bond(agent.id, target_id)
                entangled = social_network.are_entangled(agent.id, target_id)
                entangled_str = "⚛️ Entrelazado" if entangled else "Ninguno"
                
                # Render bond as a bar between -1.0 and 1.0 (normalize to 0-1)
                norm_val = (bond + 1.0) / 2.0
                bond_bar = self.generate_progress_bar(norm_val, length=10)
                
                body.append(f"| [[{target_id}]] | `{bond:+.2f}` | `{bond_bar}` | {entangled_str} |")
                relations_found = True

        if not relations_found:
            body.append("| *Ninguno* | - | - | - |")

        # 4. Dreams
        body.extend([
            "",
            "---",
            "",
            "## 💤 Bitácora Onírica (Últimos Sueños)",
            ""
        ])
        if agent.dreams:
            for dream in agent.dreams:
                body.append(f"- **Día {dream.dia}:** Soñó con `'{dream.simbolo}'` (arquetipo `{dream.arquetipo}`).")
                body.append(f"  - *Insight:* {dream.insight}")
        else:
            body.append("*Aún no se registran experiencias oníricas en esta psique.*")

        # 5. Episodic Log
        body.extend([
            "",
            "---",
            "",
            "## 📖 Crónicas Episódicas (Memoria de Acontecimientos)",
            ""
        ])
        if agent.episodic_log:
            for log_entry in agent.episodic_log:
                body.append(f"- {log_entry}")
        else:
            body.append("*La memoria de este agente está en blanco.*")

        full_content = frontmatter_str + "\n".join(body) + "\n"
        
        file_path = os.path.join(self.personas_path, f"{agent.id}.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_content)

    def write_collective_field(self, field) -> None:
        """Writes Colectivo/Inconsciente_Colectivo.md describing the global symbols and pressure.
        
        Args:
            field: CollectiveField instance.
        """
        self._ensure_dirs()
        
        pressure_bar = self.generate_progress_bar(field.emotional_pressure, length=15)
        
        body = [
            "# 🌌 Inconsciente Colectivo",
            "",
            f"> **Presión Emocional Global:** `{field.emotional_pressure:.3f}`",
            f"> `[{pressure_bar}]`",
            "",
            "---",
            "",
            "## 🔮 Cargas Meméticas y Símbolos Activos",
            "",
            "Representa la concentración de energía psíquica en los símbolos universales de la simulación.",
            "",
            "| Símbolo | Fuerza | Barra Visual |",
            "| :--- | :---: | :--- |"
        ]

        # Sorted by strength descending
        sorted_symbols = sorted(field.symbols.items(), key=lambda x: x[1], reverse=True)
        for sym_name, weight in sorted_symbols:
            bar = self.generate_progress_bar(weight, length=12)
            sym_cap = sym_name.capitalize()
            body.append(f"| **{sym_cap}** | `{weight:.3f}` | `{bar}` |")

        full_content = "\n".join(body) + "\n"
        
        file_path = os.path.join(self.colectivo_path, "Inconsciente_Colectivo.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_content)

    def write_mythology(self, mythology_engine, agents) -> None:
        """Writes Colectivo/Mitologia.md detailing crystalized global narratives.
        
        Args:
            mythology_engine: MythologyEngine instance.
            agents: Dict of agent instances.
        """
        self._ensure_dirs()
        
        body = [
            "# 📜 Registro de Mitología y Tabús",
            "",
            "Los mitos son cristalizaciones de alta intensidad en el inconsciente colectivo que otorgan roles forzosos y modificadores persistentes de conducta.",
            "",
            "---",
            "",
            "## ⚔️ Mito Activo: Héroe vs Monstruo",
            ""
        ]

        hero_id, monster_id = mythology_engine.get_myth_hero_monster()
        
        # Find active myth
        active_myth = None
        for myth in mythology_engine.active_myths:
            if myth.name == "heroe_vs_monstruo" and myth.active:
                active_myth = myth
                break

        if active_myth and hero_id and monster_id:
            hero_name = agents[hero_id].nombre if hero_id in agents else hero_id
            monster_name = agents[monster_id].nombre if monster_id in agents else monster_id

            body.extend([
                "⚠️ **¡Mito Cristalizado Activo!**",
                "",
                f"- **Día de Cristalización:** Día `{active_myth.day_crystallized}`",
                f"- **Héroe Asignado:** [[{hero_id}]] ({hero_name})",
                f"- **Monstruo / Chivo Expiatorio:** [[{monster_id}]] ({monster_name})",
                "",
                "### 🎭 Impacto Psicológico",
                "- **El Héroe:** Recibe bonificaciones emocionales continuas (+0.05 Humor, -0.05 Ansiedad por día).",
                "- **El Monstruo:** Experimenta una carga de pánico y aislamiento (+0.08 Ansiedad, -0.05 Humor por día).",
            ])
        else:
            body.append("> *No hay ningún mito del Héroe vs Monstruo cristalizado actualmente en el inconsciente colectivo.*")

        # History of all myths
        body.extend([
            "",
            "---",
            "",
            "## 📜 Historial de Cristalizaciones Mitológicas",
            "",
            "| Mito | Estado | Protagonistas | Sincronía |",
            "| :--- | :---: | :--- | :---: |"
        ])
        
        if mythology_engine.active_myths:
            for myth in mythology_engine.active_myths:
                myth_name = myth.name.capitalize()
                status = "🟢 Activo" if myth.active else "🔴 Disuelto"

                h_id = myth.protagonista_id
                m_id = myth.antagonista_id
                if h_id and m_id:
                    protags = f"Héroe: [[{h_id}]], Monstruo: [[{m_id}]]"
                else:
                    protags = "N/A"

                day = myth.day_crystallized
                body.append(f"| {myth_name} | {status} | {protags} | Día {day} |")
        else:
            body.append("| *Ninguno* | - | - | - |")

        full_content = "\n".join(body) + "\n"
        
        file_path = os.path.join(self.colectivo_path, "Mitologia.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_content)

    def write_tribes(self, tribe_manager, agents, dia: int) -> None:
        """Writes Tribus/{tribe_id}.md for each active tribe.

        Args:
            tribe_manager: TribeManager instance.
            agents: Dict of agent instances.
            dia: Current simulated day.
        """
        self._ensure_dirs()

        for tribe_id, member_ids in tribe_manager.tribes.items():
            display_name = tribe_manager.get_tribe_display_name(tribe_id, agents)
            local_field  = tribe_manager.local_fields.get(tribe_id)
            local_myths  = tribe_manager.local_myths.get(tribe_id)
            alive_members = [agents[aid] for aid in member_ids if aid in agents and agents[aid].is_alive]

            body = [
                f"# 🏕️ {display_name}",
                "",
                f"> **Día:** `{dia}` | **Miembros vivos:** `{len(alive_members)}`",
                "",
                "---",
                "",
                "## 👥 Composición de la Tribu",
                "",
                "| Agente | Rol | Edad | Arquetipo Dominante |",
                "| :--- | :--- | :---: | :--- |",
            ]
            for agent in sorted(alive_members, key=lambda a: a.nombre):
                body.append(f"| [[{agent.id}]] ({agent.nombre}) | {agent.rol} | {agent.edad} | {agent.arquetipo_dominante} |")

            # Campo colectivo local
            body.extend([
                "",
                "---",
                "",
                "## 🌀 Inconsciente Colectivo Local",
                "",
            ])
            if local_field is not None:
                pressure_bar = self.generate_progress_bar(local_field.emotional_pressure, length=12)
                body.append(f"> **Presión emocional:** `{local_field.emotional_pressure:.3f}` `[{pressure_bar}]`")
                body.extend([
                    "",
                    "| Símbolo | Fuerza | Barra Visual |",
                    "| :--- | :---: | :--- |",
                ])
                for sym, val in sorted(local_field.symbols.items(), key=lambda x: x[1], reverse=True):
                    bar = self.generate_progress_bar(val, length=10)
                    body.append(f"| **{sym.capitalize()}** | `{val:.3f}` | `{bar}` |")
            else:
                body.append("> *Campo sin inicializar.*")

            # Mitología local
            body.extend([
                "",
                "---",
                "",
                "## 📜 Mitología Local",
                "",
            ])
            if local_myths and local_myths.active_myths:
                for myth in local_myths.active_myths:
                    status = "🟢 Activo" if myth.active else "🔴 Disuelto"
                    name   = myth.name.replace("_", " ").capitalize()
                    day_c  = myth.day_crystallized
                    body.append(f"- **{name}** — {status} (Día {day_c})")
            else:
                body.append("> *Ningún mito cristalizado aún en esta tribu.*")

            full_content = "\n".join(body) + "\n"
            file_path = os.path.join(self.tribus_path, f"{tribe_id}.md")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(full_content)

    def write_cultura(self, culture_engine, agents, dia: int) -> None:
        """Writes Colectivo/Cultura_Material.md with all active structures and their auras."""
        self._ensure_dirs()

        _TIPO_EMOJI = {"totem": "🗿", "altar": "⛩️", "muralla": "🧱", "hoguera": "🔥"}
        _TIPO_NOMBRE = {"totem": "Tótem", "altar": "Altar", "muralla": "Muralla", "hoguera": "Hoguera Sagrada"}

        body = [
            "# 🏛️ Cultura Material",
            "",
            f"> **Día:** `{dia}` | **Estructuras activas:** `{len(culture_engine.structures)}`",
            "",
            "---",
            "",
            "## 🏗️ Registro de Estructuras",
            "",
            "| Tipo | Tribu | Coordenada | Día erigida | Radio | Aura Humor | Aura Ansiedad |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :---: |",
        ]

        if culture_engine.structures:
            for s in sorted(culture_engine.structures, key=lambda x: x.day_built):
                emoji = _TIPO_EMOJI.get(s.tipo, "")
                nombre = _TIPO_NOMBRE.get(s.tipo, s.tipo)
                humor_str = f"{s.humor_d:+.3f}" if s.humor_d else "—"
                ans_str   = f"{s.ansiedad_d:+.3f}" if s.ansiedad_d else "—"
                dur_str   = f"(exp. día {s.day_built + s.duration})" if s.duration else ""
                body.append(
                    f"| {emoji} {nombre} | `{s.tribe_id}` | `{s.coord}` "
                    f"| Día {s.day_built} {dur_str}| {s.radio} hex | `{humor_str}` | `{ans_str}` |"
                )
        else:
            body.append("| *Ninguna estructura erigida aún.* | — | — | — | — | — | — |")

        # Detalle por tipo
        tipos_presentes = list({s.tipo for s in culture_engine.structures})
        if tipos_presentes:
            body.extend(["", "---", "", "## 🌀 Auras por Tipo de Estructura", ""])
            for tipo in sorted(tipos_presentes):
                emoji  = _TIPO_EMOJI.get(tipo, "")
                nombre = _TIPO_NOMBRE.get(tipo, tipo)
                count  = sum(1 for s in culture_engine.structures if s.tipo == tipo)
                ejemplar = next(s for s in culture_engine.structures if s.tipo == tipo)
                arch_str = ", ".join(f"{k}: +{v:.4f}/día" for k, v in ejemplar.arch_push.items())
                body.extend([
                    f"### {emoji} {nombre} ({count} activa{'s' if count != 1 else ''})",
                    f"- **Radio:** {ejemplar.radio} hexes",
                    f"- **Para miembros:** humor `{ejemplar.humor_d:+.3f}`, ansiedad `{ejemplar.ansiedad_d:+.3f}`/día",
                    f"- **Para forasteros:** humor `{ejemplar.humor_d_ext:+.3f}`, ansiedad `{ejemplar.ansiedad_d_ext:+.3f}`/día",
                    f"- **Impulso arquetípico:** {arch_str or '—'}",
                    "",
                ])

        full_content = "\n".join(body) + "\n"
        file_path = os.path.join(self.colectivo_path, "Cultura_Material.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_content)

    def write_simulation_log(self, death_log, current_dia: int) -> None:
        """Writes Meta/Simulacion_Log.md acting as a history timeline of simulation events.
        
        Args:
            death_log: List of death logs from AgentCore.
            current_dia: Current simulation day.
        """
        self._ensure_dirs()
        
        body = [
            "# 📋 Bitácora Global de la Simulación",
            "",
            f"**Última Sincronización:** Día `{current_dia}`",
            "",
            "---",
            "",
            "## 📅 Registro de Acontecimientos Históricos",
            "",
            "Acontecimientos existenciales y decesos registrados a lo largo del ciclo vital:",
            "",
            "| Día | Evento | Descripción |",
            "| :---: | :--- | :--- |"
        ]

        if death_log:
            sorted_deaths = sorted(death_log, key=lambda x: x.get("dia", 0))
            for death in sorted_deaths:
                dia = death.get("dia", 0)
                agent_id = death.get("agent_id", "")
                nombre = death.get("nombre", "")
                causa = death.get("causa", "causas desconocidas")
                body.append(f"| **Día {dia}** | 💀 Deceso | [[{agent_id}]] ({nombre}) falleció a causa de `{causa}`. |")
        else:
            body.append("| - | 🌱 Inicio | La simulación ha comenzado sin decesos registrados. |")

        full_content = "\n".join(body) + "\n"

        file_path = os.path.join(self.meta_path, "Simulacion_Log.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_content)

    # ── F3: Crónica de eventos culturales ────────────────────────────────────

    def write_cronica(self, tribe_manager, dia: int, n_events: int = 50) -> None:
        """F3 — Exporta los últimos N eventos de CulturalMemory a vault/Colectivo/Cronica.md."""
        self._ensure_dirs()

        all_events: list[dict] = []
        for tribe_id, cmem in tribe_manager.cultural_memories.items():
            for rec in cmem.records:
                all_events.append({
                    "dia":    rec.dia_origen,
                    "tipo":   rec.tipo_evento,
                    "tribe":  tribe_id,
                    "origen": rec.agente_origen,
                    "desc":   rec.descripcion_actual,
                    "intens": rec.intensidad_emocional,
                    "trans":  rec.n_transmisiones,
                })

        all_events.sort(key=lambda e: -e["dia"])
        shown = all_events[:n_events]

        tipo_icons = {
            "nacimiento": "👶", "construccion": "🏛️", "ruina": "🪨",
            "muerte": "💀", "catastrofe": "⚡", "taboo": "🚫",
            "deposicion": "👑", "vinculo": "🔗", "conocimiento": "📖",
            "depredador": "🐺",
        }

        lines = [
            "# 📜 Crónica Cultural",
            "",
            f"_Exportada en el Día {dia} — últimos {n_events} eventos registrados_",
            "",
            "---",
            "",
        ]
        for ev in shown:
            icon = next(
                (v for k, v in tipo_icons.items() if k in ev["tipo"]),
                "📌",
            )
            intensidad_bar = "█" * int(ev["intens"] * 10) + "░" * (10 - int(ev["intens"] * 10))
            lines += [
                f"### {icon} Día {ev['dia']} — {ev['tipo'].replace('_', ' ').title()}",
                f"**Tribu:** `{ev['tribe']}` · **Agente:** {ev['origen']} "
                f"· **Intensidad:** `{intensidad_bar}` ({ev['intens']:.2f})",
                f"**Transmisiones:** {ev['trans']}",
                f"> {ev['desc']}",
                "",
            ]

        if not shown:
            lines.append("_Sin eventos culturales registrados aún._")

        content = "\n".join(lines) + "\n"
        path = os.path.join(self.colectivo_path, "Cronica.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
