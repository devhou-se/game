# Item icons

Every shop / inventory item has an icon in the buy and sell lists, the Items
screen and the HUD effect chips. With no art here they are drawn in code at
16x16 by `src/ItemIcons.js` from the item's `icon: { shape, colors }`.

To replace one with real art, no code change needed:

1. Save a square PNG (16x16 art, or any multiple of it; transparent background)
   as `<item id>.png` in this folder — the id from `Shop.DEFAULT_ITEMS` or, for
   fish, `Fishing.CATCHES` (`zone-energy.png`, `koi.png`, ...).
2. Add the id to `manifest.json`: `{ "icons": ["zone-energy", "koi"] }`.

Only listed ids are requested, so an item without art never 404s. The PNG is
loaded under the texture key `item-<id>`, the same key the drawn icon would
use, and is shown at 32x32.
