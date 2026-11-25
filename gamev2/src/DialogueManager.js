class DialogueManager {
    /**
     * Head-and-shoulders band of a 64px `<name>_front_frame_0` character
     * sprite: the head is rows 8-37 (CharacterCreator.CUTS.front.top[0] = 38
     * is the first torso row), so this keeps 4px of air above the hair and
     * 6 rows of shoulders, centred on the 42px-wide body.
     */
    static BUST = { x: 7, y: 4, w: 48, h: 40 };

    /** The portrait window inside the frame: the bust at 5x. */
    static PORTRAIT_WINDOW = { w: 240, h: 200 };

    /** `bailey_front` -> `bailey`: the name portraits are filed under. */
    static portraitName(spriteKey) {
        const m = /^(.+)_front$/.exec(spriteKey || '');
        return m ? m[1] : null;
    }

    /** The dialogue text's font — shared by the Text object and wrapLines' measuring. */
    static TEXT_FONT = { size: 24, family: 'PixelOperatorMono' };

    /**
     * Characters with no spaces between words (Japanese/Chinese: kana, han,
     * CJK punctuation, full-width punctuation, half-width kana). A line may
     * break on either side of one, subject to the kinsoku rules below.
     * Full-width letters and digits (ＡＢＣ, １２３) are left out: they spell
     * words and numbers, which stay whole like their ASCII forms.
     */
    static CJK = /[\u2E80-\u2FDF\u3000-\u30FF\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\uFF00-\uFF0F\uFF1A-\uFF20\uFF3B-\uFF40\uFF5B-\uFFEF]|[\u{20000}-\u{3FFFF}]/u;
    /** A number stays with the counter after it: 20分間 never wraps as 20 / 分間. */
    static DIGIT = /[0-9\uFF10-\uFF19]/;
    /** Never start a line: closing punctuation, small kana, the long-vowel mark. */
    static NO_LINE_START = new Set(Array.from(
        '、。，．・：；？！ー…‥々ゝゞヽヾ゛゜）］｝」』〉》】〕〙〗’”' +
        'ぁぃぅぇぉっゃゅょゎゕゖァィゥェォッャュョヮヵヶ' +
        '!?,.:;)]}%'));
    /** Never end a line: opening brackets and quotes. */
    static NO_LINE_END = new Set(Array.from('（［｛「『〈《【〔〘〖‘“([{'));

    /**
     * Split text into the pieces a line break may fall between. Latin words
     * (anything between spaces that is not CJK) stay whole; every CJK
     * character is its own piece unless kinsoku glues it to a neighbour
     * ("。" to the character before it, "「" to the one after, a counter to
     * the number before it). `space` says
     * the piece was preceded by whitespace in the source.
     */
    static breakUnits(text) {
        const units = [];
        let cur = '', prev = null, space = false, pendingSpace = false;
        const flush = () => {
            if (cur) units.push({ text: cur, space: pendingSpace });
            cur = '';
        };
        for (const ch of text) {
            if (/\s/.test(ch)) {
                flush();
                space = true;
                prev = null;
                continue;
            }
            const breakable = prev !== null &&
                (DialogueManager.CJK.test(prev) || DialogueManager.CJK.test(ch)) &&
                !DialogueManager.NO_LINE_START.has(ch) &&
                !DialogueManager.NO_LINE_END.has(prev) &&
                !DialogueManager.DIGIT.test(prev);
            if (breakable) flush();
            if (!cur) {
                pendingSpace = space;
                space = false;
            }
            cur += ch;
            prev = ch;
        }
        flush();
        return units;
    }

    /**
     * Wrap text to lines no wider than maxWidth, as measured by
     * `measure(string) -> px`. Breaks at spaces and at CJK break
     * opportunities (see breakUnits), so Japanese wraps even though it has
     * no spaces and Latin words are never cut — except a single piece wider
     * than a whole line, which is split by character as a last resort.
     * Explicit newlines are kept. Phaser's own word wrap only knows spaces.
     */
    static wrapLines(text, maxWidth, measure) {
        const lines = [];
        for (const paragraph of String(text).split('\n')) {
            let line = '';
            for (const unit of DialogueManager.breakUnits(paragraph)) {
                const joined = line + (line && unit.space ? ' ' : '') + unit.text;
                if (measure(joined) <= maxWidth) {
                    line = joined;
                    continue;
                }
                if (line) lines.push(line);
                line = '';
                for (const ch of unit.text) {   // a no-op loop when the piece fits a line
                    if (line && measure(line + ch) > maxWidth) {
                        lines.push(line);
                        line = '';
                    }
                    line += ch;
                }
            }
            lines.push(line);
        }
        return lines;
    }

    /**
     * Deal wrapped lines into pages of at most maxLines, evenly (7 lines at
     * 6 a page become 4 + 3, not 6 + 1).
     */
    static paginate(lines, maxLines) {
        const pageCount = Math.max(1, Math.ceil(lines.length / maxLines));
        const perPage = Math.ceil(lines.length / pageCount);
        const pages = [];
        for (let i = 0; i < lines.length; i += perPage) pages.push(lines.slice(i, i + perPage));
        return pages.length ? pages : [[]];
    }

    constructor(scene) {
        this.scene = scene;
        this.visible = false;
        this.currentNPC = null;
        this.currentDialogueIndex = 0;
        this.pages = [[]];      // the current line, wrapped and paged (see layout)
        this.currentPage = 0;

        this.createOverlay();
    }

    createOverlay() {
        // Semi-transparent background overlay: the same 0.85 black as the menu
        // and the other overlays, and it measures the same on screen (15% of
        // the world's brightness gets through — issue #52). The world reads
        // as lighter here only because this panel is small and leaves most
        // of the dimmed scene in view, which is wanted: you can still see
        // who you are talking to and where.
        this.overlay = this.scene.add.graphics();
        this.overlay.fillStyle(0x000000, 0.85);
        this.overlay.fillRect(0, 0, this.scene.cameras.main.width, this.scene.cameras.main.height);
        this.overlay.setScrollFactor(0);
        this.overlay.setDepth(3000);
        this.overlay.setVisible(false);

        // Dialogue panel - centered vertically with room for NPC sprite above
        const panelWidth = 600;
        const panelHeight = 250;
        const panelX = (this.scene.cameras.main.width - panelWidth) / 2;

        // Center the entire dialogue area (NPC sprite + name + panel)
        const totalHeight = 128 + 40 + panelHeight; // sprite (64*2) + spacing + panel
        const startY = (this.scene.cameras.main.height - totalHeight) / 2;
        const panelY = startY + 168; // After sprite and spacing

        // Store panel position for later use
        this.panelX = panelX;
        this.panelY = panelY;
        this.panelWidth = panelWidth;
        this.panelHeight = panelHeight;

        // NPC sprite (will be created dynamically)
        this.npcSprite = null;

        this.panel = this.scene.add.graphics();
        this.panel.fillStyle(0x1a1a1a, 1);
        this.panel.fillRect(panelX, panelY, panelWidth, panelHeight);
        this.panel.lineStyle(3, 0x666666, 1);
        this.panel.strokeRect(panelX, panelY, panelWidth, panelHeight);
        this.panel.setScrollFactor(0);
        this.panel.setDepth(3001);
        this.panel.setVisible(false);

        // Calculate positions for NPC elements
        this.npcSpriteY = this.panelY - 100; // NPC sprite position
        // World: label is 5px above sprite top. At 2x scale: (GRID_SIZE/2 + 5) * 2 = 74px
        // (only used by the full-sprite fallback; a framed portrait carries
        // its own name plate — see showPortrait)
        const nameY = this.npcSpriteY - 74;
        this.npcNameY = nameY;

        // NPC name label (styled same as world labels, scaled 2x)
        this.npcNameText = this.scene.add.text(
            this.scene.cameras.main.width / 2,
            nameY,
            '',
            {
                fontSize: '24px', // 2x of world's 12px
                fill: '#ffffff', // White like world labels
                fontFamily: 'PixelOperatorMonoBold',
                backgroundColor: '#000000', // Black background like world
                padding: { x: 8, y: 4 } // Add padding around text
            }
        );
        this.npcNameText.setOrigin(0.5, 1); // Bottom-center aligned like world labels
        this.npcNameText.setResolution(1);
        this.npcNameText.setScrollFactor(0);
        this.npcNameText.setDepth(3004); // above the portrait frame it straddles
        this.npcNameText.setVisible(false);

        // Dialogue text. Wrapped by layout() rather than Phaser's wordWrap,
        // which only breaks on spaces (Japanese lines have none).
        this.textWidth = this.panelWidth - 60;
        this.dialogueText = this.scene.add.text(
            this.panelX + 30,
            this.panelY + 30,
            '',
            {
                fontSize: `${DialogueManager.TEXT_FONT.size}px`,
                fill: '#ffffff',
                fontFamily: DialogueManager.TEXT_FONT.family
            }
        );
        this.dialogueText.setResolution(1);
        this.dialogueText.setScrollFactor(0);
        this.dialogueText.setDepth(3002);
        this.dialogueText.setVisible(false);

        // Continue prompt
        this.continuePrompt = this.scene.add.text(
            this.scene.cameras.main.width / 2,
            this.panelY + this.panelHeight - 30,
            DialogueManager.hintText(this.scene.touchControls && this.scene.touchControls.enabled, ''),
            {
                fontSize: '16px',
                fill: '#888888',
                fontFamily: 'PixelOperatorMonoBold'
            }
        );
        this.continuePrompt.setOrigin(0.5, 0.5);
        this.continuePrompt.setResolution(1);
        this.continuePrompt.setScrollFactor(0);
        this.continuePrompt.setDepth(3002);
        this.continuePrompt.setVisible(false);

        // Room for the text: from its top down to a gap above the hint line
        this.textHeight = this.continuePrompt.y - this.continuePrompt.height / 2 - 10 - this.dialogueText.y;

        // Make overlay clickable to advance dialogue
        this.overlay.setInteractive(
            new Phaser.Geom.Rectangle(0, 0, this.scene.cameras.main.width, this.scene.cameras.main.height),
            Phaser.Geom.Rectangle.Contains
        );
        this.overlay.on('pointerdown', () => this.advance());
    }

    show(npc) {
        if (!npc.canInteract || !npc.dialogue || npc.dialogue.length === 0) {
            return;
        }

        this.visible = true;
        this.currentNPC = npc;
        this.currentDialogueIndex = 0;

        if (this.npcSprite) {
            this.npcSprite.destroy();
            this.npcSprite = null;
        }
        this.destroyPortrait();
        this.destroyPhoto();

        // Blog-post photo (dated NPC state "photo") hangs in a frame on the
        // right, above the panel
        const photoKey = npc.photo ? `photo-${npc.photo}` : null;
        const hasPhoto = !!(photoKey && this.scene.textures.exists(photoKey));

        // The speaker: a framed bust standing on the panel's top-left corner
        // (visual-novel style). Sprites without a front-facing frame set keep
        // the old look — the whole sprite at 2x, centred above the panel.
        if (!this.showPortrait(npc)) {
            this.showFullSprite(npc, hasPhoto);
        }
        if (hasPhoto) {
            this.showPhoto(photoKey);
        }

        // Show overlay elements
        this.overlay.setVisible(true);
        this.panel.setVisible(true);
        this.npcNameText.setVisible(true);
        this.dialogueText.setVisible(true);
        this.continuePrompt.setVisible(true);

        // Set NPC name
        this.npcNameText.setText(npc.name);

        // Display first dialogue line
        this.updateText();
    }

    /**
     * What to draw as the speaker's portrait, or null when the NPC has
     * nothing bust-shaped (the caller then falls back to the full sprite).
     *
     *  - hand-drawn art: texture `portrait-<name>`, loaded at boot for every
     *    name listed in assets/portraits/manifest.json (see the README there)
     *  - otherwise the head-and-shoulders band of `<name>_front_frame_0`
     *    (DialogueManager.BUST), for any directional 64px character sprite
     */
    portraitSource(npc) {
        const textures = this.scene.textures;
        const baseSpriteKey = npc.baseSpriteKey || npc.sprite.texture.key;
        const name = DialogueManager.portraitName(baseSpriteKey);

        if (name && textures.exists(`portrait-${name}`)) {
            return { key: `portrait-${name}`, crop: null };
        }

        const spriteConfig = this.scene.getSpriteConfig(baseSpriteKey);
        if (!name || !spriteConfig.isDirectional) return null;
        const frontKey = this.scene.getDirectionalSpriteKey(baseSpriteKey, 'down');
        const key = `${frontKey}_frame_0`;
        if (!frontKey || !frontKey.endsWith('_front') || !textures.exists(key)) return null;
        const src = textures.get(key).getSourceImage();
        const b = DialogueManager.BUST;
        if (!src || src.width < b.x + b.w || src.height < b.y + b.h) return null;
        return { key, crop: b };
    }

    /**
     * Frame the speaker dating-sim style: a large crisp bust in a bevelled
     * frame that stands proud of the panel's top-left corner, with the name
     * plate bridging frame and panel. Returns false (nothing drawn) when the
     * NPC has no portrait source.
     */
    showPortrait(npc) {
        const source = this.portraitSource(npc);
        if (!source) return false;

        const { w: winW, h: winH } = DialogueManager.PORTRAIT_WINDOW;
        const border = 20;
        const frameW = winW + border * 2;
        const frameH = winH + border * 2;
        // hangs 60px off the panel's left edge; its right edge stops 20px
        // short of the blog-photo frame (which is right-aligned to the panel)
        const frameX = this.panelX - 60;
        const frameY = this.panelY - 12 - frameH; // same baseline as the blog-photo frame
        const winX = frameX + border;
        const winY = frameY + border;

        this.portraitFrame = this.drawFrame(frameX, frameY, winW, winH, 0x3a4a6e);

        const img = this.scene.add.image(0, 0, source.key);
        img.texture.setFilter(Phaser.Textures.FilterMode.NEAREST);
        img.setOrigin(0, 0);
        if (source.crop) {
            // the bust band, at a whole-number scale that fills the window
            const c = source.crop;
            const scale = winW / c.w;
            img.setCrop(c.x, c.y, c.w, c.h);
            img.setScale(scale);
            img.setPosition(winX - c.x * scale, winY - c.y * scale);
        } else {
            // hand-drawn portrait: fit the window, centred, standing on its
            // bottom edge (whole-number scale when it is being enlarged)
            let scale = Math.min(winW / img.width, winH / img.height);
            if (scale > 1) scale = Math.floor(scale);
            img.setScale(scale);
            img.setPosition(
                Math.round(winX + (winW - img.width * scale) / 2),
                Math.round(winY + winH - img.height * scale)
            );
        }
        img.setScrollFactor(0);
        img.setDepth(3003);
        this.portraitImage = img;

        // name plate straddles the frame's bottom edge and the panel's top
        this.npcNameText.setOrigin(0.5, 0.5);
        this.npcNameText.setPosition(frameX + frameW / 2, this.panelY - 8);
        return true;
    }

    destroyPortrait() {
        if (this.portraitFrame) {
            this.portraitFrame.destroy();
            this.portraitFrame = null;
        }
        if (this.portraitImage) {
            this.portraitImage.destroy();
            this.portraitImage = null;
        }
    }

    /**
     * Fallback for sprites with no front-facing frame set (tiles, objects,
     * single-image NPCs): the whole sprite at 2x centred above the panel,
     * shifted left when a photo hangs beside it, with the name above it.
     */
    showFullSprite(npc, hasPhoto) {
        const spriteX = this.scene.cameras.main.width / 2 - (hasPhoto ? 180 : 0);

        // Get the base sprite key and config
        const baseSpriteKey = npc.baseSpriteKey || npc.sprite.texture.key;
        const spriteConfig = this.scene.getSpriteConfig(baseSpriteKey);

        // Use the down/forward directional sprite if available
        let displaySpriteKey = baseSpriteKey;
        if (spriteConfig.isDirectional) {
            const downSpriteKey = this.scene.getDirectionalSpriteKey(baseSpriteKey, 'down');
            if (downSpriteKey) {
                displaySpriteKey = downSpriteKey;
            }
        }

        // Get the config for the display sprite
        const displaySpriteConfig = this.scene.getSpriteConfig(displaySpriteKey);

        // Determine texture key - for multi-frame sprites, use frame_0
        let textureKey = displaySpriteKey;
        if (displaySpriteConfig.frameCount > 1 && !displaySpriteConfig.spriteSheet) {
            textureKey = `${displaySpriteKey}_frame_0`;
        }

        this.npcSprite = this.scene.add.sprite(
            spriteX,
            this.npcSpriteY,
            textureKey
        );

        // Apply flip info if directional
        if (spriteConfig.isDirectional) {
            const flipInfo = this.scene.getDirectionalFlipInfo(baseSpriteKey, 'down');
            if (flipInfo) {
                this.npcSprite.setFlipX(flipInfo.flipX);
                this.npcSprite.setFlipY(flipInfo.flipY);
            }
        }

        // Use sprite's configured scale * 2 for dialogue close-up
        this.npcSprite.setScale(spriteConfig.scale * 2);
        this.npcSprite.setScrollFactor(0);
        this.npcSprite.setDepth(3002);

        // Enable pixel-perfect rendering (no anti-aliasing)
        this.npcSprite.texture.setFilter(Phaser.Textures.FilterMode.NEAREST);

        this.npcNameText.setOrigin(0.5, 1); // sits on top of the sprite, like world labels
        this.npcNameText.setPosition(spriteX, this.npcNameY);
    }

    /**
     * A chunky wooden pixel frame around a winW x winH window whose backing
     * colour is `inset`. (x, y) is the frame's outer top-left; the window
     * starts 20px in (4px outline + 12px wood + 4px inner inset).
     */
    drawFrame(x, y, winW, winH, inset) {
        const frameX = x, frameY = y;
        const frameW = winW + 40, frameH = winH + 40;
        const g = this.scene.add.graphics();
        g.fillStyle(0x1f1410, 1);   // outline
        g.fillRect(frameX, frameY, frameW, frameH);
        g.fillStyle(0x9c6b3f, 1);   // wood
        g.fillRect(frameX + 4, frameY + 4, frameW - 8, frameH - 8);
        g.fillStyle(0xc99a62, 1);   // bevel highlight (top + left)
        g.fillRect(frameX + 4, frameY + 4, frameW - 8, 4);
        g.fillRect(frameX + 4, frameY + 4, 4, frameH - 8);
        g.fillStyle(0x6e4526, 1);   // bevel shadow (bottom + right)
        g.fillRect(frameX + 4, frameY + frameH - 8, frameW - 8, 4);
        g.fillRect(frameX + frameW - 8, frameY + 4, 4, frameH - 8);
        g.fillStyle(0x2a1c10, 1);   // inner inset around the window
        g.fillRect(frameX + 16, frameY + 16, winW + 8, winH + 8);
        if (inset !== undefined) {
            g.fillStyle(inset, 1);  // backdrop behind a transparent picture
            g.fillRect(frameX + 20, frameY + 20, winW, winH);
        }
        g.setScrollFactor(0);
        g.setDepth(3002);
        return g;
    }

    /**
     * Hang the blog-post photo in a chunky wooden pixel frame on the right,
     * right-aligned with the dialogue panel. Photos are 160×144 pixel-art
     * prints (tools/photo_pixelize.py) shown at 2x.
     */
    showPhoto(photoKey) {
        const photoW = 160 * 2;
        const photoH = 144 * 2;
        const border = 20;
        const frameW = photoW + border * 2;
        const frameH = photoH + border * 2;
        const frameX = this.panelX + this.panelWidth - frameW;
        const frameY = this.panelY - 12 - frameH;

        this.photoFrame = this.drawFrame(frameX, frameY, photoW, photoH);

        this.photoImage = this.scene.add.image(frameX + border, frameY + border, photoKey);
        this.photoImage.setOrigin(0, 0);
        this.photoImage.setScale(2);
        this.photoImage.setScrollFactor(0);
        this.photoImage.setDepth(3002);
        this.photoImage.texture.setFilter(Phaser.Textures.FilterMode.NEAREST);
    }

    destroyPhoto() {
        if (this.photoFrame) {
            this.photoFrame.destroy();
            this.photoFrame = null;
        }
        if (this.photoImage) {
            this.photoImage.destroy();
            this.photoImage = null;
        }
    }

    /** Pixel width of a string in the dialogue font. */
    measure(str) {
        if (!this.measureContext) {
            this.measureContext = document.createElement('canvas').getContext('2d');
        }
        const font = DialogueManager.TEXT_FONT;
        this.measureContext.font = `${font.size}px ${font.family}`;
        return this.measureContext.measureText(str).width;
    }

    /** Height of n lines of dialogue text at the given line spacing. */
    linesHeight(n, lineSpacing) {
        if (!this.lineHeight) {
            // Phaser's own figure for this font: the height two lines add over one
            this.dialogueText.setLineSpacing(0);
            const one = this.dialogueText.setText('A').height;
            this.lineHeight = this.dialogueText.setText('A\nA').height - one;
            this.lineBase = one - this.lineHeight;
        }
        return this.lineBase + n * this.lineHeight + (n - 1) * lineSpacing;
    }

    /**
     * Fit one dialogue line into the panel: wrapped to the text width
     * (wrapLines), then paged if it is taller than the room above the hint.
     * Japanese gets extra leading — its glyphs fill the whole em box, so at
     * the Latin line height consecutive rows touch.
     */
    layout(text) {
        const lineSpacing = DialogueManager.CJK.test(text) ? 8 : 0;
        const lines = DialogueManager.wrapLines(text, this.textWidth, s => this.measure(s));
        let maxLines = 1;
        while (this.linesHeight(maxLines + 1, lineSpacing) <= this.textHeight) maxLines++;
        return { lineSpacing, pages: DialogueManager.paginate(lines, maxLines) };
    }

    /** Show the current dialogue line from its first page, and speak it. */
    updateText() {
        if (!this.currentNPC || !this.currentNPC.dialogue) {
            return;
        }

        const dialogue = this.currentNPC.dialogue[this.currentDialogueIndex];
        const { lineSpacing, pages } = this.layout(dialogue);
        this.pages = pages;
        this.currentPage = 0;
        this.dialogueText.setLineSpacing(lineSpacing);
        this.showPage();

        // Speak the line (replaces the previous line's clip; a no-op for
        // NPCs without a voice — see src/Voice.js)
        this.scene.voice.playLine(this.currentNPC.voice, this.currentDialogueIndex);
    }

    showPage() {
        this.dialogueText.setText(this.pages[this.currentPage].join('\n'));
        const more = this.pages.length > 1 ? ` (${this.currentPage + 1}/${this.pages.length})` : '';
        this.continuePrompt.setText(DialogueManager.hintText(
            this.scene.touchControls && this.scene.touchControls.enabled, more));
    }

    /** The line under the dialogue text, worded for how this player advances it. */
    static hintText(touch, more) {
        return touch ? `TAP: continue${more} | B: close` : `SPACE/ENTER: continue${more} | ESC: close`;
    }

    advance() {
        if (!this.visible || !this.currentNPC) {
            return;
        }

        // A line too long for the panel reads on over further pages first
        if (this.currentPage < this.pages.length - 1) {
            this.currentPage++;
            this.showPage();
            return;
        }

        this.currentDialogueIndex++;

        // Check if we've exhausted all dialogue
        if (this.currentDialogueIndex >= this.currentNPC.dialogue.length) {
            this.close();
        } else {
            this.updateText();
        }
    }

    close() {
        this.visible = false;
        this.currentNPC = null;
        this.currentDialogueIndex = 0;
        this.scene.voice.stop();

        // Destroy NPC sprite
        if (this.npcSprite) {
            this.npcSprite.destroy();
            this.npcSprite = null;
        }
        this.destroyPortrait();
        this.destroyPhoto();

        // Hide overlay elements
        this.overlay.setVisible(false);
        this.panel.setVisible(false);
        this.npcNameText.setVisible(false);
        this.dialogueText.setVisible(false);
        this.continuePrompt.setVisible(false);
    }

    isVisible() {
        return this.visible;
    }

    getCurrentNPC() {
        return this.currentNPC;
    }
}
