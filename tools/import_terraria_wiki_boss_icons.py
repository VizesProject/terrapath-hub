import json
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "docs" / "assets" / "icons" / "terraria" / "bosses"
WIKI_API = "https://terraria.wiki.gg/api.php"
USER_AGENT = "TerraPathHub/1.0 (+https://github.com/)"

# Canonical map-icon file pages used by Terraria wiki.gg.
ICON_SPECS: dict[str, str] = {
    "king-slime-wiki.png": "File:Map_Icon_King_Slime.png",
    "queen-slime-wiki.png": "File:Map_Icon_Queen_Slime.png",
    "moon-lord-wiki.png": "File:Map_Icon_Moon_Lord.png",
    "deerclops-wiki.png": "File:Map_Icon_Deerclops.png",
    "dark-mage-wiki.png": "File:Map_Icon_Dark_Mage.png",
    "ogre-wiki.png": "File:Map_Icon_Ogre.png",
    "betsy-wiki.png": "File:Map_Icon_Betsy.png",
}


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def resolve_file_url(file_title: str) -> str:
    query = urllib.parse.urlencode(
        {
            "action": "query",
            "titles": file_title,
            "prop": "imageinfo",
            "iiprop": "url",
            "format": "json",
        }
    )
    payload = fetch_json(f"{WIKI_API}?{query}")
    pages = payload.get("query", {}).get("pages", {})
    for page in pages.values():
        image_info = page.get("imageinfo") or []
        if image_info:
            return str(image_info[0].get("url") or "")
    raise RuntimeError(f"Could not resolve URL for {file_title}")


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for output_name, file_title in ICON_SPECS.items():
        url = resolve_file_url(file_title)
        data = fetch_bytes(url)
        output_path = OUTPUT_DIR / output_name
        output_path.write_bytes(data)
        print(f"Saved {output_path.relative_to(ROOT)} from {file_title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
