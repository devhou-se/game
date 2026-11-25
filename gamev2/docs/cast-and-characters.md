# The cast: playable characters, members, interim sprites, blog authors

Playing as a cast member, `config.members`, `tools/generate_cast.py` and the blog author table (`AUTHOR_NPCS`).

A "see X" in the text names a section; if it is not in this file, the index in [`../CLAUDE.md`](../CLAUDE.md) says which file has it.

### Playing as the Cast: Character Menu and the Name Easter Egg (issues #15, #45)

`src/CharacterSelect.js` (Menu → Character) swaps the player to a cast member with a full sprite set
(`CharacterSelect.available(config)`: james, bailey, damian, dylan, julia, khoi, sam, xander — derived from
`spriteMetadata`, never listed in code). The whole swap lives in ONE
place, `CharacterSelect.become(scene, name)`: it writes `localStorage.gamev2_character = <name>`, swaps the
live player sprite, and calls `syncNpcPresence()` (that person's NPC leaves the world) and
`syncPlayerNameLabel()`. `CharacterSelect.applySaved` restores it on reload.

`src/CharacterCreator.js` (first-run, or Menu → Create Character) has an Easter egg on top of that: type one
of those names as your own (`castMatch()` — whole name, trimmed, case-insensitive; "baileyx" and the
sprite-less credits names Gloria/Yashuk do nothing) and the live preview flips to that person's own sprite,
the part/colour rows and RANDOM dim and lock, and a "hey, it's Bailey!" hint appears; it all reverts as soon
as the name stops matching. A creation that was already saved under one of those names opens as itself
(`eggArmed` is false until the name box is edited). START/ENTER then calls `CharacterSelect.become` and toasts "You are Bailey!"
instead of saving a composite. It deliberately skips `CharacterCreator.save()`, so an earlier creation in
`gamev2_custom_character` survives and is still offered as the custom row in Menu → Character.

### The Cast, and Interim Sprites for People Without Art (issue #117)

**The cast is data.** A cast member is a name with a full sprite set in `config.json` `spriteMetadata`
(`<name>_front`, `_back`, `_side`; 4 + 4 + 2 frames of 64x64 in `assets/sprites/<name>_<dir>_frame_<i>.png`).
`CharacterSelect.available(config)` derives the list, and everything playable reads it: Menu → Character,
the creator's name Easter egg, `syncNpcPresence` (you never meet yourself) and `tools/play.js as <name>`.
No code lists the names. The ONE explicit list is `config.json` top-level `members` (sprite base names;
shown alphabetically whatever order the list is written in: bailey, damian, dylan, julia, khoi, sam, xander) — the devhouse members, read through
`CharacterSelect.lineup(config)` by the title line-up ONLY (the intro's cast row and its sentence pass the game date's trip
members, `lineup(config, trip.members)` — `Intro.cast`, see Trips). A listed name with no
sprite set is skipped; a sprite set that is not listed never appears there (James is the default player
sprite and selectable, but not a member — issue #56). The line-ups size themselves for any
number (title: spacing and scale from the count; intro: the row closes up, then drops to 1x; the Character
menu's rows close up when the roster outgrows the screen).

**Devhouse 3** (Sapporo 18-25 Feb, Asahikawa 25-28 Feb) adds Khoi, Sam and Xander to Bailey, Damian, Dylan and
Julia. They have no hand-drawn sprites yet, so `tools/generate_cast.py` bakes INTERIM ones: the character
creator's composite (head / torso / legs / beard donors + recolours), run offline and saved as real PNGs.

```bash
/Library/Developer/CommandLineTools/usr/bin/python3 tools/generate_cast.py                # write frames, register
/Library/Developer/CommandLineTools/usr/bin/python3 tools/generate_cast.py --check        # exit 1 if stale
/Library/Developer/CommandLineTools/usr/bin/python3 tools/generate_cast.py --sheet x.png  # contact sheet, LOOK at it
```

- **The looks are one table**, `LOOKS` at the top of the tool (same shape as a creation saved by the
  creator, so a look can be designed in the game and copied over; the bake is what the creator
  previews). Today, all placeholders — nobody has
  described what they look like:

  | name | head | hair | top | legs | beard | skin |
  |---|---|---|---|---|---|---|
  | khoi | james | `#1a1208` black | damian, `#3a6fd8` blue | bailey, `#2b2b33` charcoal | none | `#f6c39a` |
  | sam | dylan | `#8a5a2b` light brown | bailey, `#7e4fc9` purple | julia, `#8a5a2b` brown | none | `#fdcba2` |
  | xander | james | `#b0491f` auburn | damian, `#d9d9d9` off-white | julia, `#032e48` navy | bailey's, `#b0491f` | `#f4bc8e` |

- **Faithful port, read not copied**: the compose is `CharacterCreator.composePixels` line for line (the DOM-free
  half of `composeFrame`), and
  `DONORS` / `BEARDS` / `CUTS` are parsed out of `src/CharacterCreator.js` at run time, so those tables
  cannot drift (the tool exits if it cannot find them). The output is pixel-identical to the creator's
  (a unit test composes every look with the game's code and compares it with the baked PNGs — change one
  side and port it to the other). Both carry five marked `TIDY` rules that remove
  the artefacts of a plain band cut between different donors: holes where the top donor shows its own trousers in the torso band
  (damian's hem), the stray outline of the head donor's own high sleeve (james, side frame 1), mouth-interior
  pixels recoloured as hair (dylan — a moustache that flickers with the walk cycle), an open shoulder
  line where the head donor's shoulders are narrower than the top worn, and what the top donor's own long hair
  leaves in the torso band (julia's top on another head: a stray strand of outline behind the shoulder in side
  view, and in back view a see-through hole over a dark band — the hole and the outline under it become shirt).
- **`dylan` as a top donor**: his shirt is a two-teal checker (both teals are in `DONORS.dylan.top`), so a
  recolour keeps the checker as two shades. It is solid: a unit test keeps every donor sprite hole-free.
- **Replacing an interim set with real art**: drop the ten hand-drawn PNGs over the generated ones (same file
  names, same 64x64 template as the rest of the cast) and delete that name from `LOOKS`, or the next run
  overwrites them. Nothing else changes. Generated sets are cast, not creator donors (`DONORS` holds the
  measured palettes of the hand-drawn five); a hand-drawn replacement can be added there.
- **Base NPCs** come from the same tool (`HOME`: room, cell, two placeholder lines that state no facts about
  anyone). They are added only while the room has no NPC of that name, so later edits and the blog pipeline's
  states are never undone. All three stand in Sapporo — Khoi by the station house (38,8), Sam on the Odori
  park path (21,27), Xander on the Clock Tower plaza (35,17) — and are marked `"trip": "devhouse3",
  "stay": "Sapporo"`, so they are there on devhouse 3's Sapporo days only (issue #131, see Trips), until
  their first post moves them. The rest of the devhouse 3 base cast (the other four in Sapporo, all seven
  in Asahikawa) is plain config data with the same marks.
- **Blog authors** (`AUTHOR_NPCS` in `tools/blog_to_npc.py`, GitHub login → NPC name): the three are listed
  under placeholder keys (`'<khoi github login>'`) because their logins are NOT known. A placeholder can never
  match a post (`is_login`: only login-shaped keys are looked up — letters, digits, inner hyphens, underscores, a
  `[bot]` suffix). Replace the key with the
  real lower-case login and that author's posts start placing their NPC. Until then — and for any other
  unknown author — the post is skipped with `WARNING: #<id>: blog author '<login>' is not mapped to an NPC`,
  which names the login to add, the file, and who is still waiting (also a `::warning::` annotation under
  GitHub Actions). `tools/test_blog_to_npc.py` covers mapped, unmapped and placeholder authors.
