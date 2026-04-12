import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WAVE2_MODS = ("Fargowiltas", "FargowiltasSouls", "FargowiltasDLC", "FargowiltasSoulsDLC")


def run(args: list[str]) -> None:
    subprocess.run([sys.executable, *args], check=True, cwd=ROOT)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mods", nargs="*", default=list(WAVE2_MODS), help="subset of wave2 mods to process")
    parser.add_argument("--promote", action="store_true", help="promote mods that pass validation to official")
    args = parser.parse_args()

    targets = [str(mod).strip() for mod in args.mods if str(mod).strip()]
    failures: list[tuple[str, str]] = []

    for mod_name in targets:
        print(f"\n=== Wave 2: {mod_name} ===")
        try:
            run(["tools/build_support_pack.py", "--mod", mod_name])
            run(["tools/generate_critical_ru_list.py", "--mod", mod_name])
            run(["tools/validate_support_data.py", "--promotion-mod", mod_name])
            if args.promote:
                run(["tools/promote_mod_official.py", "--mod", mod_name])
        except subprocess.CalledProcessError as exc:
            failures.append((mod_name, f"command failed with exit code {exc.returncode}"))
        except Exception as exc:  # pragma: no cover
            failures.append((mod_name, str(exc)))

    if failures:
        print("\nWave 2 finished with failures:")
        for mod_name, reason in failures:
            print(f"- {mod_name}: {reason}")
        return 1

    print("\nWave 2 completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

