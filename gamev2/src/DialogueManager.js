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
                fontFamily: 'monospace',
                backgroundColor: '#000000', // Black background like world
                padding: { x: 8, y: 4 } // Add padding around text
            }
        );
        this.npcNameText.setOrigin(0.5, 1); // Bottom-center aligned like world labels
        this.npcNameText.setResolution(window.devicePixelRatio || 2);
        this.npcNameText.setScrollFactor(0);
        this.npcNameText.setDepth(3002);
        this.npcNameText.setVisible(false);

        // Dialogue text
        this.dialogueText = this.scene.add.text(
            this.panelX + 30,
            this.panelY + 30,
            '',
            {
                fontSize: '18px',
                fill: '#ffffff',
                fontFamily: 'monospace',
                wordWrap: { width: this.panelWidth - 60 }
            }
        );
        this.dialogueText.setResolution(window.devicePixelRatio || 2);
        this.dialogueText.setScrollFactor(0);
        this.dialogueText.setDepth(3002);
        this.dialogueText.setVisible(false);

        // Continue prompt
        this.continuePrompt = this.scene.add.text(
            this.scene.cameras.main.width / 2,
            this.panelY + this.panelHeight - 30,
            'SPACE/ENTER: continue | ESC: close',
            {
                fontSize: '14px',
                fill: '#888888',
                fontFamily: 'monospace'
            }
        );
        this.continuePrompt.setOrigin(0.5, 0.5);
        this.continuePrompt.setResolution(window.devicePixelRatio || 2);
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

        // Create NPC sprite (2x scale, centered above dialogue panel)
        if (this.npcSprite) {
            this.npcSprite.destroy();
        }

        const spriteKey = npc.sprite.texture.key;
        this.npcSprite = this.scene.add.sprite(
            this.scene.cameras.main.width / 2,
            this.npcSpriteY,
            spriteKey
        );
        this.npcSprite.setScale(2); // 2x size
        this.npcSprite.setScrollFactor(0);
        this.npcSprite.setDepth(3002);

        // Enable pixel-perfect rendering (no anti-aliasing)
        this.npcSprite.texture.setFilter(Phaser.Textures.FilterMode.NEAREST);

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
