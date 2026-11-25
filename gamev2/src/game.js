const config = {
    type: Phaser.AUTO,
    width: 1280,
    height: 960,
    scene: GameScene,
    scale: {
        mode: Phaser.Scale.NONE,
        autoCenter: Phaser.Scale.NO_CENTER, // Viewport.apply positions the canvas
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

// Canvas size and position in the window (pixel-perfect integer scale when
// there is room, exact fit when there is not, clear of the touch controls):
// see src/systems/Viewport.js.
function resizeGame() {
    Viewport.apply(game);
}

window.addEventListener('resize', resizeGame);
// Apply once the canvas exists, then keep it in sync with the window.
game.events.once('ready', resizeGame);
resizeGame();
