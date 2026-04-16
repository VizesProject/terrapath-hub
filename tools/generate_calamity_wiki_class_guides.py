#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import unicodedata
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

TERRARIA_SEARCH = ROOT / "supported" / "Terraria" / "search-content.json"
CALAMITY_SEARCH = ROOT / "supported" / "CalamityMod" / "search-content.json"

OUTPUT_ROOT = ROOT / "guides" / "ru-RU"

META_RE = re.compile(r"^([a-z-]+)\s+([a-z0-9-]+)\s+([A-Za-z]+)$")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
MULTISPACE_RE = re.compile(r"\s+")

STAGE_ALIAS = {"pre-scal": "pre-scal-exo", "pre-exo": "pre-scal-exo"}

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
    "pre-boss": {"era": "prehardmode", "title": "Пре-боссы {{icon:CalamityMod/DesertScourgeHead}}"},
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

CLASS_PLANS = [
    {"tag": "melee", "title": "Calamity wiki - Воин", "slug": "calamity-wiki-melee"},
    {"tag": "ranged", "title": "Calamity wiki - Стрелок", "slug": "calamity-wiki-ranged"},
    {"tag": "magic", "title": "Calamity wiki - Маг", "slug": "calamity-wiki-magic"},
    {"tag": "summoner", "title": "Calamity wiki - Призыватель", "slug": "calamity-wiki-summoner"},
    {"tag": "rogue", "title": "Calamity wiki - Разбойник", "slug": "calamity-wiki-rogue"},
]

# Curated fixes for the few names that still cannot be resolved deterministically.
MANUAL_ALIASES = {
    "buffcandles": "CalamityMod/VigorousCandle",
    "патронвысокойскорости": "Terraria/HighVelocityBullet",
    "стрелаобжигающегохолода": "Terraria/FrostburnArrow",
    "минуядерныйзарядi": "Terraria/MiniNukeI",
    "минуядерныйзарядii": "Terraria/MiniNukeII",
    "волфрамоваяпуля": "Terraria/MusketBall",
    "волшебнаясила": "Terraria/MagicPowerPotion",
    "ясновидение": "Terraria/Clairvoyance",
}


@dataclass
class RowItem:
    class_key: str
    stage: str
    bucket: str
    name_ru: str
    slug_ru: str
    name_en: str
    slug_en: str


def normalize(text: str) -> str:
    value = unicodedata.normalize("NFKC", (text or "").strip().lower())
    value = value.replace("ё", "е")
    return re.sub(r"[^a-z0-9а-я]+", "", value)


def should_include_row(target_class: str, row_class: str) -> bool:
    if row_class == target_class:
        return True
    if row_class == "all":
        return True
    if row_class == "all-but-summoner" and target_class != "summon":
        return True
    if row_class == "all-but-stealth" and target_class != "rogue":
        return True
    return False


def parse_markdown_item_cells(line: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for text, url in LINK_RE.findall(line):
        label = text.strip()
        if not label or label.startswith("!["):
            continue
        if label in {"+", "†", "≤", "∞"}:
            continue
        slug = unquote(urlparse(url).path.split("/")[-1]).split("?")[0]
        out.append((label, slug))
    if out:
        return out

    raw = MULTISPACE_RE.sub(" ", line).strip()
    if not raw:
        return []
    parts = [part.strip() for part in re.split(r"\s*/\s*", raw) if part.strip()]
    return [(part, "") for part in parts]


def parse_rows(path: Path) -> list[tuple[tuple[str, str, str], int, list[tuple[str, str]]]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    occurrences: dict[tuple[str, str, str], int] = defaultdict(int)
    rows: list[tuple[tuple[str, str, str], int, list[tuple[str, str]]]] = []

    for i, line in enumerate(lines):
        match = META_RE.match(line.strip())
        if not match:
            continue
        class_key, stage, bucket = match.groups()
        stage = STAGE_ALIAS.get(stage, stage)
        key = (class_key, stage, bucket)
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
    if b.startswith("weapon") or b in {"minions", "sentries", "weaponsummon", "support"}:
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
    if b.startswith("buff"):
        if "mobility" in b:
            return "buff", "Мобильные"
        if "defense" in b:
            return "buff", "Защитные"
        if "offense" in b:
            return "buff", "Атакующие"
        return "buff", "Универсальные"
    if b == "ammo":
        return "ammo", None
    return "other", None


def load_item_entries() -> list[dict]:
    terraria = json.loads(TERRARIA_SEARCH.read_text(encoding="utf-8")).get("entries", [])
    calamity = json.loads(CALAMITY_SEARCH.read_text(encoding="utf-8")).get("entries", [])
    return [entry for entry in (terraria + calamity) if entry.get("kind") == "item" and entry.get("id")]


def build_indexes(entries: Iterable[dict]) -> dict[str, dict[str, list[dict]]]:
    by_internal: dict[str, list[dict]] = defaultdict(list)
    by_ru: dict[str, list[dict]] = defaultdict(list)
    by_en: dict[str, list[dict]] = defaultdict(list)
    by_any: dict[str, list[dict]] = defaultdict(list)

    for entry in entries:
        keys_internal = [
            entry.get("internalName"),
            str(entry.get("id", "")).split("/", 1)[-1],
        ]
        keys_ru = [entry.get("displayNameRu")]
        keys_en = [entry.get("displayName")]
        keys_any = [
            entry.get("displayNameRu"),
            entry.get("displayName"),
            entry.get("internalName"),
            str(entry.get("id", "")),
            str(entry.get("id", "")).replace("/", " "),
        ]

        for key in keys_internal:
            norm = normalize(str(key or ""))
            if norm:
                by_internal[norm].append(entry)
        for key in keys_ru:
            norm = normalize(str(key or ""))
            if norm:
                by_ru[norm].append(entry)
        for key in keys_en:
            norm = normalize(str(key or ""))
            if norm:
                by_en[norm].append(entry)
        for key in keys_any:
            norm = normalize(str(key or ""))
            if norm:
                by_any[norm].append(entry)

    return {"internal": by_internal, "ru": by_ru, "en": by_en, "any": by_any}


def expected_categories(bucket: str, output_category: str) -> set[str]:
    b = bucket.lower()
    if output_category == "weapon":
        return {"weapon"}
    if output_category == "armor":
        return {"armor"}
    if output_category == "accessory":
        return {"accessory"}
    if output_category == "buff":
        return {"buff"}
    if b == "ammo":
        return {"buff", "other"}
    return set()


def slug_variants(slug: str) -> list[str]:
    if not slug:
        return []
    base = slug.split("#", 1)[0].split("?", 1)[0]
    return [base, base.replace("_", " "), re.sub(r"\s*\([^)]*\)\s*$", "", base)]


def pick_best(candidates: list[tuple[int, dict]], expect: set[str]) -> dict | None:
    if not candidates:
        return None
    scored: list[tuple[int, dict]] = []
    for base_score, entry in candidates:
        score = base_score
        if expect and entry.get("category") in expect:
            score += 25
        scored.append((score, entry))
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[0][1]


def resolve_content_id(item: RowItem, category: str, indexes: dict[str, dict[str, list[dict]]]) -> str | None:
    alias = MANUAL_ALIASES.get(normalize(item.name_ru))
    if alias:
        return alias

    expect = expected_categories(item.bucket, category)
    candidates: dict[str, tuple[int, dict]] = {}

    def add(entry_list: Iterable[dict], base_score: int) -> None:
        for entry in entry_list:
            eid = str(entry.get("id"))
            prev = candidates.get(eid)
            if prev is None or base_score > prev[0]:
                candidates[eid] = (base_score, entry)

    for value in slug_variants(item.slug_en):
        norm = normalize(value)
        if norm:
            add(indexes["internal"].get(norm, []), 120)
            add(indexes["en"].get(norm, []), 100)
    for value in slug_variants(item.slug_ru):
        norm = normalize(value)
        if norm:
            add(indexes["ru"].get(norm, []), 95)
            add(indexes["any"].get(norm, []), 75)

    for value in [item.name_en, item.name_ru]:
        norm = normalize(value)
        if not norm:
            continue
        add(indexes["en"].get(norm, []), 90)
        add(indexes["ru"].get(norm, []), 90)
        add(indexes["any"].get(norm, []), 70)

    best = pick_best(list(candidates.values()), expect)
    if best:
        return str(best["id"])
    return None


def build_rows_with_pairs() -> list[RowItem]:
    ru_rows = []
    en_rows = []
    for path in RU_DATA_FILES:
        ru_rows.extend(parse_rows(path))
    for path in EN_DATA_FILES:
        en_rows.extend(parse_rows(path))

    en_by_key: dict[tuple[str, str, str, int], list[tuple[str, str]]] = {}
    for (class_key, stage, bucket), idx, cells in en_rows:
        en_by_key[(class_key, stage, bucket, idx)] = cells

    paired: list[RowItem] = []
    for (class_key, stage, bucket), idx, ru_cells in ru_rows:
        if stage not in STAGE_ORDER:
            continue
        en_cells = en_by_key.get((class_key, stage, bucket, idx), [])
        for i, (name_ru, slug_ru) in enumerate(ru_cells):
            name_en, slug_en = ("", "")
            if i < len(en_cells):
                name_en, slug_en = en_cells[i]
            elif en_cells:
                name_en, slug_en = en_cells[-1]
            paired.append(
                RowItem(
                    class_key=class_key,
                    stage=stage,
                    bucket=bucket,
                    name_ru=name_ru,
                    slug_ru=slug_ru,
                    name_en=name_en,
                    slug_en=slug_en,
                )
            )
    return paired


def build_items_for_class(class_tag: str, rows: list[RowItem], indexes: dict[str, dict[str, list[dict]]]) -> tuple[dict[str, list[dict]], list[RowItem]]:
    by_stage: dict[str, list[dict]] = {stage_id: [] for stage_id in STAGE_ORDER}
    dedupe: dict[str, set[tuple[str, str, str | None]]] = defaultdict(set)
    unresolved: list[RowItem] = []

    class_key = "summon" if class_tag == "summoner" else class_tag

    for row in rows:
        if not should_include_row(class_key, row.class_key):
            continue
        category, subgroup = bucket_to_category(row.bucket)
        item_id = resolve_content_id(row, category, indexes)
        if not item_id:
            unresolved.append(row)
            continue

        signature = (item_id, category, subgroup)
        if signature in dedupe[row.stage]:
            continue
        dedupe[row.stage].add(signature)

        payload = {"itemId": item_id, "category": category}
        if subgroup:
            payload["subgroup"] = subgroup
        by_stage[row.stage].append(payload)

    return by_stage, unresolved


def build_document(plan: dict, stage_items: dict[str, list[dict]]) -> dict:
    today = date.today().isoformat()
    stages = []
    for stage_id in STAGE_ORDER:
        meta = STAGE_META[stage_id]
        stage = {
            "id": stage_id,
            "title": meta["title"],
            "era": meta["era"],
            "description": "",
            "items": stage_items.get(stage_id, []),
        }
        boss_refs = BOSS_REFS.get(stage_id, [])
        if boss_refs:
            stage["bossRefs"] = boss_refs
        stages.append(stage)

    return {
        "schemaVersion": 1,
        "id": plan["slug"],
        "title": plan["title"],
        "author": "TerraPath Team",
        "language": "ru-RU",
        "summary": f"Копия wiki-конфигурации класса {plan['title'].split(' - ', 1)[1]} для Calamity (описания этапов оставлены пустыми).",
        "requiredMods": ["Terraria", "CalamityMod"],
        "classTags": [plan["tag"]],
        "createdAt": today,
        "updatedAt": today,
        "stages": stages,
    }


def write_guides() -> dict[str, list[RowItem]]:
    rows = build_rows_with_pairs()
    indexes = build_indexes(load_item_entries())

    unresolved_by_class: dict[str, list[RowItem]] = {}
    for plan in CLASS_PLANS:
        stage_items, unresolved = build_items_for_class(plan["tag"], rows, indexes)
        unresolved_by_class[plan["tag"]] = unresolved
        document = build_document(plan, stage_items)
        out = OUTPUT_ROOT / plan["slug"] / "guide.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return unresolved_by_class


def main() -> None:
    unresolved_by_class = write_guides()
    print("Generated guides:")
    for plan in CLASS_PLANS:
        guide_path = OUTPUT_ROOT / plan["slug"] / "guide.json"
        print(f"  - {plan['title']} -> {guide_path}")
    print()
    print("Unresolved rows:")
    total = 0
    for plan in CLASS_PLANS:
        unresolved = unresolved_by_class[plan["tag"]]
        total += len(unresolved)
        print(f"  - {plan['tag']}: {len(unresolved)}")
    print(f"Total unresolved: {total}")


if __name__ == "__main__":
    main()
