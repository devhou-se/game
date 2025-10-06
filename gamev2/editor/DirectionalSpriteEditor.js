// DirectionalSpriteEditor - Visual editor for 4-way directional sprites
class DirectionalSpriteEditor {
    constructor(configManager) {
        this.configManager = configManager;
        this.currentSpriteKey = null;
    }

    render(spriteKey, container) {
        this.currentSpriteKey = spriteKey;
        const metadata = this.configManager.getSpriteMetadata(spriteKey);

        if (!metadata) return;

        // Get all available sprites for selection
        const allSprites = this.configManager.getAllSpriteMetadata();
        const spriteOptions = allSprites
            .map(s => `<option value="${s.key}" ${s.key === spriteKey ? 'selected' : ''}>${s.key}</option>`)
            .join('');

        container.innerHTML = `
            <div class="directional-sprite-editor">
                <h5>Direction Assignment</h5>

                <!-- 4-way directional grid -->
                <div class="directional-grid">
                    <!-- Up -->
                    <div class="directional-cell empty-center"></div>
                    <div class="directional-cell" data-direction="up">
                        <div class="directional-label">↑ UP</div>
                        <div class="directional-preview" id="dir-preview-up">
                            ${this.renderDirectionPreview(metadata, 'up', spriteKey)}
                        </div>
                        <select class="directional-select" id="dir-select-up" data-direction="up">
                            <option value="">None (use default)</option>
                            ${spriteOptions}
                        </select>
                    </div>
                    <div class="directional-cell empty-center"></div>

                    <!-- Left, Center (current), Right -->
                    <div class="directional-cell" data-direction="left">
                        <div class="directional-label">← LEFT</div>
                        <div class="directional-preview" id="dir-preview-left">
                            ${this.renderDirectionPreview(metadata, 'left', spriteKey)}
                        </div>
                        <select class="directional-select" id="dir-select-left" data-direction="left">
                            <option value="">None (use default)</option>
                            ${spriteOptions}
                        </select>
                    </div>
                    <div class="directional-cell directional-center">
                        <div class="directional-current-sprite">
                            <img src="${metadata.frames[0]}" alt="${spriteKey}">
                            <div class="directional-current-label">Current</div>
                        </div>
                    </div>
                    <div class="directional-cell" data-direction="right">
                        <div class="directional-label">→ RIGHT</div>
                        <div class="directional-preview" id="dir-preview-right">
                            ${this.renderDirectionPreview(metadata, 'right', spriteKey)}
                        </div>
                        <select class="directional-select" id="dir-select-right" data-direction="right">
                            <option value="">None (use default)</option>
                            ${spriteOptions}
                        </select>
                    </div>

                    <!-- Down -->
                    <div class="directional-cell empty-center"></div>
                    <div class="directional-cell" data-direction="down">
                        <div class="directional-label">↓ DOWN</div>
                        <div class="directional-preview" id="dir-preview-down">
                            ${this.renderDirectionPreview(metadata, 'down', spriteKey)}
                        </div>
                        <select class="directional-select" id="dir-select-down" data-direction="down">
                            <option value="">None (use default)</option>
                            ${spriteOptions}
                        </select>
                    </div>
                    <div class="directional-cell empty-center"></div>
                </div>

                <div class="directional-help">
                    <p>💡 Select a sprite for each direction, or leave as "None" to use the default sprite.</p>
                    <p>Enable auto-flip to automatically mirror sprites for opposite directions.</p>
                </div>
            </div>
        `;

        // Set current values
        this.setDirectionValues(metadata.directions);

        // Attach event listeners
        this.attachEventListeners();
    }

    renderDirectionPreview(metadata, direction, currentSpriteKey) {
        const directionSpriteKey = metadata.directions?.[direction];
        const autoFlip = metadata.autoFlip || {};

        // Check if we should show a flipped version
        let shouldFlipH = false;
        let shouldFlipV = false;
        let previewSpriteKey = directionSpriteKey || currentSpriteKey;

        if (!directionSpriteKey) {
            // No specific sprite for this direction, check auto-flip
            if (direction === 'right' && autoFlip.horizontal && metadata.directions?.left) {
                previewSpriteKey = metadata.directions.left;
                shouldFlipH = true;
            } else if (direction === 'left' && autoFlip.horizontal && metadata.directions?.right) {
                previewSpriteKey = metadata.directions.right;
                shouldFlipH = true;
            } else if (direction === 'down' && autoFlip.vertical && metadata.directions?.up) {
                previewSpriteKey = metadata.directions.up;
                shouldFlipV = true;
            } else if (direction === 'up' && autoFlip.vertical && metadata.directions?.down) {
                previewSpriteKey = metadata.directions.down;
                shouldFlipV = true;
            }
        }

        // Get the preview sprite
        const previewMetadata = this.configManager.getSpriteMetadata(previewSpriteKey);
        if (!previewMetadata || !previewMetadata.frames[0]) {
            return '<div class="directional-preview-empty">No sprite</div>';
        }

        const transform = [];
        if (shouldFlipH) transform.push('scaleX(-1)');
        if (shouldFlipV) transform.push('scaleY(-1)');
        const transformStyle = transform.length > 0 ? `style="transform: ${transform.join(' ')}"` : '';

        const autoFlipIndicator = (shouldFlipH || shouldFlipV) ?
            '<div class="auto-flip-indicator">Auto-flip</div>' : '';

        return `
            <img src="${previewMetadata.frames[0]}" alt="${direction}" ${transformStyle}>
            ${autoFlipIndicator}
        `;
    }

    setDirectionValues(directions) {
        if (!directions) return;

        ['up', 'down', 'left', 'right'].forEach(dir => {
            const select = document.getElementById(`dir-select-${dir}`);
            if (select && directions[dir]) {
                select.value = directions[dir];
            }
        });
    }

    attachEventListeners() {
        const selects = document.querySelectorAll('.directional-select');

        selects.forEach(select => {
            select.addEventListener('change', (e) => {
                const direction = e.target.dataset.direction;
                const spriteKey = e.target.value;

                // Update metadata
                const metadata = this.configManager.getSpriteMetadata(this.currentSpriteKey);
                if (metadata) {
                    metadata.directions[direction] = spriteKey || null;
                    this.configManager.notifyListeners('sprite-direction-changed', {
                        key: this.currentSpriteKey,
                        direction,
                        spriteKey
                    });

                    // Refresh preview
                    this.refreshPreview(direction);
                }
            });
        });
    }

    refreshPreview(direction) {
        const metadata = this.configManager.getSpriteMetadata(this.currentSpriteKey);
        if (!metadata) return;

        const previewContainer = document.getElementById(`dir-preview-${direction}`);
        if (previewContainer) {
            previewContainer.innerHTML = this.renderDirectionPreview(metadata, direction, this.currentSpriteKey);
        }
    }

    refreshAll() {
        const metadata = this.configManager.getSpriteMetadata(this.currentSpriteKey);
        if (!metadata) return;

        ['up', 'down', 'left', 'right'].forEach(dir => {
            this.refreshPreview(dir);
        });
    }
}
