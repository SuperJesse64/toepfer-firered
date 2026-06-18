# Toepfer sprite source art

Numbered PNGs used to build battle sprites. Naming: `NNN_NAME.png` (dex number + in-game name).

| Folder | Role |
|--------|------|
| `front/` | 64×64 front battle art (151 files) |
| `back/` | 64×64 back battle art (`NNN_NAME_BACK.png` or `_BACKS.png`) |

Import into the ROM with:

```powershell
python tools/import_toepfer_sprites.py
```

This writes DMG-ready PNGs to `gfx/pokemon/front/` and `gfx/pokemon/back/`, and syncs names in `docs/toepfer-dex.csv`.

## Known gaps in source art

- **#119 seaking** — no front file; import falls back to #118 until `119_BIGFISH.png` is added
- **#134 vaporeon** — duplicate `134_FISHY.png` and `134_TIDAL.png` (import uses FISHY)
- **#139 omastar** — `ANCIENT_SHELL` is 13 chars; in-game name is truncated to `ANCIENTSHE`
