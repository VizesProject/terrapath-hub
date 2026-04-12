import argparse
import json
import re
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "supported" / "mods.registry.json"

STRICT_ITEM_CATEGORIES = {"weapon", "armor", "accessory", "buff", "other"}
VALID_BOSS_COLUMNS = {"miniboss", "prehardmode", "hardmode", "postmoonlord"}
ITEM_LIKE_KINDS = {"item", "material", "ore", "other"}
BOSS_LIKE_KINDS = {"boss", "miniboss"}
OFFICIAL_STATUSES = {"official"}

WEAPON_CONTAMINATION_HINTS = re.compile(
    r"pickaxe|drill|hamaxe|chainsaw|fishingpole|aquarium|bowl|bookcase|statue|wall",
    re.IGNORECASE,
)
ACCESSORY_CONTAMINATION_HINTS = re.compile(
    r"bookcase|banner$|statue$|brick$|wall$|bar$|pickaxe|drill|hamaxe|helmet$|"
    r"breastplate$|chestplate$|greaves$|leggings$|robe$|hood$|mask$",
    re.IGNORECASE,
)
BUFF_CONTAMINATION_HINTS = re.compile(
    r"bookcase|banner$|statue$|brick$|wall$|bar$|pickaxe|drill|hamaxe|helmet$|"
    r"breastplate$|chestplate$|greaves$|leggings$|robe$|hood$|mask$",
    re.IGNORECASE,
)
CYRILLIC_PATTERN = re.compile(r"[\u0400-\u04FF]")

TERRARIA_BOSS_WIKI_ICON_OVERRIDES = {
    "Terraria/KingSlime": "assets/icons/terraria/bosses/king-slime-wiki.png",
    "Terraria/QueenSlimeBoss": "assets/icons/terraria/bosses/queen-slime-wiki.png",
    "Terraria/MoonLordCore": "assets/icons/terraria/bosses/moon-lord-wiki.png",
    "Terraria/Deerclops": "assets/icons/terraria/bosses/deerclops-wiki.png",
    "Terraria/DD2DarkMageT1": "assets/icons/terraria/bosses/dark-mage-wiki.png",
    "Terraria/DD2OgreT2": "assets/icons/terraria/bosses/ogre-wiki.png",
    "Terraria/DD2Betsy": "assets/icons/terraria/bosses/betsy-wiki.png",
}

CALAMITY_FORBIDDEN_BOSS_SEGMENTS = {
    "CalamityMod/StormWeaverBody",
    "CalamityMod/StormWeaverTail",
    "CalamityMod/ThanatosBody1",
    "CalamityMod/ThanatosBody2",
    "CalamityMod/ThanatosTail",
    "CalamityMod/AresGaussNuke",
    "CalamityMod/AresLaserCannon",
    "CalamityMod/AresPlasmaFlamethrower",
    "CalamityMod/AresTeslaCannon",
    "CalamityMod/Apollo",
    "CalamityMod/Artemis",
    "CalamityMod/AquaticScourgeBody",
    "CalamityMod/AquaticScourgeBodyAlt",
    "CalamityMod/AquaticScourgeTail",
}
CALAMITY_CRITICAL_RU_IDS = {
    "CalamityMod/AuricTeslaBodyArmor",
    "CalamityMod/AuricTeslaCuisses",
    "CalamityMod/AuricTeslaHeadMagic",
    "CalamityMod/AuricTeslaHeadMelee",
    "CalamityMod/AuricTeslaHeadRanged",
    "CalamityMod/AuricTeslaHeadRogue",
    "CalamityMod/AuricTeslaHeadSummon",
}
WAVE2_MODS = {"Fargowiltas", "FargowiltasSouls", "FargowiltasDLC", "FargowiltasSoulsDLC"}


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def load_registry() -> list[dict]:
    require(REGISTRY_PATH.exists(), "supported/mods.registry.json is missing")
    payload = read_json(REGISTRY_PATH)
    mods = payload.get("mods", [])
    require(isinstance(mods, list) and mods, "supported/mods.registry.json has no mods list")

    ids = []
    for row in mods:
        mod_id = str(row.get("id") or "").strip()
        require(mod_id, "mods.registry contains an entry without id")
        ids.append(mod_id)
    require(len(ids) == len(set(ids)), "mods.registry contains duplicated mod ids")
    require("Terraria" in ids, "mods.registry must include Terraria")
    return mods


def support_file(mod_name: str, filename: str) -> Path:
    return ROOT / "supported" / mod_name / filename


def validate_item_categories(mod_name: str, rows: list[dict]) -> None:
    weapon_tools = [
        row["id"]
        for row in rows
        if row.get("category") == "weapon" and WEAPON_CONTAMINATION_HINTS.search(str(row.get("internalName", "")))
    ]
    contaminated_accessories = [
        row["id"]
        for row in rows
        if row.get("category") == "accessory" and ACCESSORY_CONTAMINATION_HINTS.search(str(row.get("internalName", "")))
    ]
    contaminated_buffs = [
        row["id"]
        for row in rows
        if row.get("category") == "buff"
        and BUFF_CONTAMINATION_HINTS.search(str(row.get("internalName", "")))
        and row.get("internalName") not in {"WarTable"}
    ]

    require(not weapon_tools, f"{mod_name}: tools/decor leaked into weapons: {', '.join(weapon_tools[:20])}")
    require(not contaminated_accessories, f"{mod_name}: non-accessory entries leaked into accessories: {', '.join(contaminated_accessories[:20])}")
    require(not contaminated_buffs, f"{mod_name}: non-buff entries leaked into buffs: {', '.join(contaminated_buffs[:20])}")


def validate_search_content(mod_name: str, entries: list[dict], bosses_subset: list[dict], strict_required: bool) -> None:
    require(entries or not strict_required, f"{mod_name}: search-content is empty")

    rows_by_id: dict[str, list[dict]] = {}
    for row in entries:
        content_id = str(row.get("id") or "")
        if content_id:
            rows_by_id.setdefault(content_id, []).append(row)

    for row in entries:
        content_id = str(row.get("id") or "")
        kind = str(row.get("kind") or "").lower()
        category = row.get("category")
        icon = str(row.get("icon") or "")

        if category is not None:
            require(category in STRICT_ITEM_CATEGORIES, f"{mod_name}: invalid category '{category}' for {content_id}")
            if category == "armor":
                require(row.get("armorMode") in {"set", "piece"}, f"{mod_name}: armorMode missing/invalid for {content_id}")
                require(bool(row.get("armorGroupKey")), f"{mod_name}: armorGroupKey missing for {content_id}")

        if kind in BOSS_LIKE_KINDS:
            require(row.get("bossColumn") in VALID_BOSS_COLUMNS, f"{mod_name}: invalid bossColumn for {content_id}")
            if row.get("bossPickerEligible"):
                require(bool(icon), f"{mod_name}: picker-eligible boss has no icon: {content_id}")
                require((ROOT / "docs" / icon).exists(), f"{mod_name}: boss icon file is missing on disk: {icon}")
                require(
                    str(row.get("canonicalBossId") or "") == content_id,
                    f"{mod_name}: picker-eligible boss must be canonical: {content_id} -> {row.get('canonicalBossId')}",
                )

    for boss in bosses_subset:
        content_id = str(boss.get("id") or "")
        rows = rows_by_id.get(content_id) or []
        row = next((candidate for candidate in rows if str(candidate.get("kind") or "").lower() in BOSS_LIKE_KINDS), None)
        require(row is not None, f"{mod_name}: bosses.json entry missing from search-content: {content_id}")
        require(row.get("bossPickerEligible"), f"{mod_name}: bosses.json entry is not picker-eligible in search-content: {content_id}")


def is_picker_visible(row: dict) -> bool:
    if row.get("pickerHidden"):
        return False
    return True


def localization_coverage(mod_name: str, entries: list[dict]) -> tuple[int, int, float]:
    if not entries:
        return 0, 0, 0.0
    visible = [row for row in entries if is_picker_visible(row)]
    localized = 0
    for row in visible:
        en = str(row.get("displayName") or "").strip()
        ru = str(row.get("displayNameRu") or "").strip()
        if ru and ru != en:
            localized += 1
    percent = (localized / max(1, len(visible))) * 100.0
    print(f"[coverage] {mod_name}: localized {localized}/{len(visible)} picker-visible ({percent:.1f}%)")
    return localized, len(visible), percent


def load_mod_localization_policy(mod_name: str) -> dict:
    supplement_path = support_file(mod_name, "supplement.json")
    if not supplement_path.exists():
        return {}
    supplement = read_json(supplement_path)
    policy = supplement.get("localizationPolicy", {})
    return policy if isinstance(policy, dict) else {}


def validate_mod_localization_policy(mod_name: str, entries: list[dict], policy: dict) -> None:
    rows_by_id = {str(row.get("id") or ""): row for row in entries if row.get("id")}
    threshold = float(policy.get("coverageThresholdPickerVisible", 0.0) or 0.0)
    _, visible_count, percent = localization_coverage(mod_name, entries)

    if threshold > 0:
        require(visible_count > 0, f"{mod_name}: no picker-visible entries to evaluate localization coverage")
        require(percent >= threshold * 100.0, f"{mod_name}: RU coverage {percent:.1f}% is below required {threshold * 100.0:.1f}%")

    critical_ids = [str(value) for value in policy.get("criticalRuIds", []) if str(value).strip()]
    missing_critical = [content_id for content_id in critical_ids if content_id not in rows_by_id]
    require(not missing_critical, f"{mod_name}: critical RU ids are missing in search-content: {', '.join(missing_critical[:20])}")

    bad_critical: list[str] = []
    for content_id in critical_ids:
        row = rows_by_id[content_id]
        en = str(row.get("displayName") or "").strip()
        ru = str(row.get("displayNameRu") or "").strip()
        if not ru or ru == en:
            bad_critical.append(content_id)
    require(not bad_critical, f"{mod_name}: critical entries must have localized displayNameRu: {', '.join(bad_critical[:20])}")


def validate_terraria_boss_icons() -> None:
    path = support_file("Terraria", "bosses.json")
    if not path.exists():
        return
    rows = {row["id"]: row for row in read_json(path).get("bosses", [])}
    for content_id, icon in TERRARIA_BOSS_WIKI_ICON_OVERRIDES.items():
        row = rows.get(content_id)
        require(row is not None, f"Missing Terraria boss entry: {content_id}")
        require(row.get("icon") == icon, f"{content_id} must use {icon}, got {row.get('icon')}")
        icon_path = ROOT / "docs" / icon
        require(icon_path.exists(), f"Missing Terraria boss icon file: {icon}")
        raw = icon_path.read_bytes()
        width, height = struct.unpack(">II", raw[16:24])
        require(max(width, height) <= 128, f"{content_id} appears to use a sprite sheet ({width}x{height}): {icon}")


def validate_calamity_boss_picker() -> None:
    path = support_file("CalamityMod", "bosses.json")
    if not path.exists():
        return
    boss_rows = read_json(path).get("bosses", [])
    boss_ids = {row.get("id") for row in boss_rows}
    leaked = sorted(str(value) for value in (boss_ids & CALAMITY_FORBIDDEN_BOSS_SEGMENTS))
    require(not leaked, f"Calamity boss picker contains technical segments: {', '.join(leaked)}")
    require("CalamityMod/AquaticScourgeHead" in boss_ids, "Calamity boss picker is missing Aquatic Scourge")


def validate_calamity_critical_localization() -> None:
    path = support_file("CalamityMod", "search-content.json")
    if not path.exists():
        return

    rows = {str(row.get("id") or ""): row for row in read_json(path).get("entries", []) if row.get("id")}
    missing = sorted(content_id for content_id in CALAMITY_CRITICAL_RU_IDS if content_id not in rows)
    require(not missing, f"Calamity critical localization entries are missing: {', '.join(missing)}")

    not_localized: list[str] = []
    for content_id in sorted(CALAMITY_CRITICAL_RU_IDS):
        row = rows[content_id]
        display_name_ru = str(row.get("displayNameRu") or "").strip()
        if not CYRILLIC_PATTERN.search(display_name_ru):
            not_localized.append(content_id)
    require(not not_localized, f"Calamity critical entries lost RU localization: {', '.join(not_localized)}")


def validate_mod(mod_row: dict, promotion_mod: str | None = None) -> None:
    mod_name = str(mod_row.get("id") or "").strip()
    status = str(mod_row.get("status") or "planned").strip().lower()
    strict_required = status in OFFICIAL_STATUSES or (promotion_mod == mod_name)

    search_path = support_file(mod_name, "search-content.json")
    items_path = support_file(mod_name, "items.json")
    bosses_path = support_file(mod_name, "bosses.json")

    if strict_required:
        require(search_path.exists(), f"{mod_name}: official mod is missing search-content.json")
        require(items_path.exists(), f"{mod_name}: official mod is missing items.json")
        require(bosses_path.exists(), f"{mod_name}: official mod is missing bosses.json")
    elif not (search_path.exists() and items_path.exists() and bosses_path.exists()):
        return

    search_entries = read_json(search_path).get("entries", [])
    items_rows = read_json(items_path).get("items", [])
    bosses_rows = read_json(bosses_path).get("bosses", [])

    validate_item_categories(mod_name, items_rows)
    validate_search_content(mod_name, search_entries, bosses_rows, strict_required)
    localization_coverage(mod_name, search_entries)

    policy = load_mod_localization_policy(mod_name)
    if strict_required and mod_name in WAVE2_MODS:
        if "coverageThresholdPickerVisible" not in policy:
            policy["coverageThresholdPickerVisible"] = 0.85
        policy.setdefault("criticalRuIds", [])
    if strict_required and policy:
        validate_mod_localization_policy(mod_name, search_entries, policy)

    if mod_name == "Terraria" and strict_required:
        event_count = sum(1 for row in search_entries if str(row.get("kind") or "").lower() == "event")
        biome_count = sum(1 for row in search_entries if str(row.get("kind") or "").lower() == "biome")
        require(event_count >= 8, f"{mod_name}: expected at least 8 events in search-content, got {event_count}")
        require(biome_count >= 8, f"{mod_name}: expected at least 8 biomes in search-content, got {biome_count}")

    if strict_required:
        missing_item_icons = [
            str(row.get("id"))
            for row in items_rows
            if str(row.get("icon") or "").strip() == "" and not row.get("pickerHidden")
        ]
        require(not missing_item_icons, f"{mod_name}: picker-visible item rows are missing icons: {', '.join(missing_item_icons[:20])}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--promotion-mod", help="validate a planned mod with official-grade gates before promoting it")
    args = parser.parse_args()

    mods = load_registry()
    promotion_mod = str(args.promotion_mod or "").strip() or None
    if promotion_mod and promotion_mod not in {str(row.get("id")) for row in mods}:
        raise SystemExit(f"{promotion_mod}: unknown mod id in registry")

    for row in mods:
        validate_mod(row, promotion_mod=promotion_mod)

    status_by_mod = {str(row.get("id")): str(row.get("status") or "").lower() for row in mods}
    if status_by_mod.get("Terraria") in OFFICIAL_STATUSES or promotion_mod == "Terraria":
        validate_terraria_boss_icons()
    if status_by_mod.get("CalamityMod") in OFFICIAL_STATUSES or promotion_mod == "CalamityMod":
        validate_calamity_boss_picker()
        validate_calamity_critical_localization()

    print("Support data validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
