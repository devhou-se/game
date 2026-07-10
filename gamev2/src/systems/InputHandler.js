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
            left: false,
            right: false,
            up: false,
            down: false,
            esc: false,
            enter: false,
            space: false
        };

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
     * Set up keyboard input bindings
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
    }

    /**
     * Main input update - called every frame
     */
    handleInput() {
        // Priority 0: no input at all while riding the train
        if (this.scene.trainTravel && this.scene.trainTravel.riding) return;

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
            const escPressed = this.escKey.isDown && !this.lastKeyState.esc;
            if (escPressed && this.scene.achievementsCloseCallback) this.scene.achievementsCloseCallback();
            this.lastKeyState.esc = this.escKey.isDown;
            return;
        }

        // Priority 2b2: Map overlay — ESC closes it (not the menu)
        if (this.scene.mapVisible) {
            const escPressed = this.escKey.isDown && !this.lastKeyState.esc;
            if (escPressed && this.scene.mapCloseCallback) this.scene.mapCloseCallback();
            this.lastKeyState.esc = this.escKey.isDown;
            return;
        }

        // Priorities 2b3-2c: one overlay at a time owns all input while open.
        // Each branch also syncs lastKeyState.esc — the ESC that closed the
        // overlay must not read as a fresh press and pop the main menu open
        // on the very next frame.
        const overlays = [
            this.scene.stationPicker && this.scene.stationPicker.isVisible() && this.scene.stationPicker,
            this.scene.shop && this.scene.shop.isVisible() && this.scene.shop,
            this.scene.characterSelect && this.scene.characterSelect.isVisible() && this.scene.characterSelect,
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

        // Priority 4.5: T opens the time-travel date picker
        if (this.scene.datePicker && Phaser.Input.Keyboard.JustDown(this.scene.datePicker.keys.t)) {
            this.scene.datePicker.show();
            return;
        }

        // Priority 5: Player movement
        this.handlePlayerMovement();
    }

    /**
     * Handle input when dialogue is visible
     */
    handleDialogueInput() {
        const spacePressed = this.spaceKey.isDown && !this.lastKeyState.space;
        const enterPressed = this.enterKey.isDown && !this.lastKeyState.enter;
        const escPressed = this.escKey.isDown && !this.lastKeyState.esc;

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
        const escPressed = this.escKey.isDown && !this.lastKeyState.esc;
        if (escPressed && this.scene.creditsCloseCallback) {
            this.scene.creditsCloseCallback();
        }
        this.lastKeyState.esc = this.escKey.isDown;
    }

    /**
     * Handle ESC key for menu toggle
     */
    handleMenuToggle() {
        if (this.escKey.isDown && !this.lastKeyState.esc) {
            this.scene.menuManager.toggle();
        }
        this.lastKeyState.esc = this.escKey.isDown;
    }

    /**
     * Handle menu navigation input
     */
    handleMenuInput() {
        // Arrow up - previous option
        if (this.cursors.up.isDown && !this.lastKeyState.up) {
            this.scene.menuManager.selectPrevious();
        }

        // Arrow down - next option
        if (this.cursors.down.isDown && !this.lastKeyState.down) {
            this.scene.menuManager.selectNext();
        }

        // Enter - activate selected option
        if (this.enterKey.isDown && !this.lastKeyState.enter) {
            this.scene.menuManager.activate();
        }

        // Update key states for menu navigation
        this.lastKeyState.up = this.cursors.up.isDown;
        this.lastKeyState.down = this.cursors.down.isDown;
        this.lastKeyState.enter = this.enterKey.isDown;
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

        const leftHeld  = this.cursors.left.isDown  || this.aKey.isDown || (t && t.left);
        const rightHeld = this.cursors.right.isDown || this.dKey.isDown || (t && t.right);
        const upHeld    = this.cursors.up.isDown    || this.wKey.isDown || (t && t.up);
        const downHeld  = this.cursors.down.isDown  || this.sKey.isDown || (t && t.down);

        // Check if any directional input is currently held (arrows, WASD, or touch)
        const anyKeyHeld = leftHeld || rightHeld || upHeld || downHeld;

        // Update last key states
        this.lastKeyState.left = this.cursors.left.isDown;
        this.lastKeyState.right = this.cursors.right.isDown;
        this.lastKeyState.up = this.cursors.up.isDown;
        this.lastKeyState.down = this.cursors.down.isDown;

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
