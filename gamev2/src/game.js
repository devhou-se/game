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
// When there's room (>=1x) we snap to a whole-integer step so the pixel art
// maps 1 source pixel -> N screen pixels exactly (crisp). When the window is
// SMALLER than the game (mobile / small laptops) no integer scale fits, so we
// use the exact fractional scale to keep the whole world visible -- but then we
// also switch the canvas to SMOOTH scaling, because nearest-neighbour at a
// fractional factor produces uneven pixel widths + jagged text (the "zoom
// artifacts"). Internal sprites stay crisp (pixelArt:true); only the final
// framebuffer->screen downscale is softened, giving a clean uniform result.
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
    const isInteger = Math.abs(scale - Math.round(scale)) < 0.001;

    canvas.style.width = (baseWidth * scale) + 'px';
    canvas.style.height = (baseHeight * scale) + 'px';
    // crisp nearest for whole-integer scales; smooth+uniform for fractional
    canvas.style.imageRendering = isInteger ? 'pixelated' : 'auto';
}

window.addEventListener('resize', resizeGame);
// Apply once the canvas exists, then keep it in sync with the window.
game.events.once('ready', resizeGame);
resizeGame();
