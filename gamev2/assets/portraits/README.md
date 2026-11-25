# Character portraits

Hand-drawn portrait art for the cast. Nothing is shipped here yet (the manifest is empty), so the
game falls back to art derived from the overworld sprites:

- **Dialogue** (`src/DialogueManager.js`): the head-and-shoulders band of `<name>_front_frame_0`
  at 5x inside the wooden frame on the dialogue panel's top-left corner.
- **Title screen** (`src/TitleScreen.js`): the whole front sprite at 5x in the cast line-up.

## Dropping in real art (no code change)

1. Save the portrait as `assets/portraits/<name>.png`, where `<name>` is the character's sprite
   name — the part before `_front` in its sprite key: `bailey`, `damian`, `dylan`, `james`, `julia`, `khoi`, `sam`, `xander`.
2. Add the name to `manifest.json`:

   ```json
   { "portraits": ["bailey", "julia"] }
   ```

Only names in the manifest are requested, so a character without a file never causes a 404; the
ones not listed keep the sprite-derived version. Characters can be added one at a time.

`portraits` must be a JSON array of names (letters, digits, `_`, `-`). Anything else is ignored and
the game behaves as if the manifest were empty. Do not list a name before its PNG exists: the game
still runs and falls back to the sprite, but the browser logs a 404 for the missing file.

## Format

- PNG, RGBA. A transparent background is fine (and recommended): in dialogue the frame's
  blue-grey backdrop (`#3a4a6e`) shows through; the title screen is near-black (`#0a0a12`).
- **Dialogue window is 240x200 px (6:5).** Draw a bust (head and shoulders, facing the viewer),
  with the shoulders running off the bottom edge. Recommended canvas sizes:
  - `240x200` — shown 1:1 (most detail)
  - `120x100` — shown at 2x
  - `48x40` — shown at 5x (same pixel size as the sprite-derived bust)
- Any other size is scaled to fit inside the window (whole-number scale when enlarging,
  nearest-neighbour — so keep it pixel art), centred horizontally and standing on the bottom edge.
- The same file is used in the title screen's cast line-up, fitted the same way into a 240x200
  slot standing on the cast's baseline — so it shows at the same scale in both places.
