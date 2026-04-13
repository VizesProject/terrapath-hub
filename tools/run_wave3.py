import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "supported" / "mods.registry.json"
WAVE_NUMBER = 3
RUS_DOCS_LOWER = "\u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u044b"
RUS_DOCS_TITLE = "\u0414\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u044b"
DOCUMENTS_DIR_NAMES = {"documents", RUS_DOCS_LOWER}


def run_python(args: list[str]) -> None:
    subprocess.run([sys.executable, *args], check=True, cwd=ROOT)


def read_registry_wave_mods() -> list[str]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    mods = payload.get("mods", [])
    return sorted(
        [
            str(mod.get("id") or "").strip()
            for mod in mods
            if int(mod.get("rolloutWave") or -1) == WAVE_NUMBER and str(mod.get("id") or "").strip()
        ],
        key=str.lower,
    )


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


def find_export_dir(mod_name: str) -> Path | None:
    lowered = mod_name.strip().lower()
    for root in export_roots():
        if not root.exists():
            continue
        for child in root.iterdir():
            if child.is_dir() and child.name.lower() == lowered:
                return child
    return None


def read_modlist() -> set[str] | None:
    for root in export_roots():
        modlist_path = root / "modlist.json"
        if not modlist_path.exists():
            continue
        payload = json.loads(modlist_path.read_text(encoding="utf-8"))
        names = {
            str(name).strip()
            for name in payload.get("mods", [])
            if str(name).strip()
        }
        return names
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--promote", action="store_true", help="promote mods that pass validation to official")
    args = parser.parse_args()

    wave_mods = read_registry_wave_mods()
    if not wave_mods:
        print("Wave 3 has no mods in mods.registry.json.")
        return 0

    modlist = read_modlist()
    if modlist is None:
        print("modlist.json not found; preflight will rely on export folders only.")
    else:
        print(f"Loaded modlist.json with {len(modlist)} mod ids.")

    skipped: list[tuple[str, str]] = []
    failed: list[tuple[str, str]] = []
    passed: list[str] = []

    for mod_name in wave_mods:
        export_dir = find_export_dir(mod_name)
        if export_dir is None:
            skipped.append((mod_name, "export folder not found"))
            continue

        if modlist is not None and mod_name not in modlist:
            skipped.append((mod_name, "missing in modlist.json"))
            continue

        print(f"\n=== Wave 3 build: {mod_name} ===")
        try:
            run_python(["tools/build_support_pack.py", "--mod", mod_name])
            run_python(["tools/generate_critical_ru_list.py", "--mod", mod_name])
            run_python(["tools/validate_support_data.py", "--promotion-mod", mod_name])
            passed.append(mod_name)
        except subprocess.CalledProcessError as exc:
            failed.append((mod_name, f"command failed with exit code {exc.returncode}"))
        except Exception as exc:  # pragma: no cover
            failed.append((mod_name, str(exc)))

    promoted: list[str] = []
    if args.promote and passed:
        print("\n=== Wave 3 promotion ===")
        for mod_name in passed:
            try:
                run_python(["tools/promote_mod_official.py", "--mod", mod_name])
                promoted.append(mod_name)
            except subprocess.CalledProcessError as exc:
                failed.append((mod_name, f"promotion failed with exit code {exc.returncode}"))
            except Exception as exc:  # pragma: no cover
                failed.append((mod_name, f"promotion failed: {exc}"))

    print("\nWave 3 summary:")
    print(f"- passed: {len(passed)}")
    if passed:
        print(f"  {', '.join(passed)}")
    print(f"- skipped: {len(skipped)}")
    for mod_name, reason in skipped:
        print(f"  {mod_name}: {reason}")
    print(f"- failed: {len(failed)}")
    for mod_name, reason in failed:
        print(f"  {mod_name}: {reason}")
    if args.promote:
        print(f"- promoted: {len(promoted)}")
        if promoted:
            print(f"  {', '.join(promoted)}")

    if failed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
