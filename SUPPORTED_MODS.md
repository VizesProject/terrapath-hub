# Supported Content

TerraPath Hub uses deterministic generated packs from `supported/<Mod>/`.
The editor and guide renderer consume those packs directly and do not rely on
runtime category guessing.

## Support Matrix (Wave-Based)

| Wave | Source | Internal name | Web support | Notes |
| --- | --- | --- | --- | --- |
| 0 | Terraria | `Terraria` | Official | Canonical deterministic pack with curated wiki-first boss icons and full picker metadata. |
| 0 | Calamity Mod | `CalamityMod` | Official | Generated from local export + supplement normalization and canonical boss rules. |
| 1 | Thorium Mod | `ThoriumMod` | Metadata-only | Included in registry and onboarding pipeline, full deterministic pack is next. |
| 1 | Spirit Reforged | `SpiritReforged` | Planned | Onboarding uses the same deterministic pipeline and CI gates. |
|2|Fargo's Mutant Mod|`Fargowiltas`| Official | Promoted after deterministic validation gates. |
| 2 | Fargo's Souls Mod | `FargowiltasSouls` | Planned | Deterministic onboarding with canonical boss/miniboss rules. |
| 2 | Calamity - Fargo's Souls DLC | `FargowiltasCrossmod` | Planned | Internal name is validated via `/terrapath export modlist`. |
| 3 | Calamity Entropy | `CalamityEntropy` | Planned | Calamity addon wave with shared normalization contracts. |
| 3 | Calamity Fables | `CalamityFables` | Planned | Calamity addon wave with shared normalization contracts. |
| 3 | Calamity: Wrath of the Gods | `NoxusBoss` | Planned | Calamity addon wave with shared normalization contracts. |
| 3 | Calamity Catalyst | `CatalystMod` | Planned | Calamity addon wave with shared normalization contracts. |
| 3 | Calamity Infernum | `InfernumMode` | Planned | Calamity addon wave with shared normalization contracts. |
| 3 | Calamity: Hunt of the Old God | `CalamityHunt` | Planned | Calamity addon wave with shared normalization contracts. |
|4|The Stars Above|`StarsAbove`| Official | Promoted after deterministic validation gates. |
|4|Starlight River|`StarlightRiver`| Official | Promoted after deterministic validation gates. |

## Registry and Data Contracts

- `supported/mods.registry.json` is the canonical list of known mod ids, status,
  rollout wave, source policy, and icon strategy.
- Every deterministic support pack is generated into:
  - `supported/<Mod>/search-content.json`
  - `supported/<Mod>/items.json`
  - `supported/<Mod>/bosses.json`
- Every mod folder should include `supplement.json` with:
  - `entries`
  - `bossNormalization`
  - `taxonomyOverrides`

## Maintainer Rebuild Flow

1. Run `/terrapathexport modlist` in tModLoader to confirm exact internal ids.
2. Run `/terrapathexport mod <InternalModName>` for each mod you want to rebuild.
3. (Optional) Refresh curated wiki icon overrides where needed.
4. Run `python tools/build_support_pack.py --mod <InternalModName>`.
5. Run `python tools/generate_critical_ru_list.py --mod <InternalModName>`.
6. Run `python tools/validate_support_data.py --promotion-mod <InternalModName>`.
7. Promote per-mod: `python tools/promote_mod_official.py --mod <InternalModName>`.
8. Wave 3 batch mode: `python tools/run_wave3.py` (or `python tools/run_wave3.py --promote`).
9. Wave 4 batch mode: `python tools/run_wave4.py` (or `python tools/run_wave4.py --promote`).
10. Missing-mod policy for wave scripts: modules without export folders or absent in `modlist.json` are skipped and remain `planned`.

## Quality Gates

Validation is blocking for `Official` mods:

- no contamination in item categories (`weapon/accessory/buff`)
- no segmented or technical NPCs in boss picker
- selectable bosses must be canonical and icon-backed
- armor entries must carry deterministic metadata (`armorMode`, `armorGroupKey`)
- Wave 2 mods enforce `Critical+Coverage`: 100% critical RU list + at least 85% RU coverage for picker-visible entries.
