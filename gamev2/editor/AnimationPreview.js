// AnimationPreview - Component for previewing sprite animations with playback controls
class AnimationPreview {
    constructor(configManager) {
        this.configManager = configManager;
        this.currentSpriteKey = null;
        this.animationInterval = null;
        this.currentFrame = 0;
        this.isPlaying = false;
        this.frames = [];
        this.canvas = null;
        this.ctx = null;
    }

    render(spriteKey, container) {
        this.currentSpriteKey = spriteKey;
        const metadata = this.configManager.getSpriteMetadata(spriteKey);

        if (!metadata) return;

        container.innerHTML = `
            <div class="animation-preview-panel">
                <h4>Animation Preview</h4>
                <div class="animation-preview-canvas-container">
                    <canvas id="animation-preview-canvas" width="200" height="200"></canvas>
                </div>
                <div class="animation-preview-controls">
                    <button id="anim-play-pause" class="btn btn-small btn-primary">
                        ${this.isPlaying ? '⏸ Pause' : '▶ Play'}
                    </button>
                    <button id="anim-prev-frame" class="btn btn-small btn-secondary">⏮</button>
                    <button id="anim-next-frame" class="btn btn-small btn-secondary">⏭</button>
                    <button id="anim-reset" class="btn btn-small btn-secondary">⏹</button>
                </div>
                <div class="animation-preview-info">
                    <span id="anim-frame-info">Frame ${this.currentFrame + 1} / ${metadata.frames.length}</span>
                    <span id="anim-fps-info">${metadata.frameRate} fps</span>
                </div>
            </div>
        `;

        this.canvas = document.getElementById('animation-preview-canvas');
        this.ctx = this.canvas.getContext('2d');

        this.loadFrames(metadata);
        this.attachEventListeners();

        // Auto-play if multiple frames
        if (metadata.frames.length > 1) {
            this.play();
        } else {
            this.renderFrame();
        }
    }

    async loadFrames(metadata) {
        this.frames = [];

        for (const frameData of metadata.frames) {
            const img = new Image();
            img.src = frameData;
            await new Promise((resolve) => {
                img.onload = resolve;
                img.onerror = resolve;
            });
            this.frames.push(img);
        }

        this.renderFrame();
    }

    renderFrame() {
        if (!this.canvas || !this.ctx || this.frames.length === 0) return;

        const metadata = this.configManager.getSpriteMetadata(this.currentSpriteKey);
        if (!metadata) return;

        // Clear canvas
        this.ctx.fillStyle = '#1e1e1e';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw current frame centered and scaled
        const img = this.frames[this.currentFrame];
        if (img && img.complete) {
            const scale = Math.min(
                this.canvas.width / img.width,
                this.canvas.height / img.height
            ) * 0.8;

            const width = img.width * scale;
            const height = img.height * scale;
            const x = (this.canvas.width - width) / 2;
            const y = (this.canvas.height - height) / 2;

            this.ctx.imageSmoothingEnabled = false;
            this.ctx.drawImage(img, x, y, width, height);

            // Draw frame indicator
            this.ctx.fillStyle = 'rgba(79, 195, 247, 0.8)';
            this.ctx.font = '12px monospace';
            this.ctx.fillText(`Frame ${this.currentFrame + 1}/${this.frames.length}`, 8, 20);
        }

        // Update frame info
        this.updateFrameInfo();
    }

    updateFrameInfo() {
        const metadata = this.configManager.getSpriteMetadata(this.currentSpriteKey);
        if (!metadata) return;

        const frameInfo = document.getElementById('anim-frame-info');
        const fpsInfo = document.getElementById('anim-fps-info');

        if (frameInfo) {
            frameInfo.textContent = `Frame ${this.currentFrame + 1} / ${metadata.frames.length}`;
        }

        if (fpsInfo) {
            fpsInfo.textContent = `${metadata.frameRate} fps`;
        }
    }

    play() {
        const metadata = this.configManager.getSpriteMetadata(this.currentSpriteKey);
        if (!metadata || this.frames.length <= 1) return;

        this.isPlaying = true;
        this.updatePlayPauseButton();

        const frameDuration = 1000 / metadata.frameRate;

        this.animationInterval = setInterval(() => {
            this.currentFrame = (this.currentFrame + 1) % this.frames.length;
            this.renderFrame();

            // Stop if not looping and reached end
            if (!metadata.loop && this.currentFrame === 0) {
                this.pause();
            }
        }, frameDuration);
    }

    pause() {
        this.isPlaying = false;
        if (this.animationInterval) {
            clearInterval(this.animationInterval);
            this.animationInterval = null;
        }
        this.updatePlayPauseButton();
    }

    reset() {
        this.pause();
        this.currentFrame = 0;
        this.renderFrame();
    }

    nextFrame() {
        this.pause();
        this.currentFrame = (this.currentFrame + 1) % this.frames.length;
        this.renderFrame();
    }

    prevFrame() {
        this.pause();
        this.currentFrame = (this.currentFrame - 1 + this.frames.length) % this.frames.length;
        this.renderFrame();
    }

    updatePlayPauseButton() {
        const btn = document.getElementById('anim-play-pause');
        if (btn) {
            btn.textContent = this.isPlaying ? '⏸ Pause' : '▶ Play';
        }
    }

    attachEventListeners() {
        const playPauseBtn = document.getElementById('anim-play-pause');
        const prevBtn = document.getElementById('anim-prev-frame');
        const nextBtn = document.getElementById('anim-next-frame');
        const resetBtn = document.getElementById('anim-reset');

        playPauseBtn?.addEventListener('click', () => {
            if (this.isPlaying) {
                this.pause();
            } else {
                this.play();
            }
        });

        prevBtn?.addEventListener('click', () => {
            this.prevFrame();
        });

        nextBtn?.addEventListener('click', () => {
            this.nextFrame();
        });

        resetBtn?.addEventListener('click', () => {
            this.reset();
        });
    }

    refresh(spriteKey) {
        // Stop current animation
        this.pause();

        // Reload the sprite
        if (spriteKey === this.currentSpriteKey) {
            const container = document.querySelector('.animation-preview-panel')?.parentElement;
            if (container) {
                this.render(spriteKey, container);
            }
        }
    }

    destroy() {
        this.pause();
        this.frames = [];
        this.canvas = null;
        this.ctx = null;
    }
}
