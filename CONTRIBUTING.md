# Contributing to TerraPath

Thanks for helping improve Terraria and tModLoader guides.

## Current contribution paths

- Report guide mistakes through a GitHub issue.
- Request support for a mod through a GitHub issue.
- Submit guide JSON through a pull request.
- Use the web editor once it is available on GitHub Pages.

## Guide requirements

- Guides must match `schema/guide.schema.json`.
- Every guide must have a unique `id`.
- Item, NPC, boss, and ore references should use stable IDs, not display names.
- Modded references should use `ModName/InternalName`.
- Guides should not include executable code, HTML, tracking scripts, or remote images.

## Language policy

Repository documentation, issue templates, and schema keys are written in English.

Guides can be written in any supported locale and are grouped by locale in `guides/`.

## Review policy

TerraPath is designed for community guides, but published catalog data should be
valid, readable, and useful to players. Maintainers may ask for edits before a
guide is added to the public catalog.
