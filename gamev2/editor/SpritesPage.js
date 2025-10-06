// SpritesPage - Main controller for the sprite management interface
class SpritesPage {
    constructor(configManager, gridEditor) {
        this.configManager = configManager;
        this.gridEditor = gridEditor;
        this.selectedSpriteKey = null;
        this.spriteSheetEditor = null;
        this.animationPreview = null;
        this.frameSelector = null;
        this.directionalSpriteEditor = null;
        this.container = document.getElementById('sprites-page-container');

        // Listen for sprite changes
        this.configManager.addEventListener((event, data) => {
            if (event.includes('sprite')) {
                this.refreshSpriteList();
                if (this.selectedSpriteKey === data?.key) {
                    this.loadSprite(this.selectedSpriteKey);
                }
            }
        });
    }

    render() {
        this.container.innerHTML = `
            <div class="sprites-page">
                <!-- Left Panel: Sprite List -->
                <div class="sprites-sidebar">
                    <div class="sprites-sidebar-header">
                        <h3>Sprites</h3>
                        <div class="sprites-toolbar">
                            <input type="file" id="sprites-upload-file" accept="image/png,image/jpg,image/jpeg" style="display:none" multiple>
                            <button id="sprites-upload-btn" class="btn btn-small btn-primary" title="Upload Sprite">+</button>
                            <input type="text" id="sprites-search" class="sprites-search" placeholder="Search...">
                        </div>
                    </div>
                    <div id="sprites-list-container" class="sprites-list"></div>
                </div>

                <!-- Center Panel: Sprite Sheet Editor -->
                <div class="sprites-editor-area">
                    <div id="sprite-editor-container" class="sprite-editor-empty">
                        <div class="empty-state">
                            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="3" width="18" height="18" rx="2"/>
                                <circle cx="8.5" cy="8.5" r="1.5"/>
                                <path d="M21 15l-5-5L5 21"/>
                            </svg>
                            <p>Select a sprite or upload a new one to get started</p>
                        </div>
                    </div>
                </div>

                <!-- Right Panel: Properties & Animation Preview -->
                <div class="sprites-properties-panel">
                    <div class="sprites-properties-content" id="sprite-properties-content">
                        <div class="empty-state-small">
                            <p>No sprite selected</p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.attachEventListeners();
        this.refreshSpriteList();
    }

    attachEventListeners() {
        // Upload button
        const uploadBtn = document.getElementById('sprites-upload-btn');
        const uploadFile = document.getElementById('sprites-upload-file');

        uploadBtn?.addEventListener('click', () => {
            uploadFile.click();
        });

        uploadFile?.addEventListener('change', async (e) => {
            const files = e.target.files;
            if (!files || files.length === 0) return;

            for (const file of files) {
                const imageData = await this.loadImageFile(file);
                const key = prompt('Enter sprite key:', file.name.replace(/\.[^/.]+$/, ''));
                if (key) {
                    this.configManager.addSprite(key, imageData);
                }
            }
            uploadFile.value = ''; // Reset file input
        });

        // Search
        const searchInput = document.getElementById('sprites-search');
        searchInput?.addEventListener('input', (e) => {
            this.filterSprites(e.target.value);
        });
    }

    refreshSpriteList() {
        const container = document.getElementById('sprites-list-container');
        if (!container) return;

        const sprites = this.configManager.getAllSpriteMetadata();

        if (sprites.length === 0) {
            container.innerHTML = '<div class="empty-state-small"><p>No sprites yet</p></div>';
            return;
        }

        container.innerHTML = '';
        sprites.forEach(({ key, frames, scale, frameRate }) => {
            const item = document.createElement('div');
            item.className = 'sprite-list-item';
            if (key === this.selectedSpriteKey) {
                item.classList.add('selected');
            }

            item.innerHTML = `
                <div class="sprite-list-preview">
                    <img src="${frames[0]}" alt="${key}">
                </div>
                <div class="sprite-list-info">
                    <div class="sprite-list-name">${key}</div>
                    <div class="sprite-list-meta">
                        ${frames.length > 1 ? `${frames.length} frames @ ${frameRate}fps` : 'Static'}
                    </div>
                </div>
                <button class="sprite-list-delete" data-key="${key}" title="Delete sprite">×</button>
            `;

            item.addEventListener('click', (e) => {
                if (!e.target.classList.contains('sprite-list-delete')) {
                    this.selectSprite(key);
                }
            });

            const deleteBtn = item.querySelector('.sprite-list-delete');
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (confirm(`Delete sprite "${key}"?`)) {
                    this.configManager.deleteSprite(key);
                    if (this.selectedSpriteKey === key) {
                        this.selectedSpriteKey = null;
                        this.clearEditor();
                    }
                }
            });

            container.appendChild(item);
        });
    }

    filterSprites(searchTerm) {
        const items = document.querySelectorAll('.sprite-list-item');
        const term = searchTerm.toLowerCase();

        items.forEach(item => {
            const name = item.querySelector('.sprite-list-name').textContent.toLowerCase();
            if (name.includes(term)) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        });
    }

    selectSprite(key) {
        this.selectedSpriteKey = key;
        this.refreshSpriteList(); // Update selection highlight
        this.loadSprite(key);
    }

    loadSprite(key) {
        const metadata = this.configManager.getSpriteMetadata(key);
        if (!metadata) return;

        const editorContainer = document.getElementById('sprite-editor-container');
        editorContainer.className = 'sprite-editor-active';

        // Initialize sprite sheet editor
        if (!this.spriteSheetEditor) {
            this.spriteSheetEditor = new SpriteSheetEditor(this.configManager);
        }
        this.spriteSheetEditor.loadSprite(key, editorContainer);

        // Load properties panel
        this.loadPropertiesPanel(key, metadata);
    }

    loadPropertiesPanel(key, metadata) {
        const propertiesContent = document.getElementById('sprite-properties-content');
        if (!propertiesContent) return;

        propertiesContent.innerHTML = `
            <div class="sprite-properties">
                <h3>${key}</h3>

                <!-- Animation Preview -->
                <div id="animation-preview-container"></div>

                <!-- Basic Properties -->
                <div class="properties-section">
                    <h4>Properties</h4>
                    <div class="form-group">
                        <label>Scale:</label>
                        <input type="number" id="prop-scale" class="form-control"
                               value="${metadata.scale}" min="0.1" max="10" step="0.1">
                    </div>
                    <div class="form-group">
                        <label>Anchor X:</label>
                        <input type="number" id="prop-anchor-x" class="form-control"
                               value="${metadata.anchorX}" min="0" max="1" step="0.1">
                    </div>
                    <div class="form-group">
                        <label>Anchor Y:</label>
                        <input type="number" id="prop-anchor-y" class="form-control"
                               value="${metadata.anchorY}" min="0" max="1" step="0.1">
                    </div>
                </div>

                <!-- Animation Settings -->
                <div class="properties-section">
                    <h4>Animation</h4>
                    <div class="form-group">
                        <label>Frame Rate (fps):</label>
                        <input type="number" id="prop-framerate" class="form-control"
                               value="${metadata.frameRate}" min="1" max="60" step="1">
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="prop-loop" ${metadata.loop ? 'checked' : ''}>
                            Loop Animation
                        </label>
                    </div>
                </div>

                <!-- Directional Settings -->
                <div class="properties-section">
                    <h4>Directional Sprite</h4>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="prop-is-directional" ${metadata.isDirectional ? 'checked' : ''}>
                            Enable Directional Sprites
                        </label>
                    </div>

                    <div id="directional-settings" style="display: ${metadata.isDirectional ? 'block' : 'none'};">
                        <div class="form-group">
                            <label>Default Direction:</label>
                            <select id="prop-default-direction" class="form-control">
                                <option value="up" ${metadata.defaultDirection === 'up' ? 'selected' : ''}>Up</option>
                                <option value="down" ${metadata.defaultDirection === 'down' ? 'selected' : ''}>Down</option>
                                <option value="left" ${metadata.defaultDirection === 'left' ? 'selected' : ''}>Left</option>
                                <option value="right" ${metadata.defaultDirection === 'right' ? 'selected' : ''}>Right</option>
                            </select>
                        </div>

                        <div class="form-group">
                            <label>Auto-Flip Options:</label>
                            <div>
                                <label>
                                    <input type="checkbox" id="prop-autoflip-horizontal" ${metadata.autoFlip?.horizontal ? 'checked' : ''}>
                                    Horizontal (Left ↔ Right)
                                </label>
                            </div>
                            <div>
                                <label>
                                    <input type="checkbox" id="prop-autoflip-vertical" ${metadata.autoFlip?.vertical ? 'checked' : ''}>
                                    Vertical (Up ↔ Down)
                                </label>
                            </div>
                        </div>

                        <div id="directional-sprite-editor-container"></div>
                    </div>
                </div>

                <!-- Frame Selector -->
                <div class="properties-section">
                    <h4>Frames (${metadata.frames.length})</h4>
                    <div id="frame-selector-container"></div>
                </div>

                <!-- Actions -->
                <div class="properties-section">
                    <button id="save-sprite-properties" class="btn btn-success btn-block">Apply Changes</button>
                    <button id="duplicate-sprite" class="btn btn-secondary btn-block">Duplicate Sprite</button>
                </div>
            </div>
        `;

        // Initialize animation preview
        if (!this.animationPreview) {
            this.animationPreview = new AnimationPreview(this.configManager);
        }
        const previewContainer = document.getElementById('animation-preview-container');
        this.animationPreview.render(key, previewContainer);

        // Initialize frame selector
        if (!this.frameSelector) {
            this.frameSelector = new FrameSelector(this.configManager);
        }
        const frameSelectorContainer = document.getElementById('frame-selector-container');
        this.frameSelector.render(key, frameSelectorContainer);

        // Initialize directional sprite editor if enabled
        if (metadata.isDirectional) {
            if (!this.directionalSpriteEditor) {
                this.directionalSpriteEditor = new DirectionalSpriteEditor(this.configManager);
            }
            const directionalContainer = document.getElementById('directional-sprite-editor-container');
            this.directionalSpriteEditor.render(key, directionalContainer);
        }

        // Attach property event listeners
        this.attachPropertyListeners(key);
    }

    attachPropertyListeners(key) {
        // Toggle directional settings visibility
        const isDirectionalCheckbox = document.getElementById('prop-is-directional');
        const directionalSettings = document.getElementById('directional-settings');

        isDirectionalCheckbox?.addEventListener('change', (e) => {
            directionalSettings.style.display = e.target.checked ? 'block' : 'none';

            // Initialize DirectionalSpriteEditor when enabled
            if (e.target.checked) {
                if (!this.directionalSpriteEditor) {
                    this.directionalSpriteEditor = new DirectionalSpriteEditor(this.configManager);
                }
                const directionalContainer = document.getElementById('directional-sprite-editor-container');
                this.directionalSpriteEditor.render(key, directionalContainer);
            }
        });

        const saveBtn = document.getElementById('save-sprite-properties');
        saveBtn?.addEventListener('click', () => {
            const scale = parseFloat(document.getElementById('prop-scale').value);
            const anchorX = parseFloat(document.getElementById('prop-anchor-x').value);
            const anchorY = parseFloat(document.getElementById('prop-anchor-y').value);
            const frameRate = parseInt(document.getElementById('prop-framerate').value);
            const loop = document.getElementById('prop-loop').checked;

            // Directional settings
            const isDirectional = document.getElementById('prop-is-directional').checked;
            const defaultDirection = document.getElementById('prop-default-direction')?.value || 'down';
            const autoFlipHorizontal = document.getElementById('prop-autoflip-horizontal')?.checked || false;
            const autoFlipVertical = document.getElementById('prop-autoflip-vertical')?.checked || false;

            // Get current directions from DirectionalSpriteEditor if available
            const metadata = this.configManager.getSpriteMetadata(key);
            const directions = metadata.directions || { up: null, down: null, left: null, right: null };

            this.configManager.updateSpriteMetadata(key, {
                scale,
                anchorX,
                anchorY,
                frameRate,
                loop,
                isDirectional,
                directions,
                autoFlip: {
                    horizontal: autoFlipHorizontal,
                    vertical: autoFlipVertical
                },
                defaultDirection
            });

            // Refresh animation preview
            if (this.animationPreview) {
                this.animationPreview.refresh(key);
            }

            // Refresh main editor
            this.gridEditor.renderEngine.refreshSpriteFrames();
            this.gridEditor.render();
        });

        const duplicateBtn = document.getElementById('duplicate-sprite');
        duplicateBtn?.addEventListener('click', () => {
            const newKey = prompt('Enter new sprite key:', `${key}_copy`);
            if (newKey && newKey !== key) {
                const metadata = this.configManager.getSpriteMetadata(key);
                this.configManager.addSprite(newKey, metadata.frames[0]);

                // Copy all frames
                for (let i = 1; i < metadata.frames.length; i++) {
                    this.configManager.addSpriteFrame(newKey, metadata.frames[i]);
                }

                // Copy metadata
                this.configManager.updateSpriteMetadata(newKey, {
                    scale: metadata.scale,
                    anchorX: metadata.anchorX,
                    anchorY: metadata.anchorY,
                    frameRate: metadata.frameRate,
                    loop: metadata.loop
                });

                this.selectSprite(newKey);
            }
        });
    }

    clearEditor() {
        const editorContainer = document.getElementById('sprite-editor-container');
        if (editorContainer) {
            editorContainer.className = 'sprite-editor-empty';
            editorContainer.innerHTML = `
                <div class="empty-state">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="3" width="18" height="18" rx="2"/>
                        <circle cx="8.5" cy="8.5" r="1.5"/>
                        <path d="M21 15l-5-5L5 21"/>
                    </svg>
                    <p>Select a sprite or upload a new one to get started</p>
                </div>
            `;
        }

        const propertiesContent = document.getElementById('sprite-properties-content');
        if (propertiesContent) {
            propertiesContent.innerHTML = `
                <div class="empty-state-small">
                    <p>No sprite selected</p>
                </div>
            `;
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
