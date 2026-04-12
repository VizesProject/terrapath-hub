import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STRICT_ITEM_CATEGORIES = ("weapon", "armor", "accessory", "buff")
DEFAULT_PER_CATEGORY = {
    "weapon": 16,
    "armor": 12,
    "accessory": 14,
    "buff": 12,
}


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def normalized_name(entry: dict) -> str:
    return str(entry.get("displayName") or entry.get("internalName") or entry.get("id") or "").lower()


def pick_critical_ids(entries: list[dict], per_category: dict[str, int]) -> list[str]:
    selected: list[str] = []

    boss_rows = sorted(
        [
            row
            for row in entries
            if str(row.get("kind") or "").lower() in {"boss", "miniboss"} and row.get("bossPickerEligible")
        ],
        key=normalized_name,
    )
    for row in boss_rows:
        content_id = str(row.get("id") or "").strip()
        if content_id and content_id not in selected:
            selected.append(content_id)

    for category in STRICT_ITEM_CATEGORIES:
        target = int(per_category.get(category, 0))
        if target <= 0:
            continue

        category_rows = sorted(
            [
                row
                for row in entries
                if not row.get("pickerHidden")
                and str(row.get("category") or "").strip().lower() == category
            ],
            key=normalized_name,
        )[:target]

        for row in category_rows:
            content_id = str(row.get("id") or "").strip()
            if content_id and content_id not in selected:
                selected.append(content_id)

    return selected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mod", required=True, help="mod internal id")
    parser.add_argument("--threshold", type=float, default=0.85, help="picker-visible RU coverage threshold (0..1)")
    args = parser.parse_args()

    mod_name = str(args.mod).strip()
    threshold = float(args.threshold)
    if threshold < 0 or threshold > 1:
        raise SystemExit("--threshold must be within 0..1")

    search_path = ROOT / "supported" / mod_name / "search-content.json"
    supplement_path = ROOT / "supported" / mod_name / "supplement.json"
    if not search_path.exists():
        raise SystemExit(f"{search_path.relative_to(ROOT)} is missing. Build support pack first.")
    if not supplement_path.exists():
        raise SystemExit(f"{supplement_path.relative_to(ROOT)} is missing.")

    search_payload = read_json(search_path)
    entries = search_payload.get("entries", [])
    if not isinstance(entries, list) or not entries:
        raise SystemExit(f"{search_path.relative_to(ROOT)} has no entries.")

    supplement = read_json(supplement_path)
    localization_policy = supplement.get("localizationPolicy")
    if not isinstance(localization_policy, dict):
        localization_policy = {}

    per_category = dict(DEFAULT_PER_CATEGORY)
    user_per_category = localization_policy.get("criticalPerCategory")
    if isinstance(user_per_category, dict):
        for key, value in user_per_category.items():
            try:
                per_category[str(key).strip().lower()] = int(value)
            except Exception:
                continue

    critical_ids = pick_critical_ids(entries, per_category)
    localization_policy["coverageThresholdPickerVisible"] = threshold
    localization_policy["criticalRuIds"] = critical_ids
    localization_policy["criticalPerCategory"] = per_category
    supplement["localizationPolicy"] = localization_policy

    write_json(supplement_path, supplement)
    print(
        f"{mod_name}: generated critical RU list with {len(critical_ids)} ids "
        f"(bosses + category picks), threshold={threshold:.2f}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

