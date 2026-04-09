import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUIDES_DIR = ROOT / "guides"
CATALOG_DIR = ROOT / "catalog"


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, ensure_ascii=True) + "\n"
    path.write_text(text, encoding="utf-8")


def build_index() -> dict:
    popularity = read_json(CATALOG_DIR / "popularity.json").get("scores", {})
    entries = []

    for path in sorted(GUIDES_DIR.glob("**/guide.json")):
        guide = read_json(path)
        entries.append({
            "id": guide["id"],
            "title": guide["title"],
            "author": guide["author"],
            "language": guide["language"],
            "summary": guide["summary"],
            "requiredMods": guide["requiredMods"],
            "classTags": guide["classTags"],
            "guideTags": guide.get("guideTags", []),
            "updatedAt": guide["updatedAt"],
            "stageCount": len(guide.get("stages", [])),
            "path": path.relative_to(ROOT).as_posix(),
            "popularity": int(popularity.get(guide["id"], 0))
        })

    return {
        "catalogSchemaVersion": 1,
        "guides": entries
    }


def build_version(index: dict) -> dict:
    dates = [guide["updatedAt"] for guide in index["guides"]]
    return {
        "catalogSchemaVersion": 1,
        "guideCount": len(index["guides"]),
        "latestGuideUpdatedAt": max(dates) if dates else None,
        "indexPath": "catalog/index.json"
    }


def assert_same(path: Path, expected: dict) -> None:
    actual = read_json(path)
    if actual != expected:
        raise SystemExit(f"{path.relative_to(ROOT)} is out of date. Run python tools/build_catalog.py")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if generated catalog files are outdated")
    args = parser.parse_args()

    index = build_index()
    version = build_version(index)

    if args.check:
        assert_same(CATALOG_DIR / "index.json", index)
        assert_same(CATALOG_DIR / "version.json", version)
        print("Catalog files are up to date.")
        return 0

    write_json(CATALOG_DIR / "index.json", index)
    write_json(CATALOG_DIR / "version.json", version)
    print(f"Built catalog with {len(index['guides'])} guide(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
