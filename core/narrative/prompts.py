"""Constructores de prompts en español para cada tipo de narrativa mítica."""
from __future__ import annotations

_SISTEMA = (
    "Eres un narrador mítico de una civilización ancestral. "
    "Escribes en español con un estilo arcaico, poético y simbólico. "
    "Usas metáforas arquetípicas jungianas. Eres conciso: nunca superas 200 palabras."
)


def prompt_mito_fundacional(
    tribe_name:   str,
    nombres:      list[str],
    bioma:        str,
    arquetipo:    str,
    simbolos:     dict[str, float],
) -> str:
    top_simbolos = sorted(simbolos.items(), key=lambda x: x[1], reverse=True)[:3]
    simbolos_str = ", ".join(f"{s} ({v:.2f})" for s, v in top_simbolos if v > 0.05)
    nombres_str  = ", ".join(nombres[:5])
    return (
        f"{_SISTEMA}\n\n"
        f"Una nueva tribu ha emergido en el mundo. Estos son sus hechos:\n"
        f"- Nombre simbólico: {tribe_name}\n"
        f"- Fundadores: {nombres_str}\n"
        f"- Bioma natal: {bioma}\n"
        f"- Arquetipo dominante colectivo: {arquetipo}\n"
        f"- Símbolos activos en el inconsciente colectivo: {simbolos_str or 'ninguno aún'}\n\n"
        f"Escribe un MITO FUNDACIONAL (150-180 palabras) que explique el origen simbólico "
        f"de esta tribu. El mito debe sentirse antiguo, sagrado y enraizado en su bioma. "
        f"No menciones nombres modernos ni tecnología. Usa metáforas naturales."
    )


def prompt_cronica(
    tribe_name:      str,
    dia_inicio:      int,
    dia_fin:         int,
    n_miembros:      int,
    arquetipo:       str,
    presion:         float,
    simbolo_dom:     str,
    eventos:         list[str],
) -> str:
    eventos_str = "\n".join(f"  - {e}" for e in eventos[-6:]) if eventos else "  - Ningún evento mayor."
    return (
        f"{_SISTEMA}\n\n"
        f"Como cronista, registra los días {dia_inicio}–{dia_fin} de la {tribe_name}.\n"
        f"Estado actual:\n"
        f"- Miembros vivos: {n_miembros}\n"
        f"- Arquetipo dominante: {arquetipo}\n"
        f"- Presión emocional colectiva: {presion:.2f}/1.00\n"
        f"- Símbolo más cargado: {simbolo_dom}\n"
        f"Eventos registrados:\n{eventos_str}\n\n"
        f"Escribe una CRÓNICA HISTÓRICA (150-180 palabras) de este período. "
        f"Habla como un anciano que transmite la memoria oral de su pueblo. "
        f"Refleja el estado emocional y arquetípico de la tribu."
    )


def prompt_elegia(
    nombre:   str,
    edad:     int,
    causa:    str,
    arquetipo: str,
    tribu:    str,
    memorias: list[str],
) -> str:
    mem_str = "\n".join(f"  - {m}" for m in memorias[-4:]) if memorias else "  - Sin registros."
    return (
        f"{_SISTEMA}\n\n"
        f"Un ser importante ha partido. Sus datos:\n"
        f"- Nombre: {nombre}\n"
        f"- Edad al morir: {edad} años\n"
        f"- Causa: {causa}\n"
        f"- Arquetipo dominante: {arquetipo}\n"
        f"- Tribu: {tribu}\n"
        f"Fragmentos de su memoria:\n{mem_str}\n\n"
        f"Escribe una ELEGÍA POÉTICA (100-130 palabras) en su honor. "
        f"Usa el arquetipo {arquetipo} como hilo simbólico. "
        f"La elegía debe ser pronunciada por su tribu en el ritual de despedida."
    )


def prompt_profecia(
    tribe_name:      str,
    arquetipo:       str,
    heroe_nombre:    str,
    antagonista:     str,
    presion:         float,
    simbolos:        dict[str, float],
) -> str:
    top_simbolos = sorted(simbolos.items(), key=lambda x: x[1], reverse=True)[:3]
    simbolos_str = ", ".join(s for s, v in top_simbolos if v > 0.1)
    return (
        f"{_SISTEMA}\n\n"
        f"En el inconsciente colectivo de la {tribe_name} ha cristalizado un mito:\n"
        f"- Figura del Héroe: {heroe_nombre} (arquetipo: {arquetipo})\n"
        f"- Figura del Monstruo/Sombra: {antagonista}\n"
        f"- Presión emocional del campo: {presion:.2f}/1.00\n"
        f"- Símbolos activos: {simbolos_str or 'heroe y sombra'}\n\n"
        f"Escribe una PROFECÍA ENIGMÁTICA (100-130 palabras) que los chamanes de esta tribu "
        f"recitarían en sus rituales. La profecía debe hablar del enfrentamiento arquetípico "
        f"sin nombrar directamente a las personas. Usa metáforas de luz, sombra y destino."
    )
