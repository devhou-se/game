const config = {
    type: Phaser.AUTO,
    width: 1280,
    height: 960,
    scene: GameScene,
    scale: {
        mode: Phaser.Scale.NONE,
        autoCenter: Phaser.Scale.CENTER_BOTH,
        width: 1280,
        height: 960
    },
    render: {
        pixelArt: true,
        antialias: false,
        roundPixels: true
    },
    physics: {
        default: 'arcade',
        arcade: {
            gravity: { y: 0 },
            debug: false
        }
    }
};

const game = new Phaser.Game(config);
window.game = game; // Expose for debugging

// Pixel-perfect scaling: pick the largest scale that fits the window.
// Uses crisp integer steps when there's room, and falls back to a fractional
// scale on small windows so the whole game stays visible (no clipping).
function resizeGame() {
    const canvas = game.canvas;
    if (!canvas) return; // Phaser creates the canvas asynchronously after boot.

    const baseWidth = 1280;
    const baseHeight = 960;

    const fitScale = Math.min(
        window.innerWidth / baseWidth,
        window.innerHeight / baseHeight
    );
    const scale = fitScale >= 1 ? Math.floor(fitScale) : fitScale;

    canvas.style.width = (baseWidth * scale) + 'px';
    canvas.style.height = (baseHeight * scale) + 'px';
}

window.addEventListener('resize', resizeGame);
// Apply once the canvas exists, then keep it in sync with the window.
game.events.once('ready', resizeGame);
resizeGame();
