import argparse
import json
import re
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_calamity_support as calamity
import build_terraria_support as terraria

try:
    from PIL import Image, ImageSequence
except ImportError:  # pragma: no cover - Pillow is expected in maintainer env
    Image = None
    ImageSequence = None

STRICT_ITEM_CATEGORIES = {"weapon", "armor", "accessory", "buff", "other"}
BOSS_LIKE_KINDS = {"boss", "miniboss"}
ITEM_LIKE_KINDS = {"item", "material", "ore", "other"}
VALID_BOSS_COLUMNS = {"miniboss", "prehardmode", "hardmode", "postmoonlord"}
WEAPON_CONTAMINATION_HINTS = re.compile(
    r"pickaxe|drill|hamaxe|fishingpole|aquarium|bowl|bookcase|statue|wall|platform|chest|dresser|table|chair|piano|clock|lamp",
    re.IGNORECASE,
)
ACCESSORY_CONTAMINATION_HINTS = re.compile(
    r"helmet$|breastplate$|chestplate$|greaves$|leggings$|robe$|hood$|mask$|brick$|banner$|bookcase|statue$|wall$|pickaxe|drill|hamaxe|bar$",
    re.IGNORECASE,
)
BUFF_CONTAMINATION_HINTS = re.compile(
    r"helmet$|breastplate$|chestplate$|greaves$|leggings$|robe$|hood$|mask$|brick$|banner$|bookcase|statue$|wall$|pickaxe|drill|hamaxe|bar$",
    re.IGNORECASE,
)

ARMOR_SUFFIXES = (
    "Helmet",
    "Helm",
    "Headgear",
    "Headpiece",
    "Mask",
    "Hood",
    "Visage",
    "Cowl",
    "Crown",
    "Cap",
    "Hat",
    "Breastplate",
    "Chestplate",
    "Chainmail",
    "Platemail",
    "Robe",
    "Shirt",
    "Tunic",
    "BodyArmor",
    "Greaves",
    "Leggings",
    "Cuisses",
    "Pants",
    "Kilt",
)
SEGMENT_SUFFIX_PATTERN = re.compile(
    r"(BodyAlt|Body\d*|Tail\d*|Tail|Segment\d*|Part\d*|Claw\d*|Arm\d*|Hand\d*|Wing\d*|Head\d+)$",
    re.IGNORECASE,
)
TECHNICAL_BOSS_HINTS = re.compile(
    r"(Projectile|Laser|Cannon|Gauss|Flamethrower|Turret|Missile|Drone|Mine|Spawner|Portal|Hook)$",
    re.IGNORECASE,
)
SUPPLEMENT_ICON_META_KEYS = {"iconSourceFile", "iconSourceMode"}
RUS_DOCS_LOWER = "\u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u044b"
RUS_DOCS_TITLE = "\u0414\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u044b"
DOCUMENTS_DIR_NAMES = {"documents", RUS_DOCS_LOWER}


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def assert_same(path: Path, expected: dict) -> None:
    if not path.exists():
        raise SystemExit(f"{path.relative_to(ROOT)} is missing. Run python tools/build_support_pack.py --mod {path.parent.name}")
    actual = read_json(path)
    if actual != expected:
        raise SystemExit(f"{path.relative_to(ROOT)} is out of date. Run python tools/build_support_pack.py --mod {path.parent.name}")


def slugify(value: str) -> str:
    lowered = value.strip().lower()
    chars = [character if character.isalnum() else "-" for character in lowered]
    return "-".join(filter(None, "".join(chars).split("-"))) or "entry"


def humanize_identifier(value: str) -> str:
    buffer: list[str] = []
    for index, character in enumerate(value):
        if index > 0 and character.isupper() and value[index - 1].isalnum() and not value[index - 1].isupper():
            buffer.append(" ")
        if character in {"_", "-"}:
            buffer.append(" ")
            continue
        buffer.append(character)
    return "".join(buffer).strip()


def normalize_kind(value: str | None) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"item", "material", "ore", "other", "boss", "miniboss", "npc", "event", "biome", "system"}:
        return normalized
    return "other"


def normalize_category(raw: dict) -> str:
    normalized = str(raw.get("category") or "").strip().lower()
    if normalized in STRICT_ITEM_CATEGORIES:
        return normalized
    if normalized == "ammo":
        return "buff"
    if normalized in {"material", "ore", "tool", "mount", "pet", "furniture"}:
        return "other"

    kind = normalize_kind(raw.get("kind"))
    tags = {str(tag).strip().lower() for tag in raw.get("tags", []) if str(tag).strip()}
    if "weapon" in tags:
        return "weapon"
    if "armor" in tags:
        return "armor"
    if "accessory" in tags:
        return "accessory"
    if "buff" in tags or "consumable" in tags:
        return "buff"
    if kind in {"material", "ore"}:
        return "other"
    if kind == "item":
        return "other"
    return "other"


def merge_tags(*tag_sets: list[str]) -> list[str]:
    merged: list[str] = []
    for tags in tag_sets:
        for tag in tags or []:
            value = str(tag).strip()
            if value and value not in merged:
                merged.append(value)
    return merged


def default_export_dir(mod_name: str) -> Path | None:
    candidates: list[Path] = []
    for root in export_roots():
        candidates.append(root / mod_name)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def export_roots() -> list[Path]:
    roots: list[Path] = []
    checked: set[Path] = set()

    for base in (Path.home() / "OneDrive", Path.home()):
        candidates: list[Path] = [base / "Documents", base / RUS_DOCS_TITLE]
        if base.exists():
            try:
                for child in base.iterdir():
                    if child.is_dir() and child.name.strip().lower() in DOCUMENTS_DIR_NAMES:
                        candidates.append(child)
            except OSError:
                pass

        for documents_dir in candidates:
            exports_path = documents_dir / "My Games" / "Terraria" / "tModLoader" / "Mods" / "Cache" / "TerraPath" / "Exports"
            if exports_path not in checked:
                checked.add(exports_path)
                roots.append(exports_path)
    return roots


def case_insensitive_export_dir(mod_name: str) -> Path | None:
    lowered = mod_name.strip().lower()
    for root in export_roots():
        if not root.exists():
            continue
        try:
            for child in root.iterdir():
                if child.is_dir() and child.name.lower() == lowered:
                    return child
        except OSError:
            continue
    return None


def resolve_export_dir(mod_name: str, explicit: str | None) -> Path:
    if explicit:
        resolved = Path(explicit).expanduser()
        if resolved.exists():
            return resolved
        raise SystemExit(f"Export directory does not exist: {resolved}")

    resolved = default_export_dir(mod_name)
    if resolved is None:
        resolved = case_insensitive_export_dir(mod_name)
    if resolved is None:
        raise SystemExit(f"No export directory found for {mod_name}. Run /terrapathexport mod {mod_name} first or pass --export-dir.")
    return resolved


def load_previous_entries(mod_name: str) -> dict[str, dict]:
    previous_path = ROOT / "supported" / mod_name / "search-content.json"
    if not previous_path.exists():
        return {}
    previous = read_json(previous_path)
    return {
        str(entry.get("id")): entry
        for entry in previous.get("entries", [])
        if entry.get("id")
    }


def copy_icon(mod_name: str, export_dir: Path, raw: dict, kind: str) -> str:
    icon_file = str(raw.get("iconFile") or "").strip()
    if not icon_file:
        return ""
    source_path = export_dir / icon_file
    if not source_path.exists():
        return ""

    folder = "items"
    if kind in BOSS_LIKE_KINDS:
        folder = "bosses"
    elif kind == "npc":
        folder = "npcs"

    mod_slug = slugify(mod_name)
    target_root = ROOT / "docs" / "assets" / "icons" / mod_slug / folder
    target_root.mkdir(parents=True, exist_ok=True)
    file_stem = slugify(str(raw.get("internalName") or raw.get("id") or source_path.stem))
    target_path = target_root / f"{file_stem}.png"
    shutil.copyfile(source_path, target_path)
    return target_path.relative_to(ROOT / "docs").as_posix()


def infer_armor_group(raw: dict, internal_name: str) -> str:
    explicit = str(raw.get("armorGroupKey") or raw.get("armorSetKey") or "").strip()
    if explicit:
        return slugify(explicit)
    for suffix in ARMOR_SUFFIXES:
        if internal_name.endswith(suffix) and len(internal_name) > len(suffix):
            return slugify(internal_name[: -len(suffix)])
    return slugify(internal_name)


def build_item_entry(mod_name: str, export_dir: Path, raw: dict, previous: dict | None = None) -> dict | None:
    content_id = str(raw.get("id") or "").strip()
    internal_name = str(raw.get("internalName") or "").strip()
    if not content_id or not internal_name:
        return None

    kind = normalize_kind(raw.get("kind")) if raw.get("kind") else "item"
    if kind not in ITEM_LIKE_KINDS:
        kind = "item"
    category = normalize_category(raw)
    display_name = str(raw.get("displayName") or humanize_identifier(internal_name)).strip() or humanize_identifier(internal_name)
    display_name_ru = str(raw.get("displayNameRu") or "").strip()
    if not display_name_ru and previous:
        display_name_ru = str(previous.get("displayNameRu") or "").strip()
    if not display_name_ru:
        display_name_ru = display_name

    icon = copy_icon(mod_name, export_dir, raw, kind)
    if not icon and previous:
        icon = str(previous.get("icon") or "")

    entry: dict = {
        "id": content_id,
        "kind": kind,
        "internalName": internal_name,
        "displayName": display_name,
        "displayNameRu": display_name_ru,
        "icon": icon,
        "category": category,
        "tags": merge_tags([str(tag) for tag in raw.get("tags", [])], [category]),
    }

    if category == "armor":
        armor_mode = str(raw.get("armorMode") or "").strip().lower()
        if armor_mode not in {"set", "piece"}:
            armor_mode = "set" if raw.get("armorSetKey") else "piece"
        entry["armorMode"] = armor_mode
        entry["armorGroupKey"] = infer_armor_group(raw, internal_name)

    if raw.get("pickerHidden") is True:
        entry["pickerHidden"] = True

    return entry


def build_npc_entry(mod_name: str, export_dir: Path, raw: dict, previous: dict | None = None) -> dict | None:
    content_id = str(raw.get("id") or "").strip()
    internal_name = str(raw.get("internalName") or "").strip()
    if not content_id or not internal_name:
        return None

    kind = normalize_kind(raw.get("kind"))
    if kind not in {"boss", "miniboss", "npc"}:
        kind = "boss" if raw.get("isBoss") else "npc"

    display_name = str(raw.get("displayName") or humanize_identifier(internal_name)).strip() or humanize_identifier(internal_name)
    display_name_ru = str(raw.get("displayNameRu") or "").strip()
    if not display_name_ru and previous:
        display_name_ru = str(previous.get("displayNameRu") or "").strip()
    if not display_name_ru:
        display_name_ru = display_name

    icon = copy_icon(mod_name, export_dir, raw, kind)
    if not icon and previous:
        icon = str(previous.get("icon") or "")

    entry: dict = {
        "id": content_id,
        "kind": kind,
        "internalName": internal_name,
        "displayName": display_name,
        "displayNameRu": display_name_ru,
        "icon": icon,
        "tags": merge_tags([str(tag) for tag in raw.get("tags", [])], [kind]),
    }

    if kind in BOSS_LIKE_KINDS:
        entry["bossPickerEligible"] = bool(raw.get("bossPickerEligible", True))
        entry["canonicalBossId"] = str(raw.get("canonicalBossId") or content_id)
        entry["bossColumn"] = str(raw.get("bossColumn") or ("miniboss" if kind == "miniboss" else "hardmode"))

    if raw.get("pickerHidden") is True:
        entry["pickerHidden"] = True

    return entry


def load_supplement(mod_name: str) -> dict:
    path = ROOT / "supported" / mod_name / "supplement.json"
    if not path.exists():
        return {}
    return read_json(path)


def _trim_transparent_bounds(image) -> "Image.Image":
    rgba = image.convert("RGBA")
    alpha_channel = rgba.getchannel("A")
    bounds = alpha_channel.getbbox()
    if bounds is None:
        return rgba
    return rgba.crop(bounds)


def _best_visible_frame(source_path: Path, mode: str):
    if Image is None or ImageSequence is None:
        raise SystemExit("Pillow is required for iconSourceFile processing. Install it with: python -m pip install pillow")

    with Image.open(source_path) as source_image:
        normalized_mode = mode.strip().lower()
        if normalized_mode in {"first-frame", "first"}:
            source_image.seek(0)
            return _trim_transparent_bounds(source_image.copy())
        if normalized_mode in {"last-frame", "last"}:
            last_frame = None
            for frame in ImageSequence.Iterator(source_image):
                last_frame = frame.copy()
            if last_frame is None:
                return _trim_transparent_bounds(source_image.copy())
            return _trim_transparent_bounds(last_frame)

        best_score = None
        best_frame = None
        for frame in ImageSequence.Iterator(source_image):
            candidate = _trim_transparent_bounds(frame.copy())
            alpha_histogram = candidate.getchannel("A").histogram()
            visible_alpha = sum(value * index for index, value in enumerate(alpha_histogram))
            visible_pixels = sum(alpha_histogram[1:])
            area = max(1, candidate.width * candidate.height)
            squareness_penalty = abs(candidate.width - candidate.height)
            score = (visible_alpha, visible_pixels, -area, -squareness_penalty)
            if best_score is None or score > best_score:
                best_score = score
                best_frame = candidate

        if best_frame is None:
            return _trim_transparent_bounds(source_image.copy())
        return best_frame


def _resolve_icon_source_path(raw_source_path: str) -> Path:
    source_path = Path(raw_source_path).expanduser()
    if not source_path.is_absolute():
        source_path = ROOT / source_path
    return source_path


def process_supplement_icon_sources(supplement_entries: list[dict]) -> None:
    for incoming in supplement_entries:
        if not isinstance(incoming, dict):
            continue
        source_value = str(incoming.get("iconSourceFile") or "").strip()
        if not source_value:
            continue

        icon_path = str(incoming.get("icon") or "").strip()
        if not icon_path:
            content_id = str(incoming.get("id") or "").strip() or "<unknown>"
            raise SystemExit(f"{content_id}: supplement entry with iconSourceFile must include icon output path")

        source_path = _resolve_icon_source_path(source_value)
        if not source_path.exists():
            content_id = str(incoming.get("id") or "").strip() or "<unknown>"
            raise SystemExit(f"{content_id}: iconSourceFile does not exist: {source_path}")

        output_path = ROOT / "docs" / icon_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        mode = str(incoming.get("iconSourceMode") or "best-visible-auto")
        frame = _best_visible_frame(source_path, mode)
        frame.save(output_path, format="PNG")


def apply_supplement_entries(entries_by_id: dict[str, dict], supplement_entries: list[dict]) -> None:
    process_supplement_icon_sources(supplement_entries)
    for incoming in supplement_entries:
        content_id = str(incoming.get("id") or "").strip()
        if not content_id:
            continue
        existing = entries_by_id.get(content_id, {})
        cleaned_incoming = {
            key: value for key, value in incoming.items()
            if key not in SUPPLEMENT_ICON_META_KEYS
        }
        merged = {**existing, **cleaned_incoming}

        if "tags" in cleaned_incoming:
            merged["tags"] = merge_tags(
                [str(tag) for tag in existing.get("tags", [])],
                [str(tag) for tag in cleaned_incoming.get("tags", [])],
            )
        entries_by_id[content_id] = merged


def apply_taxonomy_overrides(entries_by_id: dict[str, dict], supplement: dict) -> None:
    rules = supplement.get("taxonomyOverrides", {}) if isinstance(supplement, dict) else {}
    forced = rules.get("forcedCategories", {}) if isinstance(rules, dict) else {}
    blacklist = {str(value) for value in (rules.get("blacklist", []) if isinstance(rules, dict) else []) if value}

    for content_id in blacklist:
        entries_by_id.pop(content_id, None)

    for content_id, category in forced.items():
        entry = entries_by_id.get(str(content_id))
        if not entry:
            continue
        normalized_category = str(category).strip().lower()
        if normalized_category not in STRICT_ITEM_CATEGORIES:
            normalized_category = "other"
        entry["category"] = normalized_category
        entry["tags"] = merge_tags(
            [tag for tag in entry.get("tags", []) if str(tag).strip().lower() not in STRICT_ITEM_CATEGORIES],
            [normalized_category],
        )


def infer_auto_boss_canonical(content_id: str, entry: dict, entries_by_id: dict[str, dict]) -> str:
    explicit = str(entry.get("canonicalBossId") or "").strip()
    if explicit:
        return explicit

    internal_name = str(entry.get("internalName") or content_id.split("/")[-1]).strip()
    mod_prefix = content_id.split("/", 1)[0]

    if TECHNICAL_BOSS_HINTS.search(internal_name):
        return content_id

    if SEGMENT_SUFFIX_PATTERN.search(internal_name):
        base = SEGMENT_SUFFIX_PATTERN.sub("", internal_name)
        candidates = [
            f"{mod_prefix}/{base}Head",
            f"{mod_prefix}/{base}",
        ]
        for candidate in candidates:
            candidate_entry = entries_by_id.get(candidate)
            if not candidate_entry:
                continue
            candidate_kind = normalize_kind(candidate_entry.get("kind"))
            if candidate_kind in BOSS_LIKE_KINDS:
                return candidate

    if internal_name.endswith("Body") and len(internal_name) > len("Body"):
        base = internal_name[:-len("Body")]
        candidate = f"{mod_prefix}/{base}Head"
        candidate_entry = entries_by_id.get(candidate)
        if candidate_entry and normalize_kind(candidate_entry.get("kind")) in BOSS_LIKE_KINDS:
            return candidate

    return content_id


def apply_boss_normalization(entries_by_id: dict[str, dict], supplement: dict) -> None:
    rules = supplement.get("bossNormalization", {}) if isinstance(supplement, dict) else {}
    alias_map = {
        str(source): str(target)
        for source, target in (rules.get("aliasMap") or {}).items()
        if source and target
    }
    hidden_bosses = {str(value) for value in (rules.get("hiddenBosses") or []) if value}
    eligible_minibosses = {str(value) for value in (rules.get("eligibleMinibosses") or []) if value}
    column_map = {
        str(source): str(target)
        for source, target in (rules.get("columnMap") or {}).items()
        if source and target
    }
    display_overrides = rules.get("displayOverrides", {}) or {}

    for content_id, entry in entries_by_id.items():
        kind = normalize_kind(entry.get("kind"))
        if kind not in BOSS_LIKE_KINDS:
            continue

        canonical = alias_map.get(content_id, infer_auto_boss_canonical(content_id, entry, entries_by_id))
        entry["canonicalBossId"] = canonical

        if content_id in hidden_bosses:
            entry["bossPickerEligible"] = False
            entry["pickerHidden"] = True
        elif content_id in eligible_minibosses:
            entry["kind"] = "miniboss"
            entry["bossPickerEligible"] = canonical == content_id
            entry["pickerHidden"] = False
        elif canonical != content_id:
            entry["bossPickerEligible"] = False
            entry["pickerHidden"] = True
        else:
            entry["bossPickerEligible"] = bool(entry.get("bossPickerEligible", canonical == content_id))
            entry["pickerHidden"] = bool(entry.get("pickerHidden", False))

        entry["bossColumn"] = column_map.get(
            content_id,
            str(entry.get("bossColumn") or ("miniboss" if entry.get("kind") == "miniboss" else "hardmode")),
        )

    for content_id, values in display_overrides.items():
        entry = entries_by_id.get(str(content_id))
        if not entry:
            continue
        if not isinstance(values, dict):
            continue
        if values.get("displayName"):
            entry["displayName"] = str(values["displayName"])
        if values.get("displayNameRu"):
            entry["displayNameRu"] = str(values["displayNameRu"])


def enforce_entry_shape(entries_by_id: dict[str, dict]) -> None:
    for content_id, entry in list(entries_by_id.items()):
        kind = normalize_kind(entry.get("kind"))
        entry["kind"] = kind
        entry["id"] = content_id
        entry["internalName"] = str(entry.get("internalName") or content_id.split("/")[-1])
        entry["displayName"] = str(entry.get("displayName") or humanize_identifier(entry["internalName"]))
        display_name_ru = str(entry.get("displayNameRu") or "").strip()
        entry["displayNameRu"] = display_name_ru or entry["displayName"]
        entry["icon"] = str(entry.get("icon") or "")
        entry["tags"] = merge_tags([str(tag) for tag in entry.get("tags", [])], [kind])

        if kind in ITEM_LIKE_KINDS or entry.get("category"):
            category = str(entry.get("category") or "other").strip().lower()
            if category not in STRICT_ITEM_CATEGORIES:
                category = "other"
            entry["category"] = category
            entry["tags"] = merge_tags(
                [tag for tag in entry.get("tags", []) if str(tag).strip().lower() not in STRICT_ITEM_CATEGORIES],
                [category],
            )
            if category == "armor":
                armor_mode = str(entry.get("armorMode") or "").strip().lower()
                if armor_mode not in {"set", "piece"}:
                    armor_mode = "piece"
                entry["armorMode"] = armor_mode
                armor_group = str(entry.get("armorGroupKey") or "").strip()
                entry["armorGroupKey"] = armor_group or slugify(entry["internalName"])
            else:
                entry.pop("armorMode", None)
                entry.pop("armorGroupKey", None)

        if kind in BOSS_LIKE_KINDS:
            canonical = str(entry.get("canonicalBossId") or content_id)
            entry["canonicalBossId"] = canonical
            entry["bossPickerEligible"] = bool(entry.get("bossPickerEligible", canonical == content_id))
            boss_column = str(entry.get("bossColumn") or ("miniboss" if kind == "miniboss" else "hardmode"))
            if boss_column not in VALID_BOSS_COLUMNS:
                boss_column = "miniboss" if kind == "miniboss" else "hardmode"
            entry["bossColumn"] = boss_column
        else:
            entry.pop("canonicalBossId", None)
            entry.pop("bossPickerEligible", None)
            entry.pop("bossColumn", None)


def validate_categories(items_payload: dict, mod_name: str) -> None:
    rows = items_payload.get("items", [])
    weapon_tools = [
        row["id"]
        for row in rows
        if row.get("category") == "weapon" and WEAPON_CONTAMINATION_HINTS.search(str(row.get("internalName") or ""))
    ]
    contaminated_accessories = [
        row["id"]
        for row in rows
        if row.get("category") == "accessory" and ACCESSORY_CONTAMINATION_HINTS.search(str(row.get("internalName") or ""))
    ]
    contaminated_buffs = [
        row["id"]
        for row in rows
        if row.get("category") == "buff" and BUFF_CONTAMINATION_HINTS.search(str(row.get("internalName") or ""))
    ]
    if weapon_tools:
        raise SystemExit(f"{mod_name}: tools/decor leaked into weapon category: {', '.join(weapon_tools[:20])}")
    if contaminated_accessories:
        raise SystemExit(f"{mod_name}: non-accessory rows leaked into accessory category: {', '.join(contaminated_accessories[:20])}")
    if contaminated_buffs:
        raise SystemExit(f"{mod_name}: non-buff rows leaked into buff category: {', '.join(contaminated_buffs[:20])}")


def validate_bosses(bosses_payload: dict, mod_name: str) -> None:
    for row in bosses_payload.get("bosses", []):
        if str(row.get("canonicalBossId") or "") != str(row.get("id") or ""):
            raise SystemExit(f"{mod_name}: boss picker contains non-canonical row {row.get('id')}")
        if not str(row.get("icon") or "").strip():
            raise SystemExit(f"{mod_name}: selectable boss entry is missing icon {row.get('id')}")
        if row.get("bossColumn") not in VALID_BOSS_COLUMNS:
            raise SystemExit(f"{mod_name}: invalid bossColumn for {row.get('id')} -> {row.get('bossColumn')}")


def build_generic_pack(mod_name: str, export_dir: Path) -> tuple[dict, dict, dict]:
    items_path = export_dir / "items.json"
    npcs_path = export_dir / "npcs.json"
    if not items_path.exists() or not npcs_path.exists():
        raise SystemExit(f"{mod_name}: export is incomplete in {export_dir}. Expected items.json and npcs.json.")

    raw_items = read_json(items_path).get("items", [])
    raw_npcs = read_json(npcs_path).get("npcs", [])
    if not isinstance(raw_items, list) or not isinstance(raw_npcs, list):
        raise SystemExit(f"{mod_name}: export payload is invalid in {export_dir}. Expected JSON arrays for items and npcs.")
    if len(raw_items) == 0 or len(raw_npcs) == 0:
        raise SystemExit(
            f"{mod_name}: preflight failed. Export must contain both items and npcs (>0). Got items={len(raw_items)}, npcs={len(raw_npcs)}."
        )

    previous = load_previous_entries(mod_name)
    supplement = load_supplement(mod_name)

    entries_by_id: dict[str, dict] = {}
    for raw in raw_items:
        content_id = str(raw.get("id") or "")
        item_entry = build_item_entry(mod_name, export_dir, raw, previous.get(content_id))
        if item_entry:
            entries_by_id[item_entry["id"]] = item_entry

    for raw in raw_npcs:
        content_id = str(raw.get("id") or "")
        npc_entry = build_npc_entry(mod_name, export_dir, raw, previous.get(content_id))
        if npc_entry:
            entries_by_id[npc_entry["id"]] = npc_entry

    apply_supplement_entries(entries_by_id, supplement.get("entries", []) if isinstance(supplement, dict) else [])
    apply_taxonomy_overrides(entries_by_id, supplement)
    apply_boss_normalization(entries_by_id, supplement)
    enforce_entry_shape(entries_by_id)

    entries = sorted(
        entries_by_id.values(),
        key=lambda entry: (
            str(entry.get("kind") or ""),
            str(entry.get("displayName") or entry.get("internalName") or entry.get("id") or "").lower(),
        ),
    )

    search_payload = {
        "mod": mod_name,
        "contentType": "search-content",
        "entries": entries,
    }
    items_payload = {
        "mod": mod_name,
        "contentType": "items",
        "items": [
            {
                key: value
                for key, value in row.items()
                if key
                in {
                    "id",
                    "internalName",
                    "displayName",
                    "displayNameRu",
                    "category",
                    "icon",
                    "kind",
                    "tags",
                    "pickerHidden",
                    "armorMode",
                    "armorGroupKey",
                }
            }
            for row in entries
            if row.get("category") or row.get("kind") in ITEM_LIKE_KINDS
        ],
    }
    bosses_payload = {
        "mod": mod_name,
        "contentType": "bosses",
        "bosses": [
            {
                key: value
                for key, value in row.items()
                if key
                in {
                    "id",
                    "internalName",
                    "displayName",
                    "displayNameRu",
                    "icon",
                    "kind",
                    "tags",
                    "bossPickerEligible",
                    "canonicalBossId",
                    "bossColumn",
                }
            }
            for row in entries
            if row.get("kind") in BOSS_LIKE_KINDS
            and row.get("bossPickerEligible")
            and row.get("canonicalBossId") == row.get("id")
        ],
    }
    validate_categories(items_payload, mod_name)
    validate_bosses(bosses_payload, mod_name)
    return search_payload, items_payload, bosses_payload


def build_payloads_for_mod(mod_name: str, export_dir: str | None) -> tuple[dict, dict, dict]:
    if mod_name == "Terraria":
        return terraria.build_payloads()
    if mod_name == "CalamityMod":
        resolved = calamity.find_export_dir(export_dir)
        if resolved is None:
            raise SystemExit("No Calamity export directory found. Run /terrapathexport mod CalamityMod first or pass --export-dir.")
        return calamity.build_pack(resolved)

    resolved = resolve_export_dir(mod_name, export_dir)
    return build_generic_pack(mod_name, resolved)


def run(mod_name: str, export_dir: str | None, check: bool) -> int:
    search_payload, items_payload, bosses_payload = build_payloads_for_mod(mod_name, export_dir)
    target_dir = ROOT / "supported" / mod_name

    if check:
        assert_same(target_dir / "search-content.json", search_payload)
        assert_same(target_dir / "items.json", items_payload)
        assert_same(target_dir / "bosses.json", bosses_payload)
        print(f"{mod_name} support files are up to date.")
        return 0

    write_json(target_dir / "search-content.json", search_payload)
    write_json(target_dir / "items.json", items_payload)
    write_json(target_dir / "bosses.json", bosses_payload)
    print(f"Built {mod_name} support with {len(search_payload['entries'])} searchable entries.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mod", required=True, help="internal mod id, e.g. Terraria or CalamityMod")
    parser.add_argument("--check", action="store_true", help="fail if generated support files are outdated")
    parser.add_argument("--export-dir", help="optional path to a TerraPath export directory")
    args = parser.parse_args()
    return run(str(args.mod).strip(), args.export_dir, args.check)


if __name__ == "__main__":
    raise SystemExit(main())
