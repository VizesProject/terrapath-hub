import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "supported" / "mods.registry.json"
SUPPORTED_MODS_PATH = ROOT / "SUPPORTED_MODS.md"


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def run_python(args: list[str]) -> None:
    subprocess.run([sys.executable, *args], check=True, cwd=ROOT)


def update_supported_mods_doc(mod_id: str) -> None:
    if not SUPPORTED_MODS_PATH.exists():
        return
    lines = SUPPORTED_MODS_PATH.read_text(encoding="utf-8").splitlines()
    updated: list[str] = []
    marker = f"`{mod_id}`"
    for line in lines:
        if marker not in line or not line.strip().startswith("|"):
            updated.append(line)
            continue
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) >= 6:
            cells[4] = " Official "
            cells[5] = " Promoted after deterministic validation gates. "
            line = "|".join(cells)
        updated.append(line)
    SUPPORTED_MODS_PATH.write_text("\n".join(updated) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mod", required=True, help="mod internal id to promote")
    args = parser.parse_args()

    mod_id = str(args.mod).strip()
    registry = read_json(REGISTRY_PATH)
    mods = registry.get("mods", [])
    row = next((entry for entry in mods if str(entry.get("id")) == mod_id), None)
    if row is None:
        raise SystemExit(f"{mod_id}: mod id not found in supported/mods.registry.json")

    print(f"[promote] validating {mod_id} with official-grade gates")
    run_python(["tools/validate_support_data.py", "--promotion-mod", mod_id])
    run_python(["tools/validate_guides.py"])
    run_python(["tools/build_catalog.py"])

    row["status"] = "official"
    write_json(REGISTRY_PATH, registry)
    update_supported_mods_doc(mod_id)
    print(f"[promote] {mod_id} marked as official.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

