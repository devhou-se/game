class DialogueManager {
    constructor(scene) {
        this.scene = scene;
        this.visible = false;
        this.currentNPC = null;
        this.currentDialogueIndex = 0;

        this.createOverlay();
    }

    createOverlay() {
        // Semi-transparent background overlay
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
        const nameY = this.npcSpriteY - 74;

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
        this.npcNameText.setDepth(3002);
        this.npcNameText.setVisible(false);

        // Dialogue text
        this.dialogueText = this.scene.add.text(
            this.panelX + 30,
            this.panelY + 30,
            '',
            {
                fontSize: '24px',
                fill: '#ffffff',
                fontFamily: 'PixelOperatorMono',
                wordWrap: { width: this.panelWidth - 60 }
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
            'SPACE/ENTER: continue | ESC: close',
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

        // Create NPC sprite (use configured scale * 2 for dialogue view)
        if (this.npcSprite) {
            this.npcSprite.destroy();
        }
        this.destroyPhoto();

        // Blog-post photo (dated NPC state "photo") hangs in a frame beside
        // the author; shift the author left to make room for it
        const photoKey = npc.photo ? `photo-${npc.photo}` : null;
        const hasPhoto = !!(photoKey && this.scene.textures.exists(photoKey));
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

        if (hasPhoto) {
            this.showPhoto(photoKey);
        }
        this.npcNameText.setX(spriteX);

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
     * Hang the blog-post photo in a chunky wooden pixel frame beside the
     * author, right-aligned with the dialogue panel. Photos are 160×144
     * pixel-art prints (tools/photo_pixelize.py) shown at 2x.
     */
    showPhoto(photoKey) {
        const photoW = 160 * 2;
        const photoH = 144 * 2;
        const border = 20;   // 4px outline + 12px wood + 4px inner inset
        const frameW = photoW + border * 2;
        const frameH = photoH + border * 2;
        const frameX = this.panelX + this.panelWidth - frameW;
        const frameY = this.panelY - 12 - frameH;

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
        g.fillStyle(0x2a1c10, 1);   // inner inset around the print
        g.fillRect(frameX + 16, frameY + 16, photoW + 8, photoH + 8);
        g.setScrollFactor(0);
        g.setDepth(3002);
        this.photoFrame = g;

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

    updateText() {
        if (!this.currentNPC || !this.currentNPC.dialogue) {
            return;
        }

        const dialogue = this.currentNPC.dialogue[this.currentDialogueIndex];
        this.dialogueText.setText(dialogue);
    }

    advance() {
        if (!this.visible || !this.currentNPC) {
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

        // Destroy NPC sprite
        if (this.npcSprite) {
            this.npcSprite.destroy();
            this.npcSprite = null;
        }
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
