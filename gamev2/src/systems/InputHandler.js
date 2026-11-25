/**
 * InputHandler - Centralizes all keyboard input processing
 */
class InputHandler {
    /**
     * @param {GameScene} scene - The parent game scene
     */
    constructor(scene) {
        this.scene = scene;

        // Track key states for press detection
        this.lastKeyState = {
            up: false,
            down: false,
            esc: false,
            enter: false,
            space: false
        };

        // Keys that went down since the last frame (see held())
        this.tapped = new Set();

        // Keyboard keys (initialized in setupKeys)
        this.cursors = null;
        this.shiftKey = null;
        this.escKey = null;
        this.enterKey = null;
        this.spaceKey = null;
        this.wKey = null;
        this.aKey = null;
        this.sKey = null;
        this.dKey = null;
    }

    /**
     * Set up keyboard input bindings.
     * The whole game runs on WASD/arrows + SPACE/ENTER + SHIFT, with ESC as
     * the one system key (menu / close). No other bindings.
     */
    setupKeys() {
        this.cursors = this.scene.input.keyboard.createCursorKeys();
        this.shiftKey = this.scene.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.SHIFT);
        this.escKey = this.scene.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.ESC);
        this.enterKey = this.scene.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.ENTER);
        this.spaceKey = this.scene.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.SPACE);

        // WASD keys
        this.wKey = this.scene.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.W);
        this.aKey = this.scene.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.A);
        this.sKey = this.scene.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.S);
        this.dKey = this.scene.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.D);

        // Latch each keydown until the next frame has read it (see held())
        const c = this.cursors;
        for (const key of [c.up, c.down, c.left, c.right, this.escKey, this.enterKey, this.spaceKey,
            this.wKey, this.aKey, this.sKey, this.dKey]) {
            key.on('down', () => this.tapped.add(key));
        }
    }

    /**
     * Main input update - called every frame. Whatever was tapped since the
     * last frame has been seen by now, so the latches are dropped.
     */
    handleInput() {
        this.routeInput();
        this.tapped.clear();
    }

    /**
     * Is the key down, or was it tapped since the last frame? Keys are polled
     * once a frame; a keydown and keyup that both land between two frames
     * leave isDown false, so the keydown is latched until it has been read.
     * lastKeyState remembers isDown alone: a latched tap is already up again,
     * and the next tap is a new press.
     */
    held(key) {
        return key.isDown || this.tapped.has(key);
    }

    /**
     * Hand this frame's input to whoever owns it
     */
    routeInput() {
        // Priority 0: the title screen owns all input until it is dismissed
        // (sync the keys that dismiss it, so the same press doesn't also pop
        // the menu or activate something on the very next frame)
        if (this.scene.titleScreen && this.scene.titleScreen.isVisible()) {
            this.scene.titleScreen.handleInput();
            this.lastKeyState.esc = this.escKey.isDown;
            this.lastKeyState.space = this.spaceKey.isDown || this.enterKey.isDown;
            this.lastKeyState.enter = this.enterKey.isDown;
            return;
        }

        // Priority 0: no input at all while riding the train
        if (this.scene.trainTravel && this.scene.trainTravel.riding) return;

        // Priority 0.5: the hidden debug menu owns input while open (sync ESC
        // so the press that closed it doesn't pop the main menu next frame)
        if (this.scene.debugManager && this.scene.debugManager.menuVisible) {
            this.scene.debugManager.handleMenuInput();
            this.lastKeyState.esc = this.escKey.isDown;
            return;
        }

        // Priority 1: Dialogue input
        if (this.scene.dialogueManager.isVisible()) {
            this.handleDialogueInput();
            return;
        }

        // Priority 2: Credits input
        if (this.scene.creditsVisible) {
            this.handleCreditsInput();
            return;
        }

        // Priority 2b: Achievements overlay — ESC closes it (not the menu)
        if (this.scene.achievementsVisible) {
            const escPressed = this.held(this.escKey) && !this.lastKeyState.esc;
            if (escPressed && this.scene.achievementsCloseCallback) this.scene.achievementsCloseCallback();
            this.lastKeyState.esc = this.escKey.isDown;
            return;
        }

        // Priority 2b2: Map overlay — ESC closes it (not the menu)
        if (this.scene.mapVisible) {
            const escPressed = this.held(this.escKey) && !this.lastKeyState.esc;
            if (escPressed && this.scene.mapCloseCallback) this.scene.mapCloseCallback();
            this.lastKeyState.esc = this.escKey.isDown;
            return;
        }

        // Priorities 2b3-2c: one overlay at a time owns all input while open.
        // Each branch also syncs lastKeyState.esc — the ESC that closed the
        // overlay must not read as a fresh press and pop the main menu open
        // on the very next frame.
        const overlays = [
            this.scene.intro && this.scene.intro.isVisible() && this.scene.intro,
            this.scene.stationPicker && this.scene.stationPicker.isVisible() && this.scene.stationPicker,
            this.scene.shop && this.scene.shop.isVisible() && this.scene.shop,
            this.scene.characterSelect && this.scene.characterSelect.isVisible() && this.scene.characterSelect,
            this.scene.characterCreator && this.scene.characterCreator.isVisible() && this.scene.characterCreator,
            this.scene.fishing && this.scene.fishing.isActive() && this.scene.fishing,
            this.scene.drinkingGame && this.scene.drinkingGame.isActive() && this.scene.drinkingGame,
            this.scene.datePicker && this.scene.datePicker.isVisible() && this.scene.datePicker,
        ];
        const overlay = overlays.find(Boolean);
        if (overlay) {
            overlay.handleInput();
            this.lastKeyState.esc = this.escKey.isDown;
            return;
        }

        // Priority 3: Menu toggle
        this.handleMenuToggle();

        // Priority 4: Menu navigation
        if (this.scene.menuManager.isVisible()) {
            this.handleMenuInput();
            return;
        }

        // Priority 5: Player movement
        this.handlePlayerMovement();
    }

    /**
     * Handle input when dialogue is visible
     */
    handleDialogueInput() {
        const spacePressed = this.held(this.spaceKey) && !this.lastKeyState.space;
        const enterPressed = this.held(this.enterKey) && !this.lastKeyState.enter;
        const escPressed = this.held(this.escKey) && !this.lastKeyState.esc;

        // ESC to close dialogue
        if (escPressed) {
            this.scene.dialogueManager.close();
        }
        // Space or Enter to advance dialogue
        else if (spacePressed || enterPressed) {
            this.scene.dialogueManager.advance();
        }

        this.lastKeyState.space = this.spaceKey.isDown;
        this.lastKeyState.enter = this.enterKey.isDown;
        this.lastKeyState.esc = this.escKey.isDown;
    }

    /**
     * Handle input when credits are visible
     */
    handleCreditsInput() {
        const escPressed = this.held(this.escKey) && !this.lastKeyState.esc;
        if (escPressed && this.scene.creditsCloseCallback) {
            this.scene.creditsCloseCallback();
        }
        this.lastKeyState.esc = this.escKey.isDown;
    }

    /**
     * Handle ESC key for menu toggle
     */
    handleMenuToggle() {
        if (this.held(this.escKey) && !this.lastKeyState.esc) {
            this.scene.menuManager.toggle();
        }
        this.lastKeyState.esc = this.escKey.isDown;
    }

    /**
     * Handle menu navigation input
     */
    handleMenuInput() {
        const upHeld = this.held(this.wKey) || this.held(this.cursors.up);
        const downHeld = this.held(this.sKey) || this.held(this.cursors.down);
        const confirmHeld = this.held(this.spaceKey) || this.held(this.enterKey);

        // W / up - previous option
        if (upHeld && !this.lastKeyState.up) {
            this.scene.menuManager.selectPrevious();
        }

        // S / down - next option
        if (downHeld && !this.lastKeyState.down) {
            this.scene.menuManager.selectNext();
        }

        // SPACE / ENTER - activate selected option
        if (confirmHeld && !this.lastKeyState.space) {
            this.scene.menuManager.activate();
        }

        // Update key states for menu navigation
        this.lastKeyState.up = this.wKey.isDown || this.cursors.up.isDown;
        this.lastKeyState.down = this.sKey.isDown || this.cursors.down.isDown;
        this.lastKeyState.space = this.spaceKey.isDown || this.enterKey.isDown;
    }

    /**
     * Handle player movement input
     */
    handlePlayerMovement() {
        // If currently moving or transitioning, don't accept input
        if (this.scene.player.isMoving || this.scene.roomManager.isTransitioning) {
            return;
        }

        // On-screen touch d-pad state (empty object on non-touch devices), so a
        // held d-pad direction reads exactly like a held arrow/WASD key.
        const t = (this.scene.touchControls && this.scene.touchControls.enabled)
            ? this.scene.touchControls.state : null;

        const leftHeld  = this.held(this.cursors.left)  || this.held(this.aKey) || (t && t.left);
        const rightHeld = this.held(this.cursors.right) || this.held(this.dKey) || (t && t.right);
        const upHeld    = this.held(this.cursors.up)    || this.held(this.wKey) || (t && t.up);
        const downHeld  = this.held(this.cursors.down)  || this.held(this.sKey) || (t && t.down);

        // Check if any directional input is currently held (arrows, WASD, or touch)
        const anyKeyHeld = leftHeld || rightHeld || upHeld || downHeld;

        // Update last key states
        this.lastKeyState.up = this.cursors.up.isDown || this.wKey.isDown;
        this.lastKeyState.down = this.cursors.down.isDown || this.sKey.isDown;

        // If any directional input is held, move based on ALL currently held dirs
        if (anyKeyHeld) {
            let moveX = 0;
            let moveY = 0;

            if (leftHeld)  moveX -= 1;
            if (rightHeld) moveX += 1;
            if (upHeld)    moveY -= 1;
            if (downHeld)  moveY += 1;

            let speedMultiplier = (this.shiftKey.isDown || (t && t.sprint)) ? 2 : 1;

            // Drink effects (issue #12): temporary speed boost, and the
            // vodka-redbull chance of stepping somewhere you didn't ask to
            const fx = this.scene.shop ? this.scene.shop.movementModifier() : null;
            if (fx) {
                speedMultiplier *= fx.speed;
                if (fx.scramble && Math.random() < fx.scramble) {
                    const dirs = [[1, 0], [-1, 0], [0, 1], [0, -1]];
                    [moveX, moveY] = dirs[Math.floor(Math.random() * dirs.length)];
                }
            }

            if (moveX !== 0 || moveY !== 0) {
                this.scene.player.startMovement(moveX, moveY, speedMultiplier);
            }
        }
    }
}
