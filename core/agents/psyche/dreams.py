"""
DreamGrammarEngine — Motor de Sueños Generativos.

Fase 7 del ROADMAP2: reemplaza la tabla estática _SYMBOL_TABLE con un generador
composicional por capas. Cada sueño se construye desde:

    Capa 1 — Paisaje (bioma):      el entorno físico del agente colorea el escenario.
    Capa 2 — Arquetipo (dominante): el protagonista psíquico de la noche.
    Capa 3 — Complejo (activo):    el conflicto que el sueño intenta procesar.
    Capa 4 — Trauma (reciente):    heridas vivas del log episódico (últimos 7 días).
    Capa 5 — Resonancia (grupal):  símbolo compartido con agentes entrelazados.

Cada capa contribuye símbolos candidatos con pesos crecientes.
El símbolo final se muestrea del pool ponderado → sueños únicos sin repetición.

Sueños Compartidos (Entrelazamiento):
    La resonancia_grupal es inyectada desde agent_core._process_nightly_dreams()
    para agentes con bond_strength > 0.65, misma tribu + bond > 0.35, o entangled=True.
    El agente con mayor tensión arquetípica "emite" el símbolo resonante.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field


# ── Vocabularios simbólicos por capa ────────────────────────────────────────

# Capa 1: paisaje del sueño (peso 1.0)
_BIOME_SYMBOLS: dict[str, list[str]] = {
    "bosque_templado": ["árbol_sin_raíces", "sombra_que_camina", "sendero_circular", "luz_oblicua"],
    "pradera_humeda":  ["campo_interminable", "hierba_que_corta", "viento_que_borra", "horizonte_inmóvil"],
    "rio_lago":        ["corriente_que_arrastra", "fondo_que_sube", "reflejo_distorsionado", "sed_en_el_agua"],
    "montana_alta":    ["cima_en_niebla", "caída_sin_fondo", "roca_que_aplasta", "silencio_absoluto"],
    "sabana_abierta":  ["sol_que_calcina", "manada_que_huye", "tierra_resquebrajada", "sombra_ausente"],
    "pantano_costero": ["terreno_que_cede", "niebla_densa", "raíz_invisible", "olor_a_descomposición"],
    "cueva":           ["oscuridad_total", "eco_sin_origen", "salida_inexistente", "ojos_en_la_roca"],
    "valle_fertil":    ["abundancia_que_pudre", "semilla_negra", "fruto_amargo", "río_tranquilo"],
    "costa_abierta":   ["marea_que_sube", "sal_en_herida", "naufragio_lento", "horizonte_de_agua"],
    "desierto_borde":  ["arena_que_avanza", "oasis_espejismo", "huesos_propios", "calor_que_piensa"],
    "colinas_suaves":  ["descenso_inevitable", "bifurcación_sin_mapa", "piedra_que_rueda", "vista_engañosa"],
    "lago_interior":   ["profundidad_sin_fondo", "calma_antes_de_algo", "reflejo_sin_original", "agua_fría"],
    "tierra":          ["suelo_inestable", "horizonte_sin_nombre", "camino_borrado"],
}

# Capa 2: arquetipo dominante (peso 2.5)
_ARCHETYPE_SYMBOLS: dict[str, list[str]] = {
    "heroe":        ["espada_rota", "montaña_que_escalar", "monstruo_sin_forma", "victoria_vacía"],
    "sombra":       ["figura_que_sigue", "espejo_que_miente", "voz_propia_extraña", "habitación_prohibida"],
    "madre":        ["árbol_que_aprieta", "leche_amarga", "nido_que_asfixia", "río_que_nutre"],
    "padre":        ["ley_grabada_en_carne", "mano_que_cierra", "tormenta_controlada", "herencia_pesada"],
    "sabio":        ["libro_en_lengua_muerta", "estrella_que_no_guía", "pregunta_sin_respuesta", "camino_conocido"],
    "trickster":    ["puerta_que_se_mueve", "laberinto_que_ríe", "máscara_adherida", "trampa_propia"],
    "gobernante":   ["trono_vacío", "corona_que_duele", "ciudad_en_ruinas", "decisión_sin_retorno"],
    "rebelde":      ["cadena_rota_en_mano", "fuego_propio", "muro_que_no_cae", "exilio_elegido"],
    "nino_divino":  ["luz_primera", "inicio_sin_memoria", "cuna_sin_fondo", "juego_que_mata"],
    "anima_animus": ["voz_sin_cuerpo", "reflejo_que_actúa_solo", "complemento_ausente", "danza_a_solas"],
    "persona":      ["máscara_cosida_a_cara", "escenario_sin_salida", "papel_sin_actor", "aplauso_vacío"],
    "self":         ["mandala_incompleto", "centro_sin_lugar", "unión_imposible", "silencio_pleno"],
}

# Capa 3: complejo activo (peso 4.0)
_COMPLEX_SYMBOLS: dict[str, list[str]] = {
    "poder":         ["trono_que_aplasta", "arma_vuelta_hacia_sí", "victoria_convertida_en_jaula"],
    "abandono":      ["puerta_que_no_cierra", "camino_sin_fin", "grito_sin_eco", "presencia_ausente"],
    "culpa":         ["sombra_que_acusa", "herida_que_abre_sola", "manos_manchadas"],
    "inferioridad":  ["gigante_que_observa", "voz_que_no_sale", "lugar_siempre_ocupado"],
    "materno":       ["raíz_que_atrapa", "pecho_que_no_alimenta", "calor_que_asfixia"],
    "trascendencia": ["puerta_sin_llave", "luz_al_final_que_retrocede", "mandala_que_gira_solo"],
}

# Capa 4: traumas recientes — keywords del log episódico → símbolos (peso 5.0)
_TRAUMA_KEYWORDS: dict[str, list[str]] = {
    "deshidratacion": ["agua_que_huye", "labios_que_piden", "sed_con_ojos"],
    "inanicion":      ["mesa_vacía", "estómago_que_habla", "fruto_que_se_pudre"],
    "Falleció":       ["sombra_que_sigue_caminando", "nombre_que_nadie_dice", "lugar_vacío"],
    "choque_violento":["sangre_en_manos_propias", "golpe_sin_causa", "cuerpo_caído"],
    "orfandad":       ["voz_de_padre_sin_cuerpo", "cuna_vacía_en_campo_abierto"],
    "hambre":         ["fruto_prohibido", "banquete_de_sombras"],
    "conflicto":      ["espejo_roto_en_dos", "guerra_contra_uno_mismo"],
    "LIMINAL_ENCUENTRO": ["puerta_entre_mundos", "ser_sin_nombre_conocido", "arquetipo_extraño", "eco_de_otro_mundo"],
}

_DEFAULT_SYMBOL = "sombra_sin_forma"

# Plantillas de insight por tipo de procesamiento — elegidas aleatoriamente para evitar
# que dos agentes con mismo arquetipo+complejo generen texto idéntico.
_INSIGHT_TEMPLATES: dict[str, list[str]] = {
    "integracion_parcial": [
        "En {landscape}, el {dominante} encuentra tregua provisional con {wound}.",
        "Entre sombras de {landscape}, el {dominante} y {wound} coexisten sin resolverse.",
        "El {dominante} descansa en {landscape} mientras {wound} aguarda en el umbral.",
        "En {landscape}, {wound} pierde fuerza un instante — el {dominante} respira.",
        "El {dominante} y {wound} se toleran esta noche en {landscape}.",
    ],
    "amplificacion": [
        "El {landscape} amplifica la tensión del {dominante}; {wound} presiona desde adentro.",
        "El {dominante} crece desmedido en {landscape} — {wound} lo empuja sin nombre.",
        "En {landscape} el {dominante} se expande más allá del control; {wound} es el combustible.",
        "{wound} enciende el {dominante} en {landscape} hasta quemar lo que toca.",
        "En {landscape}, el {dominante} no puede contenerse — {wound} alimenta el fuego.",
    ],
    "compensacion": [
        "El {dominante} busca equilibrio en {landscape} compensando la energía de {wound}.",
        "En {landscape}, el {dominante} toma prestada la forma opuesta para alejarse de {wound}.",
        "{wound} pesa demasiado — el {dominante} cede terreno en {landscape} para no caer.",
        "En {landscape}, el {dominante} negocia con {wound} en el único idioma posible: el silencio.",
        "El {dominante} se disfraza de su contrario en {landscape}, lejos de {wound}.",
    ],
    "proyeccion": [
        "El {dominante} proyecta {wound} sobre el horizonte de {landscape}.",
        "En {landscape}, {wound} aparece en el otro — el {dominante} no se reconoce.",
        "El {dominante} ve {wound} afuera en {landscape}, donde no puede alcanzarlo.",
        "En {landscape}, {wound} tiene el rostro de otro — el {dominante} lo señala sin piedad.",
        "El {dominante} expulsa {wound} hacia {landscape}: allá afuera, entre los demás.",
    ],
}

# Pesos de cada capa en el pool de símbolos
_LAYER_WEIGHT = {
    "biome":     1.0,
    "archetype": 2.5,
    "complex":   4.0,
    "trauma":    5.0,
    "resonance": 6.0,
}

# Tipos de procesamiento onírico
_PROCESSING_TYPES = ["integracion_parcial", "amplificacion", "compensacion", "proyeccion"]

# Pares opuestos arquetípicos para compensación
_ARCHETYPE_OPPOSITES: dict[str, str] = {
    "heroe":        "sombra",
    "sombra":       "heroe",
    "madre":        "padre",
    "padre":        "madre",
    "gobernante":   "rebelde",
    "rebelde":      "gobernante",
    "persona":      "sombra",
    "sabio":        "nino_divino",
    "nino_divino":  "sabio",
    "trickster":    "persona",
    "anima_animus": "self",
    "self":         "anima_animus",
}


def _select_processing(tension: float, rng: random.Random) -> str:
    if tension > 0.25:
        return rng.choice(["amplificacion", "proyeccion"])
    if tension > 0.15:
        return rng.choice(["integracion_parcial", "compensacion"])
    return "integracion_parcial"


def extract_traumas_from_log(episodic_log: list[str], last_n: int = 7) -> list[str]:
    """Extrae keywords de trauma de las últimas N entradas del log episódico."""
    recent = episodic_log[-last_n:]
    found: list[str] = []
    for entry in recent:
        for keyword in _TRAUMA_KEYWORDS:
            if keyword in entry and keyword not in found:
                found.append(keyword)
    return found


@dataclass
class Dream:
    """Resultado de un ciclo de sueño."""
    dia:             int
    simbolo:         str
    arquetipo:       str
    complejo:        str | None
    procesamiento:   str
    insight:         str
    delta_arquetipo: dict[str, float]
    bioma:           str       = "tierra"
    traumas:         list[str] = field(default_factory=list)
    shared_with:     list[str] = field(default_factory=list)


class DreamGrammarEngine:
    """
    Generador composicional de sueños por capas.

    Cada llamada a generate_dream() construye un pool de símbolos ponderado
    a partir del paisaje (bioma), el arquetipo dominante, el complejo activo,
    los traumas recientes y la resonancia grupal (entrelazamiento).
    El símbolo final se muestrea del pool → variabilidad garantizada.
    """

    def generate_dream(
        self,
        dia:               int,
        dominante:         str,
        tension:           float,
        complejo_activo:   str | None,
        bioma:             str = "tierra",
        traumas_recientes: list[str] | None = None,
        resonancia_grupal: str | None = None,
        rng:               random.Random | None = None,
        agent_id:          str | None = None,
    ) -> Dream:
        r = rng or random.Random()
        # Offset determinístico por agente: rompe empates cuando el pool es idéntico
        agent_seed = (abs(hash(agent_id)) % 10_000) / 10_000.0 if agent_id else 0.0

        pool = self._build_pool(dominante, complejo_activo, bioma, traumas_recientes, resonancia_grupal)
        simbolo = self._sample_symbol(pool, r, agent_seed)
        procesamiento = _select_processing(tension, r)
        insight = self._generate_insight(
            dominante, complejo_activo, procesamiento, bioma, traumas_recientes or [], r
        )
        delta = self._compute_delta(dominante, complejo_activo, procesamiento, r)

        return Dream(
            dia             = dia,
            simbolo         = simbolo,
            arquetipo       = dominante,
            complejo        = complejo_activo,
            procesamiento   = procesamiento,
            insight         = insight,
            delta_arquetipo = delta,
            bioma           = bioma,
            traumas         = list(traumas_recientes or []),
            shared_with     = [],
        )

    # ── Construcción del pool ────────────────────────────────────────────────

    def _build_pool(
        self,
        dominante:         str,
        complejo_activo:   str | None,
        bioma:             str,
        traumas_recientes: list[str] | None,
        resonancia_grupal: str | None,
    ) -> list[tuple[str, float]]:
        pool: list[tuple[str, float]] = []

        # Capa 1: paisaje
        for sym in _BIOME_SYMBOLS.get(bioma, _BIOME_SYMBOLS["tierra"]):
            pool.append((sym, _LAYER_WEIGHT["biome"]))

        # Capa 2: arquetipo dominante
        for sym in _ARCHETYPE_SYMBOLS.get(dominante, []):
            pool.append((sym, _LAYER_WEIGHT["archetype"]))

        # Capa 3: complejo activo
        if complejo_activo:
            for sym in _COMPLEX_SYMBOLS.get(complejo_activo, []):
                pool.append((sym, _LAYER_WEIGHT["complex"]))

        # Capa 4: traumas recientes
        for trauma in (traumas_recientes or []):
            for sym in _TRAUMA_KEYWORDS.get(trauma, []):
                pool.append((sym, _LAYER_WEIGHT["trauma"]))

        # Capa 5: resonancia grupal (entrelazamiento)
        if resonancia_grupal:
            pool.append((resonancia_grupal, _LAYER_WEIGHT["resonance"]))

        return pool

    def _sample_symbol(
        self,
        pool: list[tuple[str, float]],
        rng: random.Random,
        agent_seed: float = 0.0,
    ) -> str:
        if not pool:
            return _DEFAULT_SYMBOL
        total = sum(w for _, w in pool)
        # agent_seed desplaza el punto de muestreo de forma determinística por agente,
        # garantizando que dos agentes con pool idéntico no aterricen en el mismo símbolo.
        r = (rng.random() * total + agent_seed * (total / len(pool))) % total
        cumulative = 0.0
        for sym, w in pool:
            cumulative += w
            if r <= cumulative:
                return sym
        return pool[-1][0]

    # ── Generación de insight ────────────────────────────────────────────────

    def _generate_insight(
        self,
        dominante:       str,
        complejo_activo: str | None,
        procesamiento:   str,
        bioma:           str,
        traumas:         list[str],
        rng:             random.Random | None = None,
    ) -> str:
        r = rng or random.Random()
        landscape = bioma.replace("_", " ") if bioma != "tierra" else "la oscuridad"
        wound = (
            traumas[0].replace("_", " ") if traumas
            else complejo_activo or "lo reprimido"
        )
        templates = _INSIGHT_TEMPLATES.get(procesamiento, _INSIGHT_TEMPLATES["proyeccion"])
        template = r.choice(templates)
        return template.format(landscape=landscape, dominante=dominante, wound=wound)

    # ── Cómputo de deltas arquetípicos ───────────────────────────────────────

    def _compute_delta(
        self,
        dominante:       str,
        complejo_activo: str | None,
        procesamiento:   str,
        rng:             random.Random,
    ) -> dict[str, float]:
        delta: dict[str, float] = {}
        magnitude = rng.uniform(0.02, 0.06)

        if procesamiento == "integracion_parcial":
            delta["self"] = +magnitude
            if complejo_activo:
                delta[dominante] = -magnitude * 0.5
        elif procesamiento == "amplificacion":
            delta[dominante] = +magnitude
        elif procesamiento == "compensacion":
            opuesto = _ARCHETYPE_OPPOSITES.get(dominante, "sombra")
            delta[opuesto]   = +magnitude * 0.7
            delta[dominante] = -magnitude * 0.3
        else:  # proyeccion
            delta["sombra"]  = +magnitude * 0.8
            delta[dominante] = -magnitude * 0.4

        return delta


# Alias de retrocompatibilidad
DreamEngine = DreamGrammarEngine
