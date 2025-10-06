// FrameSelector - Component for visual frame selection and management
class FrameSelector {
    constructor(configManager) {
        this.configManager = configManager;
        this.currentSpriteKey = null;
        this.draggedFrameIndex = null;
    }

    render(spriteKey, container) {
        this.currentSpriteKey = spriteKey;
        const metadata = this.configManager.getSpriteMetadata(spriteKey);

        if (!metadata) return;

        container.innerHTML = `
            <div class="frame-selector-panel">
                <div class="frame-selector-grid" id="frame-selector-grid">
                    ${this.renderFrames(metadata.frames)}
                </div>
                <div class="frame-selector-actions">
                    <input type="file" id="frame-add-file" accept="image/png,image/jpg,image/jpeg" style="display:none" multiple>
                    <button id="frame-add-btn" class="btn btn-small btn-primary">+ Add Frames</button>
                    <button id="frame-clear-all-btn" class="btn btn-small btn-secondary">Clear All</button>
                </div>
            </div>
        `;

        this.attachMainListeners();
        this.attachGridListeners();
    }

    renderFrames(frames) {
        if (frames.length === 0) {
            return '<div class="frame-selector-empty">No frames</div>';
        }

        return frames.map((frameData, index) => `
            <div class="frame-selector-item" data-frame-index="${index}" draggable="true">
                <div class="frame-selector-preview">
                    <img src="${frameData}" alt="Frame ${index + 1}">
                </div>
                <div class="frame-selector-number">${index + 1}</div>
                <button class="frame-selector-delete" data-frame-index="${index}">×</button>
            </div>
        `).join('');
    }

    attachMainListeners() {
        // Add frames button (only attach once when render() is called)
        const addBtn = document.getElementById('frame-add-btn');
        const addFile = document.getElementById('frame-add-file');

        addBtn?.addEventListener('click', () => {
            addFile.click();
        });

        addFile?.addEventListener('change', async (e) => {
            const files = e.target.files;
            if (!files || files.length === 0) return;

            // Process all files (ConfigManager events will trigger auto-refresh)
            for (const file of files) {
                const frameData = await this.loadImageFile(file);
                this.configManager.addSpriteFrame(this.currentSpriteKey, frameData);
            }

            addFile.value = ''; // Reset file input
            // Don't call refresh() here - ConfigManager events will handle it
        });

        // Clear all button
        const clearBtn = document.getElementById('frame-clear-all-btn');
        clearBtn?.addEventListener('click', () => {
            if (confirm('Delete all frames? This will keep the first frame.')) {
                const metadata = this.configManager.getSpriteMetadata(this.currentSpriteKey);
                const frameCount = metadata.frames.length;

                // Remove all except first frame
                for (let i = frameCount - 1; i > 0; i--) {
                    this.configManager.removeSpriteFrame(this.currentSpriteKey, i);
                }
                // ConfigManager events will trigger refresh
            }
        });
    }

    attachGridListeners() {
        // Delete individual frame buttons (called both from render() and refresh())
        const deleteButtons = document.querySelectorAll('.frame-selector-delete');
        deleteButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const frameIndex = parseInt(btn.dataset.frameIndex);
                const metadata = this.configManager.getSpriteMetadata(this.currentSpriteKey);

                if (metadata.frames.length > 1) {
                    if (confirm(`Delete frame ${frameIndex + 1}?`)) {
                        this.configManager.removeSpriteFrame(this.currentSpriteKey, frameIndex);
                        // ConfigManager events will trigger refresh
                    }
                } else {
                    alert('Cannot delete the last frame');
                }
            });
        });

        // Drag and drop for reordering
        this.attachDragDropListeners();
    }

    attachDragDropListeners() {
        const frameItems = document.querySelectorAll('.frame-selector-item');

        frameItems.forEach(item => {
            item.addEventListener('dragstart', (e) => {
                this.draggedFrameIndex = parseInt(item.dataset.frameIndex);
                item.classList.add('dragging');
                e.dataTransfer.effectAllowed = 'move';
            });

            item.addEventListener('dragend', (e) => {
                item.classList.remove('dragging');
                this.draggedFrameIndex = null;
            });

            item.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';

                const targetIndex = parseInt(item.dataset.frameIndex);
                if (this.draggedFrameIndex !== null && this.draggedFrameIndex !== targetIndex) {
                    item.classList.add('drag-over');
                }
            });

            item.addEventListener('dragleave', (e) => {
                item.classList.remove('drag-over');
            });

            item.addEventListener('drop', (e) => {
                e.preventDefault();
                item.classList.remove('drag-over');

                const targetIndex = parseInt(item.dataset.frameIndex);

                if (this.draggedFrameIndex !== null && this.draggedFrameIndex !== targetIndex) {
                    this.reorderFrames(this.draggedFrameIndex, targetIndex);
                }
            });
        });
    }

    reorderFrames(fromIndex, toIndex) {
        const metadata = this.configManager.getSpriteMetadata(this.currentSpriteKey);
        if (!metadata) return;

        const frames = [...metadata.frames];
        const [movedFrame] = frames.splice(fromIndex, 1);
        frames.splice(toIndex, 0, movedFrame);

        // Update metadata with new frame order
        metadata.frames = frames;
        this.configManager.notifyListeners('sprite-frames-reordered', {
            key: this.currentSpriteKey
        });

        this.refresh();
    }

    refresh() {
        const metadata = this.configManager.getSpriteMetadata(this.currentSpriteKey);
        if (!metadata) return;

        const grid = document.getElementById('frame-selector-grid');
        if (grid) {
            grid.innerHTML = this.renderFrames(metadata.frames);
            // Only attach listeners for grid items (not main UI buttons/inputs)
            this.attachGridListeners();
        }
    }

    async loadImageFile(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }
}
