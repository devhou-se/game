# Occlusion: walking behind things

How scenery fades while a character stands hidden behind it (`src/systems/Occlusion.js`).

A "see X" in the text names a section; if it is not in this file, the index in [`../CLAUDE.md`](../CLAUDE.md) says which file has it.

### Walking behind things (issues #76 / #93)

Standing art is Y-sorted, so a character north of a roof, a tower, a torii top, a high-rise or a tree crown is
drawn under it. `src/systems/Occlusion.js` keeps them in view with one rule for every room, day or night:

- A character is **hidden** when art drawn over them (higher depth) covers more than half of their body
  with opaque pixels (12 sample points; coverage is read from a quarter-size alpha mask per texture, built
  the first time that texture is in the way — so the opening of a torii, the gap between Tokyo Tower's legs
  and the empty corners of a tree crown do not count).
- The pieces doing the covering **fade to 40%** (`Occlusion.ALPHA`, over `FADE_MS` = 160 ms) and come back
  when the character steps out. A building that is one sprite fades whole (Tokyo Tower, the Dotonbori arch
  and wheel, high-rises, house roofs), and so does a roof LAID FROM TILES (issue #172: Market's hall and
  its gate; it used to open a pale window of one to three tiles): a hit on a roof-part record
  (`Occlusion.ROOF_PARTS` - the families roofs are laid from - on an overhead layer) brings every part
  that touches it, directly or through other parts (`Occlusion.roof(rec)`: an edge in common, a corner
  alone is not enough), so the hall, the gate and each wing are one roof each. A roof is worked out the
  first time one of its tiles hides somebody, by walking outward through the chunk buckets, and kept on
  the records (`rec.roof`), which last as long as the room: no room scan at load or per frame (0.5 ms for
  the hall's 68 tiles, once). Tree crowns never group; add a family to `ROOF_PARTS` when a new roof is
  laid from tiles. Wall signs
  (`roomManager.signArt`) fade the same way.
- The character's **name label fades with them** (to `LABEL_ALPHA` = 60%, as much as the character shows
  through art at 40%) instead of floating over the roof at full strength. A label whose character stops being
  tested (an NPC that walks off camera) snaps back to full. Labels stay at depth 900 — they are never hidden by a tree in front of them — the fade
  is what says "behind". The player's own label (created characters only) and NPC labels follow the same rule.
- It applies to the player and to every NPC on camera, so a friend who wanders behind a roof is still
  findable. It is cheap: characters are only re-tested when they move, and only against the art of the
  4-cell chunks they stand in (`RoomManager.artNear`, the buckets tile streaming uses — built for every
  room) plus the room's wall signs; nothing scans the room per frame.
- The fade is stored on the tile RECORD (`rec.fade`), not the sprite, so a streamed sprite that is retired
  and re-made keeps it (`RoomManager.spawnTile` applies it). Code that sets a tile sprite's alpha for its
  own reasons would fight it — none does today.
- `GameScene.update` calls `occlusion.update()` right after `updateCharacterDepths()`. For a before/after
  look in the console: `game.scene.keys.GameScene.occlusion.enabled = false`.
- Indoors the same rule gives a room depth (issue #212): a shrine hall's pillars are 1x3 `Collidables` with only
  the foot solid, so the shaft cells are walked behind and the pillar fades; its hanging pieces are `Tops`
  under four rows tall, lifted in front of the taller thing behind them with a `depthBias` (the rope over the
  sanctuary, the bell rope in front of the offering box).
- **On furniture the player is not behind it** (issue #227, "Sitting on furniture" in `architecture.md`): on a
  bed, a sofa or any other solid seat `Seating.update()` re-sorts the player at the furniture's foot row, after
  `updateCharacterDepths()` and before `occlusion.update()`, so the furniture is under them and never counts as
  hiding them (only art with a higher depth does). The seat's `cover` - the blanket - is an image of
  Seating's own one depth step above the player, not a tile record: Occlusion does not know it and never
  fades it. It is a strip of the furniture the player is in by design; do not make a cover of anything tall.
- Layering consequences for maps: a walk-behind strip no longer hides anyone, so "the player vanishes
  behind X" is not a reason to add colliders any more (colliders are for where you cannot stand).
