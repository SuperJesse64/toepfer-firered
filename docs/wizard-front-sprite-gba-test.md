# Wizard front sprite — see it in normal play

The wizard front sprite is deployed to **all 151 Kanto species** under `graphics/pokemon/<slug>/front.png`. No special test script is required — just play the game.

## Get a `.gba`

1. Push to `toepfer` `master` (or run **Actions → Build Toepfer FireRed** manually).
2. Download the **`toepfer-firered-rom`** artifact (`pokefirered.gba`).

## Where to look in-game

1. **New Game** → pick your starter from Prof. Oak.
2. **First rival battle** (Route 1, after leaving Pallet Town) — the rival's starter shows the **enemy front sprite** (wizard).
3. **Route 1 grass** — wild Pidgey/Rattata also use the wizard front sprite.

Your own starter shows its **back** sprite in battle; check any **wild or trainer Pokémon on the enemy side** for the wizard front.

## What you should see

Each species uses the same 64×64 indexed wizard front with per-species palette (`normal.pal`). No garbled tiles, wrong colors, or missing transparency.
