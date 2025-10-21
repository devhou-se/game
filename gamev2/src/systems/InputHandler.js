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

        // Check if any directional keys are currently held (arrows or WASD)
        const anyKeyHeld = this.cursors.left.isDown || this.cursors.right.isDown ||
                           this.cursors.up.isDown || this.cursors.down.isDown ||
                           this.aKey.isDown || this.dKey.isDown ||
                           this.wKey.isDown || this.sKey.isDown;

        // Update last key states
        this.lastKeyState.left = this.cursors.left.isDown;
        this.lastKeyState.right = this.cursors.right.isDown;
        this.lastKeyState.up = this.cursors.up.isDown;
        this.lastKeyState.down = this.cursors.down.isDown;

        // If any directional key is held, move based on ALL currently held keys
        if (anyKeyHeld) {
            let moveX = 0;
            let moveY = 0;

            if (this.cursors.left.isDown || this.aKey.isDown) moveX -= 1;
            if (this.cursors.right.isDown || this.dKey.isDown) moveX += 1;
            if (this.cursors.up.isDown || this.wKey.isDown) moveY -= 1;
            if (this.cursors.down.isDown || this.sKey.isDown) moveY += 1;

            const speedMultiplier = this.shiftKey.isDown ? 2 : 1;

            if (moveX !== 0 || moveY !== 0) {
                this.scene.player.startMovement(moveX, moveY, speedMultiplier);
            }
        }
    }
}
