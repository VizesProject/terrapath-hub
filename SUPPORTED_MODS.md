# Supported Mods

TerraPath uses curated content indexes for the web editor.

The in-game mod can resolve real item and NPC icons from installed mods, but the
web editor only knows about mods that are listed here and indexed in `supported/`.

## Support levels

| Level | Meaning |
| --- | --- |
| Official | Searchable in the editor, validated in guide submissions, intended to have icons. |
| Metadata-only | Searchable by internal ID and display name, icons may be missing. |
| Unsupported | Manual references only; guide validation may warn or fail. |

## Initial list

| Mod | Internal mod name | Status |
| --- | --- | --- |
| Terraria | `Terraria` | Metadata-only starter index |
| Calamity Mod | `CalamityMod` | Planned |
| Thorium Mod | `ThoriumMod` | Planned |

## Asset note

Third-party mod icons should only be published here when TerraPath has permission
or when the asset's license allows redistribution. Until then, the web editor can
show placeholders and the in-game mod can use textures from installed mods.
