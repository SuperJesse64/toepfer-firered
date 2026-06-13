# Wizard front sprite — GBA hardware test

Verify all 151 Toepfer wizard front sprites on real GBA hardware (or emulator).

## What was added

An in-game battle loop in your bedroom (Pallet Town, 2F):

- **Location:** the posted notice on the east wall (top-right of the room, tile near the PC).
- **Mechanism:** each interaction battles the next species in dex order (#1 Bulbasaur → #151 Mew), showing the **enemy front sprite** in battle.
- **Progress:** stored in `VAR_TOEPFER_FRONT_SPRITE_TEST_INDEX` (`0x40F0`); wraps to #1 after #151.

Files:

| File | Purpose |
|------|---------|
| `data/scripts/wizard_front_sprite_test.inc` | Test script |
| `data/maps/PalletTown_PlayersHouse_2F/scripts.inc` | Hooks bedroom sign |
| `include/constants/vars.h` | Names the progress var |

## Get a `.gba` file

### Option A — GitHub Actions (recommended)

No local pret/agbcc toolchain is required. CI builds on every push to `main`/`master` and on manual dispatch.

1. **Commit and push** the wizard sprite import **and** this test (see suggested commit below). Your branch is currently **22 commits ahead** of remote with **uncommitted** sprite files — CI will not include those until pushed.

2. Open **Actions → Build Toepfer FireRed → Run workflow** (or push to trigger automatically).

3. When the run finishes, download the **`toepfer-firered-rom`** artifact (`pokefirered.gba`).

4. Flash `pokefirered.gba` to your cart (or open in mGBA / VisualBoyAdvance).

**Suggested commit message** (when you are ready to commit):

```
Deploy wizard front sprites and add in-game GBA sprite test.

Import wizard-test-front to all 151 species and hook a bedroom sign
battle loop so each species front sprite can be checked on hardware.
```

### Option B — Local build

Requires [pret/pokefirered](https://github.com/pret/pokefirered) toolchain (agbcc + arm-none-eabi). Not set up on this machine.

```bash
git clone https://github.com/pret/agbcc.git && cd agbcc && ./build.sh && ./install.sh ../
make -j$(nproc) firered
# Output: pokefirered.gba
```

## How to run the test in-game

1. Start a **New Game** (or use a save with at least one Pokémon).
2. Get your **starter from Prof. Oak** (the test refuses to run with an empty party).
3. Return to **your bedroom** (Pallet Town → your house → stairs → 2F).
4. Walk to the **notice on the east wall** (same tile as before; text now mentions the sprite test).
5. Press **A** → confirm **Yes** to battle.
6. In battle, check the **enemy front sprite** (wizard variant). Use **RUN** to exit quickly.
7. Talk to the notice again → next species (#2, #3, … #151).
8. After #151, the counter resets to #1.

**Tips**

- RUN is fastest; you do not need to win.
- Flee fails if your Pokémon is faster and attacks — use a weak/low-level lead or a status move if needed.
- To **restart at #1** mid-run: use an emulator save editor to set var `0x40F0` to `0`, or finish all 151 to wrap.

## What you are checking

Each species should show the **64×64 indexed wizard front** with:

- ≤ 16 colors, palette index 0 transparent
- Correct palette per species (`graphics/pokemon/<slug>/normal.pal`)
- No garbled tiles, wrong colors, or missing transparency

## Blockers

| Issue | Resolution |
|-------|------------|
| CI build missing new sprites | Commit + push `graphics/pokemon/*/front.png` and `.pal` changes |
| No `.gba` locally | Use CI artifact |
| “You need a Pokémon…” | Get starter from Oak first |
| Test not in ROM | Ensure `wizard_front_sprite_test.inc` is included in your build |

## Removing the test later

Revert the sign hook in `PalletTown_PlayersHouse_2F/scripts.inc`, remove the include from `event_scripts.s`, and delete `wizard_front_sprite_test.inc`.
