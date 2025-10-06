// SpriteManager - Handles sprite operations including export, animation management
class SpriteManager {
    constructor(configManager) {
        this.configManager = configManager;
    }

    // Export all sprites as a ZIP file with sprites organized in sprites/ folder
    async exportSprites() {
        if (typeof JSZip === 'undefined') {
            alert('JSZip library not loaded. Cannot create ZIP file.');
            return;
        }

        const allSprites = this.configManager.exportSprites();

        if (allSprites.length === 0) {
            alert('No sprites to export. Please upload sprites in the Sprites tab first.');
            return;
        }

        // Filter sprites that have actual frame data
        const spritesWithFrames = allSprites.filter(sprite =>
            sprite.frames && sprite.frames.length > 0 && sprite.frames[0]
        );

        if (spritesWithFrames.length === 0) {
            alert(`Found ${allSprites.length} sprite(s) in config, but none have uploaded image data.\n\nPlease upload sprite images in the Sprites tab before exporting.`);
            return;
        }

        // Create ZIP file
        const zip = new JSZip();

        // Create assets/sprites folder structure
        const assetsFolder = zip.folder('assets');
        const spritesFolder = assetsFolder.folder('sprites');

        let totalFrames = 0;

        // Add each sprite frame to sprites/ folder
        for (const sprite of spritesWithFrames) {
            for (let i = 0; i < sprite.frames.length; i++) {
                const frameData = sprite.frames[i];
                if (!frameData) continue; // Skip empty frames

                const filename = sprite.frames.length > 1
                    ? `${sprite.key}_frame_${i}.png`
                    : `${sprite.key}.png`;

                // Convert base64 to blob
                const base64Data = frameData.split(',')[1];
                spritesFolder.file(filename, base64Data, { base64: true });
                totalFrames++;
            }
        }

        // Generate and download ZIP
        try {
            const blob = await zip.generateAsync({ type: 'blob' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'game-sprites.zip';
            link.click();
            URL.revokeObjectURL(url);

            const skipped = allSprites.length - spritesWithFrames.length;
            const message = skipped > 0
                ? `Exported ${spritesWithFrames.length} sprites (${totalFrames} frames total).\n\nSkipped ${skipped} sprite(s) with no image data.`
                : `Exported ${spritesWithFrames.length} sprites (${totalFrames} frames total).`;

            alert(message);
        } catch (e) {
            console.error('Failed to create ZIP:', e);
            alert('Failed to create ZIP file: ' + e.message);
        }
    }

    // Download image data as PNG file
    downloadImage(dataUrl, filename) {
        return new Promise((resolve) => {
            const link = document.createElement('a');
            link.href = dataUrl;
            link.download = filename;
            link.click();
            setTimeout(resolve, 50);
        });
    }

    // Download JSON data
    downloadJSON(data, filename) {
        const json = JSON.stringify(data, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.click();
        URL.revokeObjectURL(url);
    }

    // Utility sleep function
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Load sprite from file
    async loadSpriteFile(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }

    // Add animation frame to existing sprite
    async addFrameToSprite(spriteKey, file) {
        const frameData = await this.loadSpriteFile(file);
        return this.configManager.addSpriteFrame(spriteKey, frameData);
    }

    // Create sprite manager modal
    createSpriteModal(spriteKey) {
        const metadata = this.configManager.getSpriteMetadata(spriteKey);
        if (!metadata) {
            console.error('Sprite not found:', spriteKey);
            return;
        }

        // Create modal
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.style.display = 'flex';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 800px;">
                <div class="modal-header">
                    <h3>Manage Sprite: ${spriteKey}</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    ${metadata.frames.length > 1 ? `
                    <div style="text-align: center; margin-bottom: 20px;">
                        <h4>Animation Preview</h4>
                        <canvas id="animation-preview" width="128" height="128" style="border: 2px solid #3d3d3d; background: #1e1e1e; image-rendering: pixelated;"></canvas>
                    </div>
                    ` : ''}

                    <div class="sprite-settings">
                        <div class="form-group">
                            <label>Scale:</label>
                            <input type="number" id="sprite-scale" class="form-control"
                                   value="${metadata.scale}" min="0.1" max="10" step="0.1">
                        </div>
                        <div class="form-group">
                            <label>Anchor X (0=left, 0.5=center, 1=right):</label>
                            <input type="number" id="sprite-anchor-x" class="form-control"
                                   value="${metadata.anchorX}" min="0" max="1" step="0.1">
                        </div>
                        <div class="form-group">
                            <label>Anchor Y (0=top, 0.5=center, 1=bottom):</label>
                            <input type="number" id="sprite-anchor-y" class="form-control"
                                   value="${metadata.anchorY}" min="0" max="1" step="0.1">
                        </div>
                        <div class="form-group">
                            <label>Frame Rate (fps):</label>
                            <input type="number" id="sprite-framerate" class="form-control"
                                   value="${metadata.frameRate}" min="1" max="60" step="1">
                        </div>
                        <div class="form-group">
                            <label>
                                <input type="checkbox" id="sprite-loop" ${metadata.loop ? 'checked' : ''}>
                                Loop Animation
                            </label>
                        </div>

                        <h4 style="margin-top: 20px;">Sprite Sheet Settings</h4>
                        <div class="form-group">
                            <label>
                                <input type="checkbox" id="sprite-is-spritesheet" ${metadata.spriteSheet ? 'checked' : ''}>
                                Use Sprite Sheet (single PNG with multiple frames)
                            </label>
                        </div>
                        <div id="spritesheet-settings" style="display: ${metadata.spriteSheet ? 'block' : 'none'}; padding-left: 20px;">
                            <div class="form-group">
                                <label>Frame Width (pixels):</label>
                                <input type="number" id="sprite-frame-width" class="form-control"
                                       value="${metadata.frameWidth || ''}" min="1" placeholder="e.g., 64">
                            </div>
                            <div class="form-group">
                                <label>Frame Height (pixels):</label>
                                <input type="number" id="sprite-frame-height" class="form-control"
                                       value="${metadata.frameHeight || ''}" min="1" placeholder="e.g., 64">
                            </div>
                            <div class="form-group">
                                <label>Start Frame (0-based index):</label>
                                <input type="number" id="sprite-start-frame" class="form-control"
                                       value="${metadata.startFrame !== undefined ? metadata.startFrame : 0}" min="0">
                            </div>
                            <div class="form-group">
                                <label>End Frame (leave blank for all):</label>
                                <input type="number" id="sprite-end-frame" class="form-control"
                                       value="${metadata.endFrame !== null && metadata.endFrame !== undefined ? metadata.endFrame : ''}" min="0" placeholder="Optional">
                            </div>
                            <div class="form-group">
                                <label>Margin (pixels around sheet):</label>
                                <input type="number" id="sprite-margin" class="form-control"
                                       value="${metadata.margin || 0}" min="0">
                            </div>
                            <div class="form-group">
                                <label>Spacing (pixels between frames):</label>
                                <input type="number" id="sprite-spacing" class="form-control"
                                       value="${metadata.spacing || 0}" min="0">
                            </div>
                        </div>
                    </div>

                    <h4>Animation Frames (${metadata.frames.length})</h4>
                    <div id="sprite-frames" class="sprite-frames">
                        ${metadata.frames.map((frame, i) => `
                            <div class="sprite-frame" data-frame="${i}">
                                <img src="${frame}" alt="Frame ${i}">
                                <button class="btn-delete-frame" data-frame="${i}">×</button>
                            </div>
                        `).join('')}
                    </div>

                    <div class="sprite-actions">
                        <input type="file" id="add-frame-file" accept="image/png,image/jpg,image/jpeg" style="display:none">
                        <button id="add-frame-btn" class="btn btn-primary">Add Frame</button>
                        <button id="delete-sprite-btn" class="btn btn-danger">Delete Sprite</button>
                    </div>
                </div>
                <div class="modal-footer">
                    <button id="save-sprite-settings" class="btn btn-success">Save</button>
                    <button class="modal-close btn btn-secondary">Cancel</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Event listeners
        // Toggle sprite sheet settings visibility
        const spritesheetCheckbox = modal.querySelector('#sprite-is-spritesheet');
        const spritesheetSettings = modal.querySelector('#spritesheet-settings');
        spritesheetCheckbox.addEventListener('change', (e) => {
            spritesheetSettings.style.display = e.target.checked ? 'block' : 'none';
        });

        modal.querySelector('#add-frame-btn').addEventListener('click', () => {
            modal.querySelector('#add-frame-file').click();
        });

        modal.querySelector('#add-frame-file').addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (file) {
                const frameData = await this.loadSpriteFile(file);
                this.configManager.addSpriteFrame(spriteKey, frameData);
                modal.remove();
                this.createSpriteModal(spriteKey); // Recreate modal with new frame
            }
        });

        modal.querySelectorAll('.btn-delete-frame').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const frameIndex = parseInt(e.target.dataset.frame);
                if (metadata.frames.length > 1) {
                    if (confirm(`Delete frame ${frameIndex}?`)) {
                        this.configManager.removeSpriteFrame(spriteKey, frameIndex);
                        modal.remove();
                        this.createSpriteModal(spriteKey); // Recreate modal
                    }
                } else {
                    alert('Cannot delete the last frame');
                }
            });
        });

        modal.querySelector('#delete-sprite-btn').addEventListener('click', () => {
            if (confirm(`Delete sprite "${spriteKey}"?`)) {
                this.configManager.deleteSprite(spriteKey);
                modal.remove();
            }
        });

        modal.querySelector('#save-sprite-settings').addEventListener('click', () => {
            const scale = parseFloat(modal.querySelector('#sprite-scale').value);
            const anchorX = parseFloat(modal.querySelector('#sprite-anchor-x').value);
            const anchorY = parseFloat(modal.querySelector('#sprite-anchor-y').value);
            const frameRate = parseInt(modal.querySelector('#sprite-framerate').value);
            const loop = modal.querySelector('#sprite-loop').checked;

            // Sprite sheet settings
            const spriteSheet = modal.querySelector('#sprite-is-spritesheet').checked;
            const frameWidth = modal.querySelector('#sprite-frame-width').value;
            const frameHeight = modal.querySelector('#sprite-frame-height').value;
            const startFrame = parseInt(modal.querySelector('#sprite-start-frame').value) || 0;
            const endFrameValue = modal.querySelector('#sprite-end-frame').value;
            const endFrame = endFrameValue ? parseInt(endFrameValue) : null;
            const margin = parseInt(modal.querySelector('#sprite-margin').value) || 0;
            const spacing = parseInt(modal.querySelector('#sprite-spacing').value) || 0;

            this.configManager.updateSpriteMetadata(spriteKey, {
                scale,
                anchorX,
                anchorY,
                frameRate,
                loop,
                spriteSheet,
                frameWidth: frameWidth ? parseInt(frameWidth) : null,
                frameHeight: frameHeight ? parseInt(frameHeight) : null,
                startFrame,
                endFrame,
                margin,
                spacing
            });

            modal.remove();
        });

        modal.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', () => {
                if (this.animationInterval) {
                    clearInterval(this.animationInterval);
                }
                modal.remove();
            });
        });

        // Start animation preview if there are multiple frames
        if (metadata.frames.length > 1) {
            this.startAnimationPreview(modal, spriteKey, metadata);
        }
    }

    // Animate preview canvas
    startAnimationPreview(modal, spriteKey, metadata) {
        const canvas = modal.querySelector('#animation-preview');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        let currentFrame = 0;
        const frames = [];

        // Load all frame images
        metadata.frames.forEach((frameData, i) => {
            const img = new Image();
            img.src = frameData;
            frames.push(img);
        });

        // Animation loop
        const frameRate = metadata.frameRate || 10;
        const frameDuration = 1000 / frameRate;

        this.animationInterval = setInterval(() => {
            if (frames[currentFrame] && frames[currentFrame].complete) {
                // Clear canvas
                ctx.fillStyle = '#1e1e1e';
                ctx.fillRect(0, 0, canvas.width, canvas.height);

                // Draw current frame centered and scaled
                const img = frames[currentFrame];
                const scale = Math.min(canvas.width / img.width, canvas.height / img.height) * 0.8;
                const width = img.width * scale;
                const height = img.height * scale;
                const x = (canvas.width - width) / 2;
                const y = (canvas.height - height) / 2;

                ctx.imageSmoothingEnabled = false;
                ctx.drawImage(img, x, y, width, height);

                // Draw frame number
                ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
                ctx.font = '12px monospace';
                ctx.fillText(`Frame ${currentFrame + 1}/${frames.length}`, 5, 15);
            }

            // Advance to next frame
            currentFrame = (currentFrame + 1) % frames.length;
        }, frameDuration);
    }
}
