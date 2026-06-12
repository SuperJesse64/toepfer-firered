#!/usr/bin/env python3
"""Apply Toepfer dex CSV to FireRed species names, categories, and pokedex text."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "docs" / "toepfer-dex-entries.csv"
MATRIX_PATH = ROOT / "docs" / "toepfer-matrix.csv"

SPECIES_NAMES = ROOT / "src" / "data" / "text" / "species_names.h"
POKEDEX_ENTRIES = ROOT / "src" / "data" / "pokemon" / "pokedex_entries.h"
POKEDEX_TEXT = ROOT / "src" / "data" / "pokemon" / "pokedex_text_fr.h"

DEX_ORDER = [
    "bulbasaur", "ivysaur", "venusaur", "charmander", "charmeleon", "charizard",
    "squirtle", "wartortle", "blastoise", "caterpie", "metapod", "butterfree",
    "weedle", "kakuna", "beedrill", "pidgey", "pidgeotto", "pidgeot",
    "rattata", "raticate", "spearow", "fearow", "ekans", "arbok",
    "pikachu", "raichu", "sandshrew", "sandslash", "nidoran_f", "nidorina",
    "nidoqueen", "nidoran_m", "nidorino", "nidoking", "clefairy", "clefable",
    "vulpix", "ninetales", "jigglypuff", "wigglytuff", "zubat", "golbat",
    "oddish", "gloom", "vileplume", "paras", "parasect", "venonat", "venomoth",
    "diglett", "dugtrio", "meowth", "persian", "psyduck", "golduck",
    "mankey", "primeape", "growlithe", "arcanine", "poliwag", "poliwhirl",
    "poliwrath", "abra", "kadabra", "alakazam", "machop", "machoke", "machamp",
    "bellsprout", "weepinbell", "victreebel", "tentacool", "tentacruel",
    "geodude", "graveler", "golem", "ponyta", "rapidash", "slowpoke", "slowbro",
    "magnemite", "magneton", "farfetchd", "doduo", "dodrio", "seel", "dewgong",
    "grimer", "muk", "shellder", "cloyster", "gastly", "haunter", "gengar",
    "onix", "drowzee", "hypno", "krabby", "kingler", "voltorb", "electrode",
    "exeggcute", "exeggutor", "cubone", "marowak", "hitmonlee", "hitmonchan",
    "lickitung", "koffing", "weezing", "rhyhorn", "rhydon", "chansey", "tangela",
    "kangaskhan", "horsea", "seadra", "goldeen", "seaking", "staryu", "starmie",
    "mr_mime", "scyther", "jynx", "electabuzz", "magmar", "pinsir", "tauros",
    "magikarp", "gyarados", "lapras", "ditto", "eevee", "vaporeon", "jolteon",
    "flareon", "porygon", "omanyte", "omastar", "kabuto", "kabutops",
    "aerodactyl", "snorlax", "articuno", "zapdos", "moltres",
    "dratini", "dragonair", "dragonite", "mewtwo", "mew",
]

THEME_WORDS = {
    "bulbasaur": "PLANT", "charmander": "SALES", "squirtle": "OPS", "caterpie": "HR",
    "weedle": "LEGAL", "pidgey": "FLYER", "rattata": "GIG", "spearow": "RETAIL",
    "ekans": "SNAKE", "pikachu": "IT", "sandshrew": "FIELD", "nidoran_f": "QUEEN",
    "nidoran_m": "KING", "clefairy": "MOON", "vulpix": "PR", "jigglypuff": "SING",
    "zubat": "NIGHT", "oddish": "GARDEN", "paras": "FUNGI", "venonat": "QA",
    "diglett": "BASE", "meowth": "COIN", "psyduck": "STRESS", "mankey": "RAGE",
    "growlithe": "GUARD", "poliwag": "SWIM", "abra": "TELE", "machop": "GYM",
    "bellsprout": "VINE", "tentacool": "SEA", "geodude": "ROCK", "ponyta": "RUSH",
    "slowpoke": "ASYNC", "magnemite": "MAG", "farfetchd": "LEEK", "doduo": "DUO",
    "seel": "COLD", "grimer": "TOXIC", "shellder": "SHELL", "gastly": "GHOST",
    "onix": "INFRA", "drowzee": "NAP", "krabby": "CRAB", "voltorb": "ORB",
    "exeggcute": "EGG", "cubone": "BONE", "hitmonlee": "KICK", "hitmonchan": "PUNCH",
    "lickitung": "LICK", "koffing": "GAS", "rhyhorn": "HORN", "chansey": "NURSE",
    "tangela": "VINE", "kangaskhan": "MOM", "horsea": "SEA", "goldeen": "FISH",
    "staryu": "STAR", "mr_mime": "MIME", "scyther": "CUT", "jynx": "ICE",
    "electabuzz": "BUZZ", "magmar": "FIRE", "pinsir": "PIN", "tauros": "BULL",
    "magikarp": "FLOP", "lapras": "RIDE", "ditto": "COPY", "eevee": "ADAPT",
    "porygon": "DATA", "omanyte": "FOSSIL", "kabuto": "BUG", "aerodactyl": "WING",
    "snorlax": "NAP", "articuno": "ICE", "zapdos": "ZAP", "moltres": "BURN",
    "dratini": "DRAG", "mewtwo": "CLONE", "mew": "MYTH",
}

FAMILIES = [
    ["bulbasaur", "ivysaur", "venusaur"], ["charmander", "charmeleon", "charizard"],
    ["squirtle", "wartortle", "blastoise"], ["caterpie", "metapod", "butterfree"],
    ["weedle", "kakuna", "beedrill"], ["pidgey", "pidgeotto", "pidgeot"],
    ["rattata", "raticate"], ["spearow", "fearow"], ["ekans", "arbok"],
    ["pikachu", "raichu"], ["sandshrew", "sandslash"],
    ["nidoran_f", "nidorina", "nidoqueen"], ["nidoran_m", "nidorino", "nidoking"],
    ["clefairy", "clefable"], ["vulpix", "ninetales"], ["jigglypuff", "wigglytuff"],
    ["zubat", "golbat"], ["oddish", "gloom", "vileplume"], ["paras", "parasect"],
    ["venonat", "venomoth"], ["diglett", "dugtrio"], ["meowth", "persian"],
    ["psyduck", "golduck"], ["mankey", "primeape"], ["growlithe", "arcanine"],
    ["poliwag", "poliwhirl", "poliwrath"], ["abra", "kadabra", "alakazam"],
    ["machop", "machoke", "machamp"], ["bellsprout", "weepinbell", "victreebel"],
    ["tentacool", "tentacruel"], ["geodude", "graveler", "golem"],
    ["ponyta", "rapidash"], ["slowpoke", "slowbro"], ["magnemite", "magneton"],
    ["farfetchd"], ["doduo", "dodrio"], ["seel", "dewgong"], ["grimer", "muk"],
    ["shellder", "cloyster"], ["gastly", "haunter", "gengar"], ["onix"],
    ["drowzee", "hypno"], ["krabby", "kingler"], ["voltorb", "electrode"],
    ["exeggcute", "exeggutor"], ["cubone", "marowak"], ["hitmonlee"], ["hitmonchan"],
    ["lickitung"], ["koffing", "weezing"], ["rhyhorn", "rhydon"], ["chansey"],
    ["tangela"], ["kangaskhan"], ["horsea", "seadra"], ["goldeen", "seaking"],
    ["staryu", "starmie"], ["mr_mime"], ["scyther"], ["jynx"], ["electabuzz"],
    ["magmar"], ["pinsir"], ["tauros"], ["magikarp", "gyarados"], ["lapras"],
    ["ditto"], ["eevee", "vaporeon", "jolteon", "flareon"], ["porygon"],
    ["omanyte", "omastar"], ["kabuto", "kabutops"], ["aerodactyl"], ["snorlax"],
    ["articuno"], ["zapdos"], ["moltres"], ["dratini", "dragonair", "dragonite"],
    ["mewtwo"], ["mew"],
]


def theme_for(slug: str) -> str:
    for fam in FAMILIES:
        if slug in fam:
            return THEME_WORDS.get(fam[0], "CORP")
    return THEME_WORDS.get(slug, "CORP")


def c_pokedex_name(slug: str) -> str:
    return {
        "nidoran_f": "NidoranF",
        "nidoran_m": "NidoranM",
        "mr_mime": "Mrmime",
        "farfetchd": "Farfetchd",
    }.get(slug, "".join(part.capitalize() for part in slug.split("_")))


def species_const(slug: str) -> str:
    return slug.upper()


def wrap_three_lines(entry: str, width: int = 38) -> list[str]:
    words = entry.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    while len(lines) < 3:
        lines.append("")
    if len(lines) > 3:
        tail = " ".join(lines[2:])
        lines = lines[:2] + [tail]
    return lines[:3]


def fmt_pokedex_text(entry: str) -> str:
    lines = wrap_three_lines(entry)
    parts = [f'    "{lines[0]}\\n"']
    parts.extend(f'    "{line}\\n"' for line in lines[1:-1])
    parts.append(f'    "{lines[-1]}");')
    return "const u8 g{name}PokedexText[] = _(\n" + "\n".join(parts)


def load_csv() -> dict[str, dict[str, str]]:
    data: dict[str, dict[str, str]] = {}
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            slug = row["slug"].strip()
            ingame = row["ingame_name"].strip().upper()
            entry = row["dex_entry"].strip()
            if len(ingame) > 10:
                sys.exit(f"name too long: {ingame}")
            if not 80 <= len(entry) <= 120:
                sys.exit(f"bad entry length {len(entry)} for {slug}")
            data[slug] = {
                "ingame": ingame,
                "category": f"{theme_for(slug)} TOEP"[:11],
                "entry": entry,
            }
    return data


def apply_species_names(data: dict[str, dict[str, str]]) -> None:
    text = SPECIES_NAMES.read_text(encoding="utf-8")
    for slug in DEX_ORDER:
        const = species_const(slug)
        ingame = data[slug]["ingame"]
        pattern = rf'(\[SPECIES_{re.escape(const)}\] = _\(")[^"]*("\))'
        replacement = rf"\g<1>{ingame}\g<2>"
        new_text, count = re.subn(pattern, replacement, text, count=1)
        if count != 1:
            sys.exit(f"species name replace failed for {slug}")
        text = new_text
    SPECIES_NAMES.write_text(text, encoding="utf-8", newline="\n")


def apply_pokedex_entries(data: dict[str, dict[str, str]]) -> None:
    text = POKEDEX_ENTRIES.read_text(encoding="utf-8")
    for slug in DEX_ORDER:
        const = species_const(slug)
        category = data[slug]["category"]
        pattern = (
            rf'(\[NATIONAL_DEX_{re.escape(const)}\] =\s*\{{\s*'
            rf'\.categoryName = _\(")[^"]*("\),)'
        )
        replacement = rf"\g<1>{category}\g<2>"
        new_text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
        if count != 1:
            sys.exit(f"category replace failed for {slug}")
        text = new_text
    POKEDEX_ENTRIES.write_text(text, encoding="utf-8", newline="\n")


def apply_pokedex_text(data: dict[str, dict[str, str]]) -> None:
    text = POKEDEX_TEXT.read_text(encoding="utf-8")
    blocks = [
        "const u8 gDummyPokedexText[] = _(\n"
        '    "This is a newly discovered TOEPFER. It is\\n"\n'
        '    "currently under investigation. No detailed\\n"\n'
        '    "information is available at this time.");\n\n'
        "const u8 gDummyPokedexTextUnused[] = _(\"\");\n"
    ]
    for slug in DEX_ORDER:
        name = c_pokedex_name(slug)
        blocks.append("\n" + fmt_pokedex_text(data[slug]["entry"]).format(name=name))
        blocks.append(f"\n\nconst u8 g{name}PokedexTextUnused[] = _(\"\");")
    kanto = "".join(blocks) + "\n"
    replacement = kanto + "const u8 gChikoritaPokedexText[] = _("
    pattern = r"const u8 gDummyPokedexText\[\] = _\(.*?^const u8 gChikoritaPokedexText\[\] = _\("
    new_text, count = re.subn(
        pattern,
        lambda _match, repl=replacement: repl,
        text,
        count=1,
        flags=re.S | re.M,
    )
    if count != 1:
        sys.exit("pokedex text splice failed")
    POKEDEX_TEXT.write_text(new_text, encoding="utf-8", newline="\n")


def write_matrix(data: dict[str, dict[str, str]]) -> None:
    rows = ["dex_num,slug,ingame_name,category,dex_entry,char_count"]
    for index, slug in enumerate(DEX_ORDER, 1):
        entry = data[slug]["entry"]
        escaped = entry.replace('"', '""')
        rows.append(
            f'{index},{slug},{data[slug]["ingame"]},{data[slug]["category"]},'
            f'"{escaped}",{len(entry)}'
        )
    MATRIX_PATH.write_text("\n".join(rows) + "\n", encoding="utf-8")


def main() -> int:
    data = load_csv()
    if len(DEX_ORDER) != len(data):
        missing = [slug for slug in DEX_ORDER if slug not in data]
        sys.exit(f"missing slugs: {missing}")
    names = [data[slug]["ingame"] for slug in DEX_ORDER]
    if len(names) != len(set(names)):
        sys.exit("duplicate ingame names")
    apply_species_names(data)
    apply_pokedex_entries(data)
    apply_pokedex_text(data)
    write_matrix(data)
    print(f"Applied {len(DEX_ORDER)} species to FireRed dex files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
