// SpriteSheetEditor - Visual sprite sheet editor with grid overlay and frame selection
class SpriteSheetEditor {
    constructor(configManager) {
        this.configManager = configManager;
        this.currentSpriteKey = null;
        this.canvas = null;
        this.ctx = null;
        this.spriteImage = null;
        this.scale = 1;
        this.frameWidth = 64;
        this.frameHeight = 64;
        this.margin = 0;
        this.spacing = 0;
        this.selectedFrames = [];
        this.showGrid = true;
    }

    loadSprite(spriteKey, container) {
        this.currentSpriteKey = spriteKey;
        const metadata = this.configManager.getSpriteMetadata(spriteKey);

        if (!metadata) return;

        // Load sprite sheet settings if they exist
        if (metadata.spriteSheet) {
            this.frameWidth = metadata.frameWidth || 64;
            this.frameHeight = metadata.frameHeight || 64;
            this.margin = metadata.margin || 0;
            this.spacing = metadata.spacing || 0;
        }

        container.innerHTML = `
            <div class="sprite-sheet-canvas-container">
                <canvas id="sprite-sheet-canvas"></canvas>

                <div class="sprite-sheet-controls">
                    <h4>Sprite Sheet Settings</h4>

                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="ss-is-sheet" ${metadata.spriteSheet ? 'checked' : ''}>
                            Use as Sprite Sheet
                        </label>
                    </div>

                    <div id="ss-grid-controls" style="display: ${metadata.spriteSheet ? 'block' : 'none'};">
                        <div class="form-group">
                            <label>Frame Width (px):</label>
                            <input type="number" id="ss-frame-width" class="form-control"
                                   value="${this.frameWidth}" min="1">
                        </div>

                        <div class="form-group">
                            <label>Frame Height (px):</label>
                            <input type="number" id="ss-frame-height" class="form-control"
                                   value="${this.frameHeight}" min="1">
                        </div>

                        <div class="form-group">
                            <label>Margin (px):</label>
                            <input type="number" id="ss-margin" class="form-control"
                                   value="${this.margin}" min="0">
                        </div>

                        <div class="form-group">
                            <label>Spacing (px):</label>
                            <input type="number" id="ss-spacing" class="form-control"
                                   value="${this.spacing}" min="0">
                        </div>

                        <div class="form-group">
                            <label>
                                <input type="checkbox" id="ss-show-grid" ${this.showGrid ? 'checked' : ''}>
                                Show Grid
                            </label>
                        </div>

                        <button id="ss-extract-frames" class="btn btn-small btn-success btn-block">
                            Extract Frames
                        </button>

                        <div style="margin-top: 8px; font-size: 10px; color: #888;">
                            Click on frames to select them for extraction
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.canvas = document.getElementById('sprite-sheet-canvas');
        this.ctx = this.canvas.getContext('2d');

        this.loadSpriteImage(metadata.frames[0]);
        this.attachEventListeners();
    }

    async loadSpriteImage(imageData) {
        this.spriteImage = new Image();
        this.spriteImage.src = imageData;

        await new Promise((resolve) => {
            this.spriteImage.onload = resolve;
            this.spriteImage.onerror = resolve;
        });

        this.setupCanvas();
        this.render();
    }

    setupCanvas() {
        if (!this.spriteImage || !this.canvas) return;

        // Set canvas size based on image size and scale
        const maxWidth = 800;
        const maxHeight = 600;

        let displayWidth = this.spriteImage.width;
        let displayHeight = this.spriteImage.height;

        // Scale down if image is too large
        if (displayWidth > maxWidth || displayHeight > maxHeight) {
            const scaleX = maxWidth / displayWidth;
            const scaleY = maxHeight / displayHeight;
            this.scale = Math.min(scaleX, scaleY, 1);
        } else {
            // Scale up small images
            this.scale = Math.min(3, maxWidth / displayWidth);
        }

        this.canvas.width = displayWidth * this.scale;
        this.canvas.height = displayHeight * this.scale;
    }

    render() {
        if (!this.canvas || !this.ctx || !this.spriteImage) return;

        // Clear canvas
        this.ctx.fillStyle = '#1e1e1e';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw sprite image
        this.ctx.imageSmoothingEnabled = false;
        this.ctx.drawImage(
            this.spriteImage,
            0, 0,
            this.spriteImage.width, this.spriteImage.height,
            0, 0,
            this.canvas.width, this.canvas.height
        );

        // Draw grid overlay if enabled
        if (this.showGrid) {
            this.drawGrid();
        }

        // Draw selected frames
        this.drawSelectedFrames();
    }

    drawGrid() {
        if (!this.ctx || !this.spriteImage) return;

        this.ctx.strokeStyle = 'rgba(79, 195, 247, 0.5)';
        this.ctx.lineWidth = 1;

        const cols = Math.floor(
            (this.spriteImage.width - this.margin * 2 + this.spacing) /
            (this.frameWidth + this.spacing)
        );
        const rows = Math.floor(
            (this.spriteImage.height - this.margin * 2 + this.spacing) /
            (this.frameHeight + this.spacing)
        );

        // Draw vertical lines
        for (let col = 0; col <= cols; col++) {
            const x = (this.margin + col * (this.frameWidth + this.spacing)) * this.scale;
            this.ctx.beginPath();
            this.ctx.moveTo(x, 0);
            this.ctx.lineTo(x, this.canvas.height);
            this.ctx.stroke();
        }

        // Draw horizontal lines
        for (let row = 0; row <= rows; row++) {
            const y = (this.margin + row * (this.frameHeight + this.spacing)) * this.scale;
            this.ctx.beginPath();
            this.ctx.moveTo(0, y);
            this.ctx.lineTo(this.canvas.width, y);
            this.ctx.stroke();
        }
    }

    drawSelectedFrames() {
        if (!this.ctx || this.selectedFrames.length === 0) return;

        this.ctx.fillStyle = 'rgba(79, 195, 247, 0.3)';
        this.ctx.strokeStyle = 'rgba(79, 195, 247, 0.9)';
        this.ctx.lineWidth = 2;

        this.selectedFrames.forEach(({ col, row }) => {
            const x = (this.margin + col * (this.frameWidth + this.spacing)) * this.scale;
            const y = (this.margin + row * (this.frameHeight + this.spacing)) * this.scale;
            const w = this.frameWidth * this.scale;
            const h = this.frameHeight * this.scale;

            this.ctx.fillRect(x, y, w, h);
            this.ctx.strokeRect(x, y, w, h);

            // Draw frame number
            const frameIndex = this.selectedFrames.indexOf(this.selectedFrames.find(f => f.col === col && f.row === row));
            this.ctx.fillStyle = '#4fc3f7';
            this.ctx.font = `bold ${12 * this.scale}px monospace`;
            this.ctx.fillText(`${frameIndex + 1}`, x + 4, y + 16 * this.scale);
            this.ctx.fillStyle = 'rgba(79, 195, 247, 0.3)';
        });
    }

    attachEventListeners() {
        // Toggle sprite sheet mode
        const isSheetCheckbox = document.getElementById('ss-is-sheet');
        const gridControls = document.getElementById('ss-grid-controls');

        isSheetCheckbox?.addEventListener('change', (e) => {
            gridControls.style.display = e.target.checked ? 'block' : 'none';
            this.showGrid = e.target.checked;
            this.render();
        });

        // Grid parameter inputs
        const frameWidthInput = document.getElementById('ss-frame-width');
        const frameHeightInput = document.getElementById('ss-frame-height');
        const marginInput = document.getElementById('ss-margin');
        const spacingInput = document.getElementById('ss-spacing');
        const showGridCheckbox = document.getElementById('ss-show-grid');

        const updateGrid = () => {
            this.frameWidth = parseInt(frameWidthInput.value) || 64;
            this.frameHeight = parseInt(frameHeightInput.value) || 64;
            this.margin = parseInt(marginInput.value) || 0;
            this.spacing = parseInt(spacingInput.value) || 0;
            this.showGrid = showGridCheckbox.checked;
            this.render();
        };

        frameWidthInput?.addEventListener('input', updateGrid);
        frameHeightInput?.addEventListener('input', updateGrid);
        marginInput?.addEventListener('input', updateGrid);
        spacingInput?.addEventListener('input', updateGrid);
        showGridCheckbox?.addEventListener('change', updateGrid);

        // Canvas click to select frames
        this.canvas?.addEventListener('click', (e) => {
            if (!isSheetCheckbox.checked) return;

            const rect = this.canvas.getBoundingClientRect();
            const x = (e.clientX - rect.left) / this.scale;
            const y = (e.clientY - rect.top) / this.scale;

            const col = Math.floor((x - this.margin) / (this.frameWidth + this.spacing));
            const row = Math.floor((y - this.margin) / (this.frameHeight + this.spacing));

            // Check if click is within a valid frame
            const frameX = this.margin + col * (this.frameWidth + this.spacing);
            const frameY = this.margin + row * (this.frameHeight + this.spacing);

            if (x >= frameX && x < frameX + this.frameWidth &&
                y >= frameY && y < frameY + this.frameHeight) {

                // Toggle frame selection
                const existingIndex = this.selectedFrames.findIndex(f => f.col === col && f.row === row);
                if (existingIndex >= 0) {
                    this.selectedFrames.splice(existingIndex, 1);
                } else {
                    this.selectedFrames.push({ col, row });
                }

                this.render();
            }
        });

        // Extract frames button
        const extractBtn = document.getElementById('ss-extract-frames');
        extractBtn?.addEventListener('click', () => {
            this.extractFrames();
        });
    }

    async extractFrames() {
        if (this.selectedFrames.length === 0) {
            alert('Please select frames by clicking on the sprite sheet');
            return;
        }

        // Extract each selected frame
        const frames = [];
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = this.frameWidth;
        tempCanvas.height = this.frameHeight;
        const tempCtx = tempCanvas.getContext('2d');

        for (const { col, row } of this.selectedFrames) {
            const sx = this.margin + col * (this.frameWidth + this.spacing);
            const sy = this.margin + row * (this.frameHeight + this.spacing);

            // Clear temp canvas
            tempCtx.clearRect(0, 0, this.frameWidth, this.frameHeight);

            // Draw frame
            tempCtx.drawImage(
                this.spriteImage,
                sx, sy, this.frameWidth, this.frameHeight,
                0, 0, this.frameWidth, this.frameHeight
            );

            // Get frame as data URL
            frames.push(tempCanvas.toDataURL('image/png'));
        }

        // Update sprite metadata
        const metadata = this.configManager.getSpriteMetadata(this.currentSpriteKey);
        metadata.frames = frames;
        metadata.spriteSheet = true;
        metadata.frameWidth = this.frameWidth;
        metadata.frameHeight = this.frameHeight;
        metadata.margin = this.margin;
        metadata.spacing = this.spacing;

        this.configManager.notifyListeners('sprite-frames-extracted', {
            key: this.currentSpriteKey
        });

        alert(`Extracted ${frames.length} frames successfully!`);
        this.selectedFrames = [];
        this.render();
    }
}
