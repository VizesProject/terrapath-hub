#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]

RU_DATA_FILES = [
    ROOT / ".tmp" / "wiki" / "prehardmode_data.md",
    ROOT / ".tmp" / "wiki" / "hardmode_data.md",
    ROOT / ".tmp" / "wiki" / "postmoonlord_data.md",
]
EN_DATA_FILES = [
    ROOT / ".tmp" / "wiki_en" / "pre.md",
    ROOT / ".tmp" / "wiki_en" / "hard.md",
    ROOT / ".tmp" / "wiki_en" / "post.md",
]

PRE_MAIN_FILE = ROOT / ".tmp" / "wiki" / "prehardmode.md"
HARD_MAIN_FILE = ROOT / ".tmp" / "wiki" / "hardmode.md"
POST_MAIN_FILE = ROOT / ".tmp" / "wiki" / "postmoonlord.md"

TERRARIA_SEARCH = ROOT / "supported" / "Terraria" / "search-content.json"
CALAMITY_SEARCH = ROOT / "supported" / "CalamityMod" / "search-content.json"

OUTPUT = ROOT / "guides" / "ru-RU" / "calamity-ranger-wiki-3-eras" / "guide.json"

ALLOWED_CLASSES = {"ranged", "all", "all-but-summoner", "all-but-stealth"}
STAGE_ALIAS = {"pre-scal": "pre-scal-exo", "pre-exo": "pre-scal-exo"}

META_RE = re.compile(r"^([a-z-]+)\s+([a-z0-9-]+)\s+([A-Za-z]+)$")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
MULTISPACE_RE = re.compile(r"\s+")

STAGE_ORDER = [
    "pre-boss",
    "pre-evil1",
    "pre-evil2",
    "pre-skeletron",
    "pre-wof",
    "pre-mech",
    "post-mech1",
    "post-mech2",
    "pre-plantera",
    "pre-golem",
    "post-golem",
    "pre-lunar",
    "pre-moonlord",
    "pre-provi",
    "pre-polter",
    "pre-dog",
    "pre-yharon",
    "pre-scal-exo",
    "endgame",
]

STAGE_META = {
    "pre-boss": {"era": "prehardmode", "title": "Пре-босс {{icon:CalamityMod/DesertScourgeHead}}"},
    "pre-evil1": {"era": "prehardmode", "title": "Пре-Пожиратель миров/Мозг Ктулху {{icon:Terraria/EaterofWorldsHead}} {{icon:Terraria/BrainofCthulhu}}"},
    "pre-evil2": {"era": "prehardmode", "title": "Пре-Разум улья/Перфораторы {{icon:CalamityMod/HiveMind}} {{icon:CalamityMod/PerforatorHive}}"},
    "pre-skeletron": {"era": "prehardmode", "title": "Пре-Скелетрон {{icon:Terraria/SkeletronHead}}"},
    "pre-wof": {"era": "prehardmode", "title": "Пре-Стена плоти {{icon:Terraria/WallofFlesh}}"},
    "pre-mech": {"era": "hardmode", "title": "Пре-Механические боссы {{icon:Terraria/QueenSlimeBoss}} {{icon:CalamityMod/Cryogen}}"},
    "post-mech1": {"era": "hardmode", "title": "Пост-Механический босс 1 {{icon:CalamityMod/AquaticScourgeHead}}"},
    "post-mech2": {"era": "hardmode", "title": "Пост-Механический босс 2 {{icon:CalamityMod/BrimstoneElemental}}"},
    "pre-plantera": {"era": "hardmode", "title": "Пре-Плантера {{icon:Terraria/Plantera}}"},
    "pre-golem": {"era": "hardmode", "title": "Пре-Голем {{icon:Terraria/Golem}}"},
    "post-golem": {"era": "hardmode", "title": "Пост-Голем {{icon:Terraria/Golem}}"},
    "pre-lunar": {"era": "hardmode", "title": "Пре-Лунные события {{icon:Terraria/CultistBoss}}"},
    "pre-moonlord": {"era": "hardmode", "title": "Пре-Лунный лорд {{icon:Terraria/MoonLordCore}}"},
    "pre-provi": {"era": "postmoonlord", "title": "Пре-Провиденс {{icon:CalamityMod/Providence}}"},
    "pre-polter": {"era": "postmoonlord", "title": "Пре-Полтергаст {{icon:CalamityMod/Polterghast}}"},
    "pre-dog": {"era": "postmoonlord", "title": "Пре-Пожиратель богов {{icon:CalamityMod/DevourerofGodsHead}}"},
    "pre-yharon": {"era": "postmoonlord", "title": "Пре-Ярон {{icon:CalamityMod/Yharon}}"},
    "pre-scal-exo": {"era": "postmoonlord", "title": "Пре-Экзо-механизмы/Высшая ведьма, Каламитас {{icon:CalamityMod/AresBody}} {{icon:CalamityMod/SupremeCalamitas}}"},
    "endgame": {"era": "postmoonlord", "title": "Пост-Экзо-механизмы {{icon:CalamityMod/AresBody}}"},
}

BOSS_REFS = {
    "pre-boss": ["CalamityMod/DesertScourgeHead"],
    "pre-evil1": ["Terraria/EaterofWorldsHead", "Terraria/BrainofCthulhu"],
    "pre-evil2": ["CalamityMod/HiveMind", "CalamityMod/PerforatorHive"],
    "pre-skeletron": ["Terraria/SkeletronHead"],
    "pre-wof": ["Terraria/WallofFlesh"],
    "pre-mech": ["Terraria/QueenSlimeBoss", "CalamityMod/Cryogen"],
    "post-mech1": ["CalamityMod/AquaticScourgeHead"],
    "post-mech2": ["CalamityMod/BrimstoneElemental"],
    "pre-plantera": ["Terraria/Plantera"],
    "pre-golem": ["Terraria/Golem"],
    "post-golem": ["Terraria/Golem"],
    "pre-lunar": ["Terraria/CultistBoss"],
    "pre-moonlord": ["Terraria/MoonLordCore"],
    "pre-provi": ["CalamityMod/Providence"],
    "pre-polter": ["CalamityMod/Polterghast"],
    "pre-dog": ["CalamityMod/DevourerofGodsHead"],
    "pre-yharon": ["CalamityMod/Yharon"],
    "pre-scal-exo": ["CalamityMod/AresBody", "CalamityMod/SupremeCalamitas"],
}

MANUAL_ALIASES = {
    "зельеэкономиибоеприпасов": "Terraria/AmmoReservationPotion",
    "сытнаятрапеза": "Terraria/SeafoodDinner",
    "buffcandles": "CalamityMod/VigorousCandle",
    "зельесердечногопритяжения": "Terraria/HeartreachPotion",
    "зельестремительности": "Terraria/SwiftnessPotion",
    "зельегнева": "Terraria/WrathPotion",
    "разведывательныйприцел": "Terraria/RifleScope",
    "шутовскаястрела": "Terraria/JestersArrow",
    "мушкетнаяпуля": "Terraria/MusketBall",
    "сказочныеботинки": "Terraria/FairyBoots",
    "снаряжениемастераниндзя": "Terraria/MasterNinjaGear",
    "ископаемаяброня": "Terraria/FossilHelm",
    "медоперка": "Terraria/Honeyfin",
    "взрывнаяпуля": "Terraria/ExplodingBullet",
    "парящаяинсигния": "Terraria/SoaringInsignia",
    "броняснежногобандита": "CalamityMod/SnowRuffianMask",
    "золотаяброня": "Terraria/GoldHelmet",
    "платиноваяброня": "Terraria/PlatinumHelmet",
    "любойнадувнойшарик": "Terraria/BundleofBalloons",
    "багрянаяброня": "Terraria/CrimsonHelmet",
    "теневаяброня": "Terraria/ShadowHelmet",
    "согревающеезелье": "Terraria/WarmthPotion",
    "высокоскоростнойпатрон": "Terraria/HighVelocityBullet",
    "эмблемастрелка": "Terraria/RangerEmblem",
    "освященныйкомплект": "Terraria/HallowedMask",
    "амулетмифов": "Terraria/CharmofMyths",
    "броняжнецачумы": "CalamityMod/PlagueReaperMask",
    "грибнитовыйкомплект": "Terraria/ShroomiteMask",
    "гидротермическийкомплект": "CalamityMod/HydrothermicHeadRanged",
    "крыльябэтси": "Terraria/BetsyWings",
    "броняэлитноголунногоотряда": "CalamityMod/LunicCorpsHelmet",
    "ауритовыйтеслакомплект": "CalamityMod/AuricTeslaHeadRanged",
    "миниядерныйзаряди": "Terraria/MiniNukeI",
    "стрелаобжигающегохолода": "Terraria/FrostburnArrow",
    "серебрянаяброня": "Terraria/SilverHelmet",
    "любойдвойнойпрыжок": "Terraria/CloudinaBottle",
    "перекус": "Terraria/RoastedBird",
    "комплектприлива": "CalamityMod/VictideHeadRanged",
    "аэрофазовыйкомплект": "CalamityMod/AerospecHeadRanged",
    "некроброня": "Terraria/NecroHelmet",
    "зельевосстановления": "Terraria/RestorationPotion",
    "кобальтовыйкомплект": "Terraria/CobaltMask",
    "палладиевыйкомплект": "Terraria/PalladiumMask",
    "мифриловыйкомплект": "Terraria/MythrilHat",
    "кристальнаяброняассасина": "CalamityMod/UmbraphileHood",
    "орихалковыйкомплект": "Terraria/OrichalcumMask",
    "адамантитовыйкомплект": "Terraria/AdamantiteMask",
    "хлорофитовыйкомплект": "Terraria/ChlorophyteMask",
    "лягушачьилапки": "Terraria/FrogLeg",
    "пламенныекрылья": "Terraria/FlameWings",
    "небесныйкаратель": "CalamityMod/HeavenlyGale",
    "вихревойзагонщик": "Terraria/VortexBeater",
    "астральнаяброня": "CalamityMod/AstralHelm",
    "вихреваяброня": "Terraria/VortexHelmet",
    "вихревойусилитель": "Terraria/WingsVortex",
    "неземнаязвезднаяплатформа": "Terraria/StardustPlatform",
    "эстрагоновыйкомплект": "CalamityMod/TarragonHeadRanged",
    "комплектбогоубийцы": "CalamityMod/GodSlayerHeadRanged",
    "комплекткровавойвспышки": "CalamityMod/BloodflareHeadRanged",
    "омегасиняяброня": "CalamityMod/OmegaBlueHelmet",
    "тенедемоническаяброня": "CalamityMod/DemonshadeHelm",
    "высокотехнологичнаясамоцветнаяброня": "CalamityMod/GemTechHeadgear",
    "неземнаяракушка": "Terraria/CelestialShell",
    "люминитовыйпатрон": "Terraria/MoonlordBullet",
    "искрометныетерработинки": "Terraria/TerrasparkBoots",
    "хлорофитовыймногозарядныйарбалет": "Terraria/ChlorophyteShotbow",
    "освященныйсамострел": "Terraria/HallowedRepeater",
    "пираньеваяпушка": "Terraria/PiranhaGun",
    "гневбэтси": "Terraria/DD2BetsyBow",
    "празднованиеобр2": "Terraria/Celeb2",
    "миниядерныйзарядi": "Terraria/MiniNukeI",
    "миниядерныйзарядii": "Terraria/MiniNukeII",
    "миниядерныйзаряди": "Terraria/MiniNukeI",
    "комплектразорителя": "CalamityMod/ReaverHeadMobility",
}


@dataclass
class RowItem:
    name_ru: str
    name_en: str
    slug_ru: str
    slug_en: str
    stage: str
    bucket: str


def normalize(text: str) -> str:
    value = (text or "").strip().lower().replace("ё", "е")
    return re.sub(r"[^a-z0-9а-я]+", "", value)


def load_entries() -> list[dict]:
    terraria = json.loads(TERRARIA_SEARCH.read_text(encoding="utf-8")).get("entries", [])
    calamity = json.loads(CALAMITY_SEARCH.read_text(encoding="utf-8")).get("entries", [])
    return terraria + calamity


def build_lookup(entries: Iterable[dict]) -> dict[str, list[str]]:
    lookup: dict[str, list[str]] = defaultdict(list)
    for entry in entries:
        cid = str(entry.get("id") or "")
        if not cid:
            continue
        keys = [
            entry.get("displayNameRu"),
            entry.get("displayName"),
            entry.get("internalName"),
            cid,
            cid.replace("/", " "),
        ]
        for key in keys:
            norm = normalize(str(key or ""))
            if norm:
                lookup[norm].append(cid)
    return lookup


def parse_markdown_item_cells(line: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for text, url in LINK_RE.findall(line):
        label = text.strip()
        if not label or label.startswith("!["):
            continue
        if label in {"+", "†", "C", "≤", "∞"}:
            continue
        slug = unquote(urlparse(url).path.split("/")[-1]).split("?")[0]
        out.append((label, slug))

    if out:
        return out

    raw = MULTISPACE_RE.sub(" ", line).strip()
    if not raw:
        return []
    return [(part.strip(), "") for part in re.split(r"\s*/\s*", raw) if part.strip()]


def parse_rows(path: Path) -> list[tuple[tuple[str, str, str], int, list[tuple[str, str]]]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    occurrences: dict[tuple[str, str, str], int] = defaultdict(int)
    rows: list[tuple[tuple[str, str, str], int, list[tuple[str, str]]]] = []
    for i, line in enumerate(lines):
        match = META_RE.match(line.strip())
        if not match:
            continue
        klass, stage, bucket = match.groups()
        if klass not in ALLOWED_CLASSES:
            continue
        stage = STAGE_ALIAS.get(stage, stage)
        key = (klass, stage, bucket)
        index = occurrences[key]
        occurrences[key] += 1

        source = ""
        prev = i - 1
        while prev >= 0:
            candidate = lines[prev].strip()
            if candidate:
                source = candidate
                break
            prev -= 1

        rows.append((key, index, parse_markdown_item_cells(source)))
    return rows


def bucket_to_category(bucket: str) -> tuple[str, str | None]:
    b = bucket.lower()
    if b.startswith("weapon"):
        return "weapon", None
    if b.startswith("armor"):
        return "armor", None
    if b.startswith("accessor") or b.startswith("accessory"):
        if "mobility" in b:
            return "accessory", "Мобильные"
        if "defense" in b:
            return "accessory", "Защитные"
        if "offense" in b or "spam" in b or "stealth" in b:
            return "accessory", "Атакующие"
        return "accessory", "Универсальные"
    if b.startswith("ammo"):
        return "ammo", "Боеприпасы"
    if b.startswith("buff"):
        if "mobility" in b:
            return "buff", "Мобильные"
        if "defense" in b:
            return "buff", "Защитные"
        if "offense" in b:
            return "buff", "Атакующие"
        return "buff", "Универсальные"
    return "other", None


def resolve_content_id(item: RowItem, lookup: dict[str, list[str]]) -> str | None:
    keys = [
        item.name_ru,
        item.name_en,
        item.slug_ru,
        item.slug_en,
        item.slug_ru.replace("_", " "),
        item.slug_en.replace("_", " "),
    ]
    for key in keys:
        norm = normalize(key)
        if norm and lookup.get(norm):
            return lookup[norm][0]
    alias = MANUAL_ALIASES.get(normalize(item.name_ru))
    if alias:
        return alias
    return None


def stage_descriptions() -> dict[str, str]:
    descriptions: dict[str, str] = {}

    def first_non_empty(lines: list[str], start: int) -> str:
        for i in range(start, len(lines)):
            if lines[i].strip():
                return lines[i].strip()
        return ""

    pre_lines = PRE_MAIN_FILE.read_text(encoding="utf-8").splitlines()
    pre_marks = {
        "pre-boss": "## Пре-босс",
        "pre-evil1": "## Пре-[Пожиратель миров]",
        "pre-evil2": "## Пре-[Разум улья]",
        "pre-skeletron": "## Пре-[Скелетрон]",
        "pre-wof": "## Пре-[Стена плоти]",
    }
    for stage_id, marker in pre_marks.items():
        idx = next((i for i, line in enumerate(pre_lines) if line.startswith(marker)), None)
        if idx is not None:
            descriptions[stage_id] = first_non_empty(pre_lines, idx + 1)

    hard_lines = HARD_MAIN_FILE.read_text(encoding="utf-8").splitlines()
    hard_marks = {
        "pre-mech": "Пре-Механические боссы",
        "post-mech1": "Пост-Механический босс 1",
        "post-mech2": "Пост-Механический босс 2",
        "pre-plantera": "Пре-Плантера",
        "pre-golem": "Пре-Голем",
        "post-golem": "Пост-Голем",
        "pre-lunar": "Пре-Лунные события",
        "pre-moonlord": "Пре-Лунный лорд",
    }
    for stage_id, marker in hard_marks.items():
        indexes = [i for i, line in enumerate(hard_lines) if marker in line]
        if indexes:
            descriptions[stage_id] = first_non_empty(hard_lines, indexes[-1] + 1)

    post_lines = POST_MAIN_FILE.read_text(encoding="utf-8").splitlines()
    post_marks = {
        "pre-provi": "Пре-Провиденс",
        "pre-polter": "Пре-Полтергаст",
        "pre-dog": "Пре-Пожиратель богов",
        "pre-yharon": "Пре-Ярон",
        "pre-scal-exo": "Пре-Экзо-механизмы/Высшая ведьма, Каламитас",
    }
    for stage_id, marker in post_marks.items():
        indexes = [i for i, line in enumerate(post_lines) if marker in line]
        if indexes:
            descriptions[stage_id] = first_non_empty(post_lines, indexes[-1] + 1)

    descriptions["endgame"] = "Финальный набор после Экзо-механизмов и Каламитас для добора максимального урона и выживаемости."

    return {k: cleanup_text(v) for k, v in descriptions.items()}


def cleanup_text(text: str) -> str:
    cleaned = text
    cleaned = re.sub(r"\[!\[[^\]]+\]\([^)]+\)\]\([^)]+\)", "", cleaned)
    cleaned = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", cleaned)
    cleaned = cleaned.replace("(calamity)", "")
    cleaned = MULTISPACE_RE.sub(" ", cleaned).strip()
    return cleaned


def build_items() -> tuple[dict[str, list[dict]], list[RowItem]]:
    ru_rows = []
    en_rows = []
    for path in RU_DATA_FILES:
        ru_rows.extend(parse_rows(path))
    for path in EN_DATA_FILES:
        en_rows.extend(parse_rows(path))

    en_iter = iter(en_rows)
    entries = load_entries()
    lookup = build_lookup(entries)

    by_stage: dict[str, list[dict]] = {stage_id: [] for stage_id in STAGE_ORDER}
    unresolved: list[RowItem] = []
    dedupe: dict[str, set[tuple[str, str, str | None]]] = defaultdict(set)

    for key, row_idx, ru_cells in ru_rows:
        klass, stage, bucket = key
        if stage not in by_stage:
            continue

        en_cells: list[tuple[str, str]] = []
        while True:
            try:
                en_key, en_idx, cells = next(en_iter)
            except StopIteration:
                cells = []
                break
            if en_key == key and en_idx == row_idx:
                en_cells = cells
                break

        category, subgroup = bucket_to_category(bucket)
        for i, (name_ru, slug_ru) in enumerate(ru_cells):
            name_en, slug_en = ("", "")
            if i < len(en_cells):
                name_en, slug_en = en_cells[i]
            elif en_cells:
                name_en, slug_en = en_cells[-1]

            row_item = RowItem(
                name_ru=name_ru,
                name_en=name_en,
                slug_ru=slug_ru,
                slug_en=slug_en,
                stage=stage,
                bucket=bucket,
            )
            item_id = resolve_content_id(row_item, lookup)
            if not item_id:
                unresolved.append(row_item)
                continue

            key_tuple = (item_id, category, subgroup)
            if key_tuple in dedupe[stage]:
                continue
            dedupe[stage].add(key_tuple)

            payload = {"itemId": item_id, "category": category}
            if subgroup:
                payload["subgroup"] = subgroup
            by_stage[stage].append(payload)

    return by_stage, unresolved


def build_document() -> tuple[dict, list[RowItem]]:
    descriptions = stage_descriptions()
    stage_items, unresolved = build_items()
    today = date.today().isoformat()

    stages = []
    for stage_id in STAGE_ORDER:
        meta = STAGE_META[stage_id]
        stage = {
            "id": stage_id,
            "title": meta["title"],
            "era": meta["era"],
            "description": descriptions.get(stage_id, ""),
            "items": stage_items.get(stage_id, []),
        }
        boss_refs = BOSS_REFS.get(stage_id, [])
        if boss_refs:
            stage["bossRefs"] = boss_refs
        stages.append(stage)

    doc = {
        "schemaVersion": 1,
        "id": "calamity-ranged-wiki-full-3-era",
        "title": "Calamity Ranger: wiki copy (3 эпохи)",
        "author": "TerraPath Team",
        "language": "ru-RU",
        "summary": "Тестовый гайд по стрелку, собранный по структуре трёх wiki-страниц Calamity: пре-хардмод, хардмод и пост-лунный лорд.",
        "requiredMods": ["Terraria", "CalamityMod"],
        "classTags": ["ranged"],
        "createdAt": today,
        "updatedAt": today,
        "stages": stages,
    }
    return doc, unresolved


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document, unresolved = build_document()
    OUTPUT.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Guide written: {OUTPUT}")
    print(f"Stages: {len(document['stages'])}")
    print(f"Items total: {sum(len(stage['items']) for stage in document['stages'])}")
    if unresolved:
        print(f"Unresolved rows: {len(unresolved)}")
        for row in unresolved[:80]:
            print(f"  - {row.stage} | {row.bucket} | {row.name_ru} ({row.name_en})")
    else:
        print("Unresolved rows: 0")


if __name__ == "__main__":
    main()
