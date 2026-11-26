# HUD, input, small viewports, cameras and touch

The HUD bar, the key bindings, and everything about showing the game on phones, tablets and small windows: canvas layout, the three cameras and world zoom, overlay rules, touch controls, hint wording.

A "see X" in the text names a section; if it is not in this file, the index in [`../CLAUDE.md`](../CLAUDE.md) says which file has it.

### HUD System

Semi-transparent bar at top showing: `{game.title} | {room name} | {game.date}` with clickable menu button
- The room segment is the room's display `name` from config, never its key (`GameScene.hudRoomName()`, the
  one place that decides it; falls back to the key for a room with no name). Generated interiors get a
  human name from their generator: `7-Eleven · Sapporo` (`generate_konbinis.py` `store_name()`, numbered
  only where a host has several stores: `7-Eleven · Market 3`), `Don Takote · Osaka`
  (`generate_discount_stores.py` `store_name()`), `Sapporo Station` (`generate_stations.py`
  `station_name()`). Nothing reads `room.name` as an identifier - room keys are the identifiers.
- Every separator on the bar is ` | ` (issue #207): a name's own ` · ` is written as one (`hudName()` in
  `NpcStates.js`, called by `hudRoomName()`), so `7-Eleven · Park 1` reads `7-Eleven | Park 1` on the bar, and
  the lead-in countdown is `devhouse 3 in 8d | February 10 2027` (`Trips.dateLabel`). The stored name keeps
  its dot everywhere else (the Map, the shop panel, the generators).
- Inside the stitched city the "room" is the district underfoot (`roomManager.currentDistrict()`, kept in
  `hudDistrict`), so the segment changes as you cross from one district into the next
- Title and date loaded from `config.json`
- Uses `window.devicePixelRatio` for retina display text rendering
- Fixed to camera with `setScrollFactor(0)`
- Depth 1000+ to render above game elements
- Menu button (right-aligned) opens MenuManager on click

### Input Handling
The whole game runs on WASD/arrows + SPACE/ENTER + SHIFT, with ESC as the single
system key — no other bindings (no T shortcut, no ,/. month keys). Touch controls
synthesize the same keys (d-pad → WASD, A → SPACE, B → ESC, sprint pill → SHIFT).
- **Movement**: WASD or arrows move 1 cell, Shift doubles speed (not distance)
- **Time Travel**: arrows / WASD move a day or a week, SHIFT + left/right jumps to the previous / next trip, SHIFT + up / down to today / the game's day,
  SPACE/ENTER travels, ESC closes
- **Menu / overlays**: ESC toggles the menu (and closes any overlay), W/S or ↑/↓ navigate, SPACE/ENTER activates
- **Dialogue**: SPACE/ENTER advances, ESC closes
- **Title screen**: SPACE/ENTER/ESC or a tap starts the game (`?notitle=1` skips the screen)
- **Intro**: SPACE/ENTER or a tap turns the page, ESC skips (`?nointro=1` skips the first-visit intro)
- **Character creator**: ↑/↓ pick a row, ←/→ change it, ENTER/SPACE plays, ESC cancels. RANDOM is the last
  row (←/→ re-rolls, or click/tap it) — it has no key of its own (#53). ENTER/SPACE plays on that
  row too (deliberate: the roll you like is kept with the usual key; if ENTER rolled there it would
  throw the look away)
- **Hidden debug menu**: triple-press backtick (``` within a second) — rows for
  the grid view/inspector, the N/E/X flag keys, map-click travel, a time-of-day
  pin (AUTO/day/dusk/night/dawn, same effect as `?tod=`), exact wallet amount
  (prompt), fast hunger (the energy meter drains `Energy.DEBUG_FACTOR` times as fast, to test it; the
  one row that is not saved, so it is off on every load) and noclip (all default off, persisted in localStorage). Deliberately
  absent from How to Play. Map-click travel on the menu's Map overlay
  only works when its toggle is on.
- Input blocked when `player.isMoving` or `isTransitioning`
- Supports diagonal movement with simultaneous key presses

### Small Viewports and Touch (issues #49, #50, #57, #81, #85, #110-#114, #116)
The game always renders 1280x960; everything below is about showing that on anything else. A
1280x960-or-larger window driven by mouse and keyboard is untouched by all of it (pixel-identical).

**The layout rule, per kind of window** (canvas size is never traded for controls):

| window | canvas | touch controls | world | text floor |
|---|---|---|---|---|
| desktop (>= 1280x960) | 1:1 or a whole multiple, centred both ways | none | as authored | as authored |
| small desktop / laptop window | exact fit, centred | none | as authored (never zoomed: all 20 x 15 cells stay in view) | overlays magnified to desktop size or the canvas; HUD >= ~11 CSS px |
| touchscreen laptop | same as the row above it would get | hidden until the screen is touched, gone again on a key press; when up, translucent over the canvas's bottom corners | same | same; keyboard wording until touched |
| tablet, 4:3-ish landscape | fills the window | translucent over the bottom corners (0.75x) | as authored | overlays kept clear of the controls |
| landscape phone | full height | in the side bars (0.8-1x); on phones under 400px tall, 0.6x and partly over the corners | 2x (10 x 7.5 cells) | HUD ~11 CSS px, hint lines and every other single line of overlay text >= 10 (667x375 and up) |
| portrait phone / tablet | fills the height above the controls; the window crops its sides (a tall slice, >= 560 canvas px wide) | under the canvas, full size | as authored in the slice (about 9.5 x 15 cells) | HUD ~11, hint lines >= 10; panels wider than the slice shrink to it (the 920px intro lands at ~7 CSS px body text) |

- **Canvas layout — `src/systems/Viewport.js`.** `Viewport.apply(game)` is the only place the canvas
  style is written (`src/game.js` calls it at boot, on window resize, on rotation and on
  `visualViewport` resize; `TouchControls` when its controls come or go). The canvas is
  `position: fixed` from the stylesheet on: a 1280px canvas in the page flow makes a phone browser
  widen its layout viewport, after which `window.innerWidth` is not the screen. Whole-integer scale
  when the window is big enough, exact fit otherwise, centred both ways. `Viewport.layout()` then
  places the controls — `portrait`, `side`, `bottom` or `over`, in that order of preference (see the
  file header) — and reports two things in canvas px that UIScale makes the game fit:
  `crop` (how much of the canvas is off each side of the window, portrait only) and `insets` (how far
  the controls reach in over the canvas, `over` only). `Viewport.CONTROLS` holds the controls'
  footprint — keep it in step with the stylesheet in `TouchControls._build`. `Viewport.current` is
  the layout in force.
- **Three layers, three cameras — `src/systems/UIScale.js` (`scene.uiScale`).** Nothing is given a
  second layout; instead, whenever the canvas is shown below 1:1, is cropped, or has controls over
  it, the picture is split by depth and each layer is drawn by its own camera:
  - **World** (everything else, main camera): on a phone or tablet only (`uiScale.handheld()`: a
    finger is the main pointer, or `?touch=1` — decided once per session, so a mouse/keyboard window
    of any size keeps all 20 x 15 cells and a touchscreen laptop does not jump when touched), zoomed
    in quarter steps towards 0.8x of authored size on screen, at most 2x and never to fewer than 8
    cells across (`worldScale()`). The follow deadzone is divided by the zoom, and its width scaled
    to a cropped (portrait) view, so the player keeps the same share of the view ahead of them. Use
    `camera.worldView` / `pointer.worldX`, never `scrollX + width`, and do not assume
    `cameras.main.x === 0`. A stitched city's chunk streaming (`RoomManager.streamRect`) and the
    lamp-halo cull (`DayNight.cullGlows`) already measure the zoomed, cropped view (centre
    `scrollX + width / 2`, half-size `width / 2 / zoom`); tiles streamed in mid-walk get their camera
    the same frame, because the split below is re-applied to the whole display list on `prerender`.
    A room whose `boundary` is narrower than that view (a konbini on a phone) is held centred in it:
    `GameScene.applyRoomBounds` narrows the camera bounds to the view around
    `roomManager.contentColumns()`, and runs again on scene event `'worldviewchange'` (zoom or view
    width changed). With the whole canvas in view the bounds are the room's, as always.
    Down the screen likewise when the view is zoomed in: a room no taller than the view
    (`roomManager.contentRows()`) is held in the part of it under the HUD bar (`GameScene.hudCover()`,
    world px) — centred there if it fits, else scrolling only from its back wall under the bar to its
    door (`RoomManager.heldRows`); `layoutHUD` re-applies the bounds when the bar's height changes.
    **Looking up at landmarks (issues #176 / #90) — `src/systems/LandmarkView.js` (`scene.landmarkView`).**
    The camera trails the player by the deadzone, so walking north leaves about five rows above them
    and the roof of an eight-row shrine hall, or most of a tower, is off the top of the screen. In
    front of a landmark MARKED AS DATA — config `game.lookUp.sprites`, `{sprite family: rows}`: the
    shrine halls, pagodas, torii, Tokyo Tower and Station, Tsutenkaku, the Dotonbori arch and wheel,
    Sapporo's two towers; never every tall sprite, so a high-rise, a tree or a house changes nothing —
    the world camera follows a point above the player (`cameras.main.followOffset.y`) with a
    narrower deadzone (`uiScale.setDeadzoneShare`), so the landmark's top comes to sit a quarter cell
    under the HUD bar. `rows` is how many cells of the building stand below the marked sprite (2 for
    a shrine's roof sprite and a torii's beam, 0 for a landmark that is one sprite); the reach is
    `lookUp.cells` cells south of that foot at full strength, fading out over `fade` more and over
    `side` cells to either side, and gone one cell behind the foot. The decision is the pure
    `LandmarkView.aim()` (`{weight, offset}`, continuous in the player's position: the camera pans as
    you walk in and out, there is no trigger edge) and is eased in time on top (`EASE_MS`); a room
    change, a train arrival and boot settle at once, under the fade (`landmarkView.reset()` from
    `RoomManager.applyRoomSwap`). It is capped so the player keeps `LandmarkView.FOOT` cells of view
    (plus any touch controls over the canvas) below them: on a phone (7.5 cells tall at 2x) or under
    a tower taller than the screen the camera shows as much as fits, not the top. Where the ordinary
    camera always shows the top nothing changes at all; where it only sometimes does (a torii) the
    deadzone narrows and the offset stays 0. A room's landmarks are indexed once per room load
    (`roomManager.landmarks`, from the tile records — a new landmark sprite is one more entry in
    `lookUp.sprites`), so a frame costs a loop over a dozen rectangles. `streamRect` covers the point
    the camera follows, so the rows it is about to show are streamed in. Never call
    `cameras.main.setDeadzone` to change the deadzone mid-game: it re-centres the camera on the
    player. Camera bounds still win: against a room's top edge (Machi under `?stitch=0`) the view
    stops there.
    The room-change fade (`RoomManager.switchRoom`) runs on the camera drawn last — the `'ui'`
    camera while the split is on — so it covers the HUD and overlays as the single camera's fade does.
  - **HUD** (depth 1000-1999 with scroll factor 0, `'hud'` camera): magnified from the top-left by
    `hudScale()` (towards 0.7x on screen). That leaves the bar less width, so `GameScene.layoutHUD()`
    lays it out for `cameras.main.width / hudZoom`: it drops the game's title, then — on a
    landscape phone, where the whole canvas is across the view and two rows are a lot of the height —
    abbreviates (`Nov 11 2025`, `shortGameDate`; then the room's name to its first part, `7-Eleven | Park 1`
    -> `7-Eleven`; then the date's year), and only then wraps date and wallet onto a second row. On a
    lead-in day that one row has no room for the countdown and the date, so there the countdown stands in
    place of the date — `Sapporo | devhouse 3 in 8 days | ¥5,000` at 844x390, `in 8d` at 667x375, the room
    abbreviated if that is what it takes (`Trips.countdown`, tried before the bare date); the segment is
    still the Time Travel button, which shows the date. A name too long for even `devhouse 3 soon` (a
    station) shows the date as on any other day; the portrait bar keeps countdown and date on its second row. `scene.hudWidth` / `scene.hudBarHeight` are the bar's size in HUD
    coordinates (the shop's energy meter and, under it, its effect chips hang off them, at the right
    end just under the bar, so the bar itself is never wider or taller for them); scene event `'hudscalechange'` says when to
    lay out again. Anything new on the HUD goes at depth 1000-1999, scroll factor 0. The date,
    wallet and `menu` buttons take a tap anywhere in the height of their row (`layoutHUD` sets their
    hit areas), not just on the glyphs, which are about 11 CSS px tall on a phone.
  - **Overlays** (depth >= 2000, `'ui'` camera): zoomed in on the overlay's content (everything
    except full-screen dimmers) until it is as big as on a desktop or fills its space — the view less
    a 12px margin, less the controls' `insets` (fitted between the controls or above them, whichever
    is bigger). A box too big for a space that is cut down (insets, or a cropped view) is shrunk to
    fit; otherwise overlays are never shrunk. Dimmers are stretched back over the whole view.
  - On a portrait phone all three cameras get the visible slice as their **viewport**, so
    `cameras.main.width` is the visible width (612 at 390x844) and `x` is not 0. Overlays built while
    that is so centre themselves in it; ones built for another width (the persistent menu and
    dialogue, anything left up while the phone is turned) are re-centred and fitted like any content.
    Read `cameras.main.width` when you draw, not once at construction, unless the thing is a
    full-screen dimmer.

  Rules this puts on overlay code:
  - Overlays live at depth 2000+, HUD at 1000-1999, world below. A new overlay gets all of the above
    for free.
  - Draw panels with Graphics `fillRect` / `strokeRect` / rounded rects / circles / triangles (their
    extents are tracked — Graphics has no bounds of its own) or any object with `getBounds()`.
  - Do not read raw `pointer.x` / `pointer.y` against overlay coordinates: use the handler's
    `localX` / `localY` (the map's click-to-travel does).
  - DOM placed over an overlay goes through `scene.uiScale.project(x, y)` and `.zoom`, and listens
    for the scene events `'uiscalechange'` AND `'inputmodechange'` (the character creator's name
    input does — from the layout the panel was drawn with, not a fresh one). The second matters on a
    big touch-capable window: the controls coming or going move the canvas with no window resize and
    no zoom change.
  - UIScale moves and scales three kinds of overlay object for the frame and puts them back
    (`UIScale.put` / `home`): dimmers, floats and hint lines. Do not tween the position or scale of
    those; alpha is fine.
  - Two per-object opt-outs: `obj.uiScaleSkip = true` for something at depth 2000+ that is NOT an
    overlay (the debug grid, flag labels and stats text — it stays with the world, or with the HUD
    if its scroll factor is 0); `obj.uiFloat = true` for something magnified but belonging to no
    overlay (the shop toast): it stays where it was authored on the canvas — except that a float
    which would cover the open overlay's content slides into the strip under (or over) the panel
    when one is tall enough to hold it (`UIScale.clearOf`). When neither is, the overlay gives up a
    strip under itself for it and keeps it until it closes, so a toast never sits on the panel's
    hint lines and the panel does not pulse.
  - **Hint lines never go below 10 CSS px** (`UIScale.MIN_HINT`): any overlay Text whose string came
    from `Hints.text` is scaled up in place (to at most 1.6x, and the panel's width) when its panel
    could not be magnified enough.
  - **Nor does any other single line of overlay text, on a landscape phone** (`UIScale.MIN_TEXT`, 10 CSS px,
    #200: under that the glyphs break up when the canvas is scaled down). A Text at overlay depth that is one
    line (no `\n`, no word wrap) grows in place about its origin, by at most a quarter
    (`MAX_TEXT_FLOOR_GROWTH`), never wider than its panel (`UIScale.textGrowth`) and never into the text
    beside it, which grows too (`UIScale.clearGrowth`, steps of 0.05). That is every panel at 667x375 and
    844x390 — the konbini's effect line and bottom row once a toast has shrunk the panel, the map's member
    names, the creator's FRONT / BACK, the dialogue's post caption — and most of the way at 568x320. A float
    that is a Text (the toast) is magnified to the same floor. Not in the cropped portrait view, and not
    wrapped or multi-line text, which cannot be re-flowed in place: keep paragraphs at 22px or more and
    single lines at 16px or more, and give a line room to grow about its origin.
  - An overlay that already fills the canvas cannot be magnified; its text can use
    `scene.uiScale.textSize('14px')` instead (the map's labels do — up to 1.6x). The HUD bar shows
    through a dimmer and is taller where it is magnified, so anything such an overlay draws near the
    top edge needs its own background there (the map's title gets one when `uiScale.hudZoom > 1`).
- **Touch in use, not touch available — `src/systems/TouchControls.js` (issue #116).** The controls
  show while touch is the input being used: a device whose main pointer is a finger
  (`(pointer: coarse)` — phones, tablets) starts with them, a touchscreen laptop does not; the first
  real `touchstart` anywhere brings them up and a real (trusted) press of a game key outside a text
  field takes them away, as often as the player switches. `?touch=1` forces them on.
  `touchControls.enabled` is "on screen now"; `setEnabled()` re-lays the canvas, rewords every hint
  on screen (`Hints.refresh`), redraws the intro's controls page and emits the scene event
  `'inputmodechange'`. Never test for touch capability anywhere else.
- **Hint wording — `src/utils/Hints.js`.** Write the hint for the keyboard and pass it through
  `Hints.text(scene, 'SPACE/ENTER: start · ESC: leave')`; with touch controls on it comes back as
  `A: start · B: leave` (SPACE/ENTER → A, ESC → B, ↑/↓ and arrows / WASD → d-pad, ←/→ → ◀ ▶, SHIFT → sprint, click → tap).
  `{ tap: true }` for overlays where a tap anywhere confirms (dialogue, intro): `TAP or A`. Use
  `Hints.touch(scene)` rather than testing `touchControls.enabled`. Never hand-write a touch string:
  every string `Hints.text` hands out is remembered, which is how a line already on screen is
  reworded when the input changes and how UIScale knows a hint line when it sees one. A hint must be
  its own Text object, set to exactly what `Hints.text` returned.
- **A touch on a control stays on the control.** Phaser listens for touches on the whole window, so
  a tap on the A button used to reach the overlay underneath as well (dialogue advanced twice, the
  intro skipped a page, B closed and reopened the menu). `TouchControls._own` default-prevents the
  touch events on every control, which Phaser's window handlers respect. Any new DOM control over
  the page needs the same.
- **"Rotate your phone" — `src/RotatePrompt.js` (`scene.rotatePrompt`, issues #111, #199).** Portrait
  phones get no layouts of their own (the owner's call); instead a touch-first device
  (`uiScale.handheld()`) held in portrait with a short side under 600 CSS px (`RotatePrompt.wanted`: never
  a desktop, a tablet or a touchscreen laptop) is shown "Rotate your phone for a better experience" for
  6 seconds. It is a toast, not an overlay: one `uiFloat` Text at depth 9500 where the shop's toast goes,
  not interactive and not in `InputHandler`'s overlay list, so the game is played under it as usual.
  A tap anywhere takes it down (and still does what it does: on the title it also starts the game); a
  turn to landscape takes it down at once. It shows over the **title screen** (first thing on every
  load, and before the creator and intro, which are what portrait shows worst) or over the plain world,
  never over anything else at overlay depth (`RotatePrompt.overlayUp`): it waits unspent for the world to
  be free and goes if an overlay opens under it, so no panel ever gives up a strip to it. Once per turn
  into portrait and `RotatePrompt.MAX` (2) times a session: `RotatePrompt.next` keeps
  `{shown, armed}` in sessionStorage `gamev2_rotate_prompt` (landscape re-arms), so a Time Travel reload
  does not replay it.
- **Testing**: playwright contexts with `hasTouch` AND `isMobile` (without `isMobile` the layout
  viewport never misbehaves the way a phone's does) at 844x390, 667x375, 390x844, 1024x768 and
  1366x1024; `page.touchscreen.tap` or CDP `Input.dispatchTouchEvent` for real touches (a d-pad press
  needs a held touch, not an instant tap). Headless Chrome with `hasTouch` reports a coarse pointer,
  so a touchscreen laptop needs `matchMedia('(pointer: coarse)')` stubbed to false. `?touch=1` shows
  the controls with a mouse. `tools/test_game.js` covers `Viewport.layout`, `UIScale.fit`, the hint
  registry and `TouchControls.touchFirst` without a browser.
