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

// Pixel-perfect integer scaling
function resizeGame() {
    const canvas = game.canvas;
    const baseWidth = 1280;
    const baseHeight = 960;

    // Calculate maximum integer scale that fits
    const scaleX = Math.floor(window.innerWidth / baseWidth);
    const scaleY = Math.floor(window.innerHeight / baseHeight);
    const scale = Math.max(1, Math.min(scaleX, scaleY));

    // Apply integer scale
    canvas.style.width = (baseWidth * scale) + 'px';
    canvas.style.height = (baseHeight * scale) + 'px';
}

window.addEventListener('resize', resizeGame);
resizeGame();
