/**
 * ItemIcons — a small pixel-art icon for every shop / inventory item (issue #82).
 *
 * There is no icon art in the repo, so icons are drawn once into 16x16 canvas
 * textures (the way AmbientBoats draws its boats) and shown at 2x on a small
 * slot square. They are
 * data-first: an item declares
 *
 *     icon: { shape: 'can', colors: { a: '#2b3a8c', b: '#1c2660', c: '#ffe14a' } }
 *
 * where `shape` names one of the pixel maps in ItemIcons.SHAPES and `colors`
 * fills in that map's item colours (a = body, b = its shade, c / d = accents).
 * An item with no `icon` (a catalogue from config.json `shop.items`, say) gets
 * the default for its category — ItemIcons.DEFAULTS.
 *
 * Real art replaces a drawn icon with no code change: put `<item id>.png` in
 * assets/items/ and list the id in assets/items/manifest.json. GameScene
 * preloads it under the same texture key (`item-<id>`) and ensure() only draws
 * what is missing. Any square size works — icons are shown at a fixed size.
 */
class ItemIcons {
    static key(item) { return `item-${item.id}`; }

    /** The icon spec an item is drawn from: its own, else its category's. */
    static specFor(item) {
        const icon = item && item.icon;
        if (icon && ItemIcons.SHAPES[icon.shape]) return icon;
        const category = item && (item.category || (item.permanent ? 'gear' : (item.effect ? 'drink' : 'food')));
        return ItemIcons.DEFAULTS[category] || ItemIcons.DEFAULTS.gear;
    }

    /**
     * The icon as a 16x16 grid of CSS colours (null = transparent). Pure, so
     * the unit checks can look at every icon without a canvas.
     */
    static pixels(item) {
        const spec = ItemIcons.specFor(item);
        const palette = Object.assign({}, ItemIcons.PALETTE, spec.colors);
        return ItemIcons.SHAPES[spec.shape].map(row =>
            Array.from(row, ch => (ch === '.' ? null : (palette[ch] || palette.a))));
    }

    static buildTexture(item) {
        const S = ItemIcons.SIZE;
        const canvas = document.createElement('canvas');
        canvas.width = canvas.height = S;
        const ctx = canvas.getContext('2d');
        ItemIcons.pixels(item).forEach((row, y) => row.forEach((colour, x) => {
            if (!colour) return;
            ctx.fillStyle = colour;
            ctx.fillRect(x, y, 1, 1);
        }));
        return canvas;
    }

    /** Texture key for the item's icon, drawing it first if nothing is loaded under it. */
    static ensure(scene, item) {
        const key = ItemIcons.key(item);
        if (!scene.textures.exists(key)) scene.textures.addCanvas(key, ItemIcons.buildTexture(item));
        return key;
    }

    /**
     * An icon centred on (x, y) at `depth`, on its slot — the lighter square
     * that keeps the dark outlines readable on the dark panels. Returns
     * [slot, image] (a caller that owns their lifetime keeps both).
     */
    static add(scene, item, x, y, depth) {
        const half = ItemIcons.SLOT / 2;
        const slot = scene.add.graphics();
        slot.fillStyle(ItemIcons.SLOT_COLOUR, 1);
        slot.fillRect(-half, -half, ItemIcons.SLOT, ItemIcons.SLOT);
        const img = scene.add.image(0, 0, ItemIcons.ensure(scene, item));
        img.setDisplaySize(ItemIcons.DISPLAY, ItemIcons.DISPLAY);
        for (const o of [slot, img]) {
            o.setPosition(x, y);
            o.setScrollFactor(0);
            o.setDepth(depth);
        }
        return [slot, img];
    }
}

ItemIcons.SIZE = 16;        // art pixels
ItemIcons.DISPLAY = 32;     // on-screen px in lists and chips (2x)
ItemIcons.SLOT = 36;        // the square behind an icon
ItemIcons.SLOT_COLOUR = 0x3c3f55;

/** Colours every map can use; an item's `colors` add (or override) a, b, c, d. */
ItemIcons.PALETTE = {
    o: '#15151f',   // outline
    w: '#ffffff',   // highlight
    e: '#c9ced6',   // silver / light grey
    k: '#6b7280',   // mid grey
    a: '#b0b6c2', b: '#7d8492', c: '#e8eaee', d: '#9aa1ad',
};

/** What an item without an `icon` of its own shows. */
ItemIcons.DEFAULTS = {
    drink: { shape: 'can',  colors: { a: '#5aa0d8', b: '#3b6f9c', c: '#e8f2fa' } },
    food:  { shape: 'bun',  colors: { a: '#d9a45a', b: '#d9a45a', d: '#a8732f' } },
    gear:  { shape: 'box',  colors: { a: '#b98a52', b: '#8a6238', c: '#e3c48a' } },
    fish:  { shape: 'fish', colors: { a: '#9fb2c4', b: '#71859a', c: '#c3d2df' } },
};

/**
 * The pixel maps: 16 rows of 16 characters. '.' is transparent, the other
 * characters are palette keys (o outline, w white, e silver, k grey, and the
 * item's own a / b / c / d).
 */
ItemIcons.SHAPES = {
    // tall slim can with a label band
    can: [
        '................',
        '.....oooooo.....',
        '....oeeeeeeo....',
        '....oaaaaabo....',
        '....owaaaabo....',
        '....owaaaabo....',
        '....occcccco....',
        '....occddcco....',
        '....occddcco....',
        '....occcccco....',
        '....owaaaabo....',
        '....owaaaabo....',
        '....oaaaaabo....',
        '....obbbbbbo....',
        '.....oooooo.....',
        '................',
    ],
    // shorter coffee can
    'can-short': [
        '................',
        '................',
        '................',
        '.....oooooo.....',
        '....oeeeeeeo....',
        '....oaaaaabo....',
        '....owaaaabo....',
        '....occcccco....',
        '....ocddddco....',
        '....occcccco....',
        '....owaaaabo....',
        '....oaaaaabo....',
        '....obbbbbbo....',
        '.....oooooo.....',
        '................',
        '................',
    ],
    // PET bottle with a cap and a wrap label
    bottle: [
        '................',
        '......oooo......',
        '......oddo......',
        '......oooo......',
        '.....oaaaao.....',
        '....owaaaabo....',
        '....owaaaabo....',
        '....occcccco....',
        '....occddcco....',
        '....occcccco....',
        '....owaaaabo....',
        '....owaaaabo....',
        '....owaaaabo....',
        '....oaaaabbo....',
        '.....oooooo.....',
        '................',
    ],
    // codd-neck ramune bottle: pinched neck with the marble in it
    ramune: [
        '................',
        '.....oooooo.....',
        '.....occcco.....',
        '.....oooooo.....',
        '......oawo......',
        '.....oaddao.....',
        '......oawo......',
        '.....oaaaao.....',
        '....owaaaabo....',
        '....occcccco....',
        '....occcccco....',
        '....owaaaabo....',
        '....owaaaabo....',
        '....oaaaabbo....',
        '.....oooooo.....',
        '................',
    ],
    // tall tumbler with ice cubes and a lemon wedge on the rim
    glass: [
        '................',
        '..........ooo...',
        '.........odddo..',
        '....oooooodddo..',
        '....oeeeeeoddo..',
        '....oacaaaaoo...',
        '....oaaacaao....',
        '....oacaaabo....',
        '....oaaaacbo....',
        '....oaacaabo....',
        '....oaaaaabo....',
        '....oaaaabbo....',
        '....oaaaabbo....',
        '....obbbbbbo....',
        '.....oooooo.....',
        '................',
    ],
    // beer mug: foam head, handle on the right
    mug: [
        '................',
        '................',
        '...oooooooo.....',
        '..owwwwwwwwo....',
        '..owwwwwwwwo....',
        '..oawwawwaaoooo.',
        '..oawaaaaabo..o.',
        '..oawaaaaabo..o.',
        '..oawaaaaabo..o.',
        '..oawaaaaabo..o.',
        '..oawaaaaaboooo.',
        '..oaaaaaaabo....',
        '..oaaaaaabbo....',
        '..oeeeeeeeeo....',
        '...oooooooo.....',
        '................',
    ],
    // rice triangle with a strip of nori
    onigiri: [
        '................',
        '.......oo.......',
        '......owwo......',
        '......owwo......',
        '.....owwwwo.....',
        '.....owwwwo.....',
        '....owwwwwwo....',
        '....owwwwweo....',
        '...owwwwwwweo...',
        '...owaaaaaaeo...',
        '..owwaaaaaaweo..',
        '..owwaaaaaaweo..',
        '..oweaaaaaaeeo..',
        '...oooooooooo...',
        '................',
        '................',
    ],
    // round bun with a scored crust (melon pan); a = b gives a plain bun
    bun: [
        '................',
        '................',
        '......oooo......',
        '....ooabaaoo....',
        '...oaabaabaao...',
        '..oawabaabaabo..',
        '..obbbbbbbbbbo..',
        '..oaabaabaabao..',
        '..oaabaabaabao..',
        '..obbbbbbbbbbo..',
        '..oaabaabaabdo..',
        '...oddddddddo...',
        '....oooooooo....',
        '................',
        '................',
        '................',
    ],
    // steamed bun: pleated top, steam rising
    nikuman: [
        '................',
        '.....e....e.....',
        '....e....e......',
        '.....e....e.....',
        '................',
        '......oooo......',
        '....oowbbwoo....',
        '...owwbwwbwwo...',
        '..owwwwbbwwwwo..',
        '..owwwwwwwwwao..',
        '..owwwwwwwwaao..',
        '..oawwwwwwaaao..',
        '...oaaaaaaaao...',
        '....oooooooo....',
        '................',
        '................',
    ],
    // two bean pods
    pods: [
        '................',
        '................',
        '...ooo..........',
        '..oawaoooo......',
        '..oaaaawaaooo...',
        '...obaaaaawaao..',
        '....oobbaaaaao..',
        '......ooobbbo...',
        '.........oooo...',
        '.....ooooawao...',
        '..oooaawaaaao...',
        '.oaawaaaaabo....',
        '.oaaaaabboo.....',
        '..obbboo........',
        '...ooo..........',
        '................',
    ],
    // a pile of fried nuggets on a plate
    nuggets: [
        '................',
        '................',
        '......oooo......',
        '.....oacaao.....',
        '....oaaaacao....',
        '...oooaaaoooo...',
        '..oacaoooacaao..',
        '.oaaaacooaaaco..',
        '.oacaaaooacaao..',
        '.obaaaboobaabo..',
        '..obbbo..obbo...',
        'oeeeeeeeeeeeeeeo',
        '.oooooooooooooo.',
        '................',
        '................',
        '................',
    ],
    // fishing rod: reel near the grip, line and float hanging from the tip
    rod: [
        '................',
        '............oo..',
        '...........oaok.',
        '..........oaao.k',
        '.........oaao..k',
        '........oaao...k',
        '.......oaao....k',
        '......oaao.....k',
        '.....oaao.....od',
        '....obbo......od',
        '...obbeo......ow',
        '..obboeeo......o',
        '.obbo.oo........',
        'obbo............',
        'ooo.............',
        '................',
    ],
    // a fish, facing left; c is its markings
    fish: [
        '................',
        '................',
        '................',
        '........ooo.....',
        '......ooaaoo....',
        '....ooaaaaaoo.oo',
        '...oaaacaaaaooao',
        '..oaoaaccaaaaaao',
        '..oaaaaaaacaaabo',
        '...obbaaaccbooao',
        '....oobbbbboo.oo',
        '......ooooo.....',
        '................',
        '................',
        '................',
        '................',
    ],
    // the same fish with a glint — the rare one
    'fish-rare': [
        '..w.............',
        '.www............',
        '..w.............',
        '........ooo.....',
        '......ooaaoo....',
        '....ooaaaaaoo.oo',
        '...oaaacaaaaooao',
        '..oaoaaccaaaaaao',
        '..oaaaaaaacaaabo',
        '...obbaaaccbooao',
        '....oobbbbboo.oo',
        '......ooooo.....',
        '.............w..',
        '............www.',
        '.............w..',
        '................',
    ],
    // an eel: head top left (w is its eye), body winding down, pale belly
    eel: [
        '................',
        '..oooo..........',
        '.oaaaaoooooo....',
        '.oawaaaaaaaaoo..',
        '.oaaabbbbbaaaao.',
        '..oooooooobaaao.',
        '..........obaao.',
        '....oooooooaaao.',
        '..ooaaaaaaaaaoo.',
        '.oaaaabbbbbboo..',
        '.oaabooooooo....',
        '.oaaaoooooo.....',
        '..oaaaaaaaaoo...',
        '...oobbbbaaaaoo.',
        '.....oooooooo...',
        '................',
    ],
    // a bowl of ramen (issue #367): a broth, c noodles, d the topping, b the bowl with e its lit rim, k chopsticks
    bowl: [
        '...............k',
        '..............k.',
        '.............k.k',
        '............k.k.',
        '...ooooooookok..',
        '..oeaacccdkako..',
        '.oeacccaddckaeo.',
        '.oeaaacccaaaaeo.',
        '.ooeeeeeeeeeeoo.',
        '.obbbbbbbbbbbbo.',
        '..obbbbbbbbbbo..',
        '..obbbbbbbbbbo..',
        '...obbbbbbbbo...',
        '....oobbbboo....',
        '.....oeeeeo.....',
        '.....oooooo.....',
    ],
    // a crate, for gear with no icon of its own
    box: [
        '................',
        '................',
        '................',
        '..oooooooooooo..',
        '..oaaaaccaaaao..',
        '..oaaaaccaaaao..',
        '..oooooooooooo..',
        '..oaaaaccaaabo..',
        '..oaaaaccaaabo..',
        '..oaaaaaaaaabo..',
        '..oaaaaaaaaabo..',
        '..obbbbbbbbbbo..',
        '..oooooooooooo..',
        '................',
        '................',
        '................',
    ],
};

if (typeof window !== 'undefined') window.ItemIcons = ItemIcons;
