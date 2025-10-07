/**
 * FloatingText - Visual feedback system for in-game events
 * Creates animated text that floats up and fades away
 */
class FloatingText {
    constructor(scene) {
        this.scene = scene;
        this.activeTexts = [];
    }

    /**
     * Show floating text at grid position
     * @param {string} text - Text to display
     * @param {number} gridX - Grid X position
     * @param {number} gridY - Grid Y position
     * @param {string} color - Text color (hex or CSS color)
     * @param {number} duration - Animation duration in ms (default 1500)
     */
    show(text, gridX, gridY, color = '#ffffff', duration = 1500) {
        const gridSize = this.scene.GRID_SIZE;
        const pixelX = gridX * gridSize + gridSize / 2;
        const pixelY = gridY * gridSize + gridSize / 2;

        // Create text object
        const textObject = this.scene.add.text(pixelX, pixelY, text, {
            fontSize: '16px',
            fontFamily: 'PixelOperatorMono, monospace',
            color: color,
            stroke: '#000000',
            strokeThickness: 3,
            align: 'center'
        });

        textObject.setOrigin(0.5, 0.5);
        textObject.setDepth(1000); // Above everything
        textObject.setScrollFactor(1); // Moves with camera

        // Animation: float up and fade out
        this.scene.tweens.add({
            targets: textObject,
            y: pixelY - 50, // Float up 50 pixels
            alpha: 0, // Fade out
            duration: duration,
            ease: 'Cubic.easeOut',
            onComplete: () => {
                textObject.destroy();
                this.removeText(textObject);
            }
        });

        this.activeTexts.push(textObject);
    }

    /**
     * Show floating text at pixel position (for when you don't have grid coords)
     */
    showAtPixel(text, pixelX, pixelY, color = '#ffffff', duration = 1500) {
        const textObject = this.scene.add.text(pixelX, pixelY, text, {
            fontSize: '16px',
            fontFamily: 'PixelOperatorMono, monospace',
            color: color,
            stroke: '#000000',
            strokeThickness: 3,
            align: 'center'
        });

        textObject.setOrigin(0.5, 0.5);
        textObject.setDepth(1000);
        textObject.setScrollFactor(1);

        this.scene.tweens.add({
            targets: textObject,
            y: pixelY - 50,
            alpha: 0,
            duration: duration,
            ease: 'Cubic.easeOut',
            onComplete: () => {
                textObject.destroy();
                this.removeText(textObject);
            }
        });

        this.activeTexts.push(textObject);
    }

    /**
     * Remove text from active list
     */
    removeText(textObject) {
        const index = this.activeTexts.indexOf(textObject);
        if (index > -1) {
            this.activeTexts.splice(index, 1);
        }
    }

    /**
     * Clear all floating texts
     */
    clearAll() {
        this.activeTexts.forEach(text => {
            if (text && !text.destroyed) {
                text.destroy();
            }
        });
        this.activeTexts = [];
    }

    /**
     * Destroy the floating text system
     */
    destroy() {
        this.clearAll();
    }
}
