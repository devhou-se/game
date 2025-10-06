// CharacterEditor - Detailed character editing interface
class CharacterEditor {
    constructor(configManager) {
        this.configManager = configManager;
        this.currentCharacter = null;
        this.directionalSpriteEditor = null;
    }

    render(character, container) {
        if (!character) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>Select a character to edit</p>
                </div>
            `;
            return;
        }

        this.currentCharacter = character;
        const isPlayer = character.isPlayer === true;
        const { roomKey, roomIndex } = character;

        // Get all available sprites for selection
        const allSprites = this.configManager.getAllSpriteMetadata();
        const spriteOptions = allSprites
            .map(s => `<option value="${s.key}" ${s.key === character.sprite ? 'selected' : ''}>${s.key}</option>`)
            .join('');

        container.innerHTML = `
            <div class="character-editor">
                <div class="character-editor-header">
                    <h3>${character.name || 'Unnamed Character'}</h3>
                    <div class="character-location">
                        ${isPlayer ? `Player Character - Start Room: ${roomKey}` : `Room: ${roomKey} (${roomIndex})`}
                    </div>
                </div>

                <!-- Basic Information -->
                <div class="properties-section">
                    <h4>Basic Information</h4>
                    <div class="form-group">
                        <label>Name:</label>
                        <input type="text" id="char-name" class="form-control"
                               value="${character.name || ''}" placeholder="Character name">
                    </div>
                    <div class="form-group">
                        <label>Default Sprite:</label>
                        <select id="char-sprite" class="form-control">
                            ${spriteOptions}
                        </select>
                    </div>
                </div>

                <!-- Position -->
                ${isPlayer ? `
                <div class="properties-section">
                    <h4>Starting Position</h4>
                    <div class="form-group">
                        <label>Start X:</label>
                        <input type="number" id="char-start-x" class="form-control"
                               value="${character.startX !== null && character.startX !== undefined ? character.startX : ''}"
                               placeholder="Starting grid X">
                    </div>
                    <div class="form-group">
                        <label>Start Y:</label>
                        <input type="number" id="char-start-y" class="form-control"
                               value="${character.startY !== null && character.startY !== undefined ? character.startY : ''}"
                               placeholder="Starting grid Y">
                    </div>
                </div>
                ` : `
                <div class="properties-section">
                    <h4>Position</h4>
                    <div class="form-group">
                        <label>Grid X:</label>
                        <input type="number" id="char-grid-x" class="form-control"
                               value="${character.gridX !== null ? character.gridX : ''}"
                               placeholder="Absolute position">
                    </div>
                    <div class="form-group">
                        <label>Grid Y:</label>
                        <input type="number" id="char-grid-y" class="form-control"
                               value="${character.gridY !== null ? character.gridY : ''}"
                               placeholder="Absolute position">
                    </div>
                    <div class="form-group">
                        <label>Grid Offset X:</label>
                        <input type="number" id="char-offset-x" class="form-control"
                               value="${character.gridOffsetX !== null && character.gridOffsetX !== undefined ? character.gridOffsetX : ''}"
                               placeholder="Relative to center">
                    </div>
                    <div class="form-group">
                        <label>Grid Offset Y:</label>
                        <input type="number" id="char-offset-y" class="form-control"
                               value="${character.gridOffsetY !== null && character.gridOffsetY !== undefined ? character.gridOffsetY : ''}"
                               placeholder="Relative to center">
                    </div>
                </div>
                `}

                <!-- Directional Sprites -->
                <div class="properties-section">
                    <h4>Directional Sprites</h4>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="char-directional-enabled"
                                   ${character.directionalSprites ? 'checked' : ''}>
                            Enable Directional Sprites
                        </label>
                    </div>

                    <div id="char-directional-settings" style="display: ${character.directionalSprites ? 'block' : 'none'};">
                        <div id="char-directional-editor"></div>
                    </div>
                </div>

                <!-- Dialogue (NPCs only) -->
                ${!isPlayer ? `
                <div class="properties-section">
                    <h4>Dialogue</h4>
                    <div id="char-dialogue-lines"></div>
                    <button id="char-add-dialogue" class="btn btn-small btn-primary">Add Dialogue Line</button>
                </div>
                ` : ''}

                <!-- Actions -->
                <div class="properties-section">
                    <button id="char-save" class="btn btn-success btn-block">Save Changes</button>
                    ${!isPlayer ? '<button id="char-delete" class="btn btn-danger btn-block">Delete Character</button>' : ''}
                </div>
            </div>
        `;

        // Render dialogue lines
        this.renderDialogueLines(character.dialogue || []);

        // Initialize directional sprite editor if enabled
        if (character.directionalSprites) {
            this.initDirectionalEditor(character);
        }

        // Attach event listeners
        this.attachEventListeners(character);
    }

    renderDialogueLines(dialogue) {
        const container = document.getElementById('char-dialogue-lines');
        if (!container) return;

        container.innerHTML = '';
        dialogue.forEach((line, index) => {
            const lineDiv = document.createElement('div');
            lineDiv.className = 'dialogue-line-item';
            lineDiv.innerHTML = `
                <input type="text" class="form-control dialogue-line-input"
                       value="${line}" data-index="${index}" placeholder="Dialogue line ${index + 1}">
                <button class="btn btn-small btn-danger dialogue-line-delete" data-index="${index}">×</button>
            `;
            container.appendChild(lineDiv);
        });

        // Attach delete listeners
        container.querySelectorAll('.dialogue-line-delete').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = parseInt(e.target.dataset.index);
                const updatedDialogue = [...(this.currentCharacter.dialogue || [])];
                updatedDialogue.splice(index, 1);
                this.currentCharacter.dialogue = updatedDialogue;
                this.renderDialogueLines(updatedDialogue);
            });
        });
    }

    initDirectionalEditor(character) {
        const container = document.getElementById('char-directional-editor');
        if (!container) return;

        // Get all available sprites
        const allSprites = this.configManager.getAllSpriteMetadata();
        const spriteOptions = allSprites
            .map(s => `<option value="${s.key}">${s.key}</option>`)
            .join('');

        const directional = character.directionalSprites || { up: '', down: '', left: '', right: '' };
        const autoFlip = character.autoFlip || { horizontal: false, vertical: false };

        container.innerHTML = `
            <div class="directional-sprite-selector">
                <div class="form-group">
                    <label>↑ Up:</label>
                    <select id="char-dir-up" class="form-control">
                        <option value="">Use default</option>
                        ${spriteOptions}
                    </select>
                </div>
                <div class="form-group">
                    <label>↓ Down:</label>
                    <select id="char-dir-down" class="form-control">
                        <option value="">Use default</option>
                        ${spriteOptions}
                    </select>
                </div>
                <div class="form-group">
                    <label>← Left:</label>
                    <select id="char-dir-left" class="form-control">
                        <option value="">Use default</option>
                        ${spriteOptions}
                    </select>
                </div>
                <div class="form-group">
                    <label>→ Right:</label>
                    <select id="char-dir-right" class="form-control">
                        <option value="">Use default</option>
                        ${spriteOptions}
                    </select>
                </div>

                <h4 style="margin-top: 20px;">Auto-Flip Settings</h4>
                <p style="font-size: 12px; color: #888; margin-bottom: 10px;">
                    If you only have sprites for one horizontal/vertical direction, enable auto-flip to mirror them.
                </p>
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="char-autoflip-horizontal" ${autoFlip.horizontal ? 'checked' : ''}>
                        Flip horizontally (use Left sprite for Right, or Right sprite for Left)
                    </label>
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="char-autoflip-vertical" ${autoFlip.vertical ? 'checked' : ''}>
                        Flip vertically (use Up sprite for Down, or Down sprite for Up)
                    </label>
                </div>
            </div>
        `;

        // Set current values
        if (directional.up) document.getElementById('char-dir-up').value = directional.up;
        if (directional.down) document.getElementById('char-dir-down').value = directional.down;
        if (directional.left) document.getElementById('char-dir-left').value = directional.left;
        if (directional.right) document.getElementById('char-dir-right').value = directional.right;
    }

    attachEventListeners(character) {
        const isPlayer = character.isPlayer === true;
        const { roomKey, roomIndex } = character;

        // Toggle directional settings
        const directionalCheckbox = document.getElementById('char-directional-enabled');
        const directionalSettings = document.getElementById('char-directional-settings');

        directionalCheckbox?.addEventListener('change', (e) => {
            directionalSettings.style.display = e.target.checked ? 'block' : 'none';
            if (e.target.checked) {
                this.initDirectionalEditor(character);
            }
        });

        // Add dialogue line
        document.getElementById('char-add-dialogue')?.addEventListener('click', () => {
            const dialogue = [...(this.currentCharacter.dialogue || [])];
            dialogue.push('');
            this.currentCharacter.dialogue = dialogue;
            this.renderDialogueLines(dialogue);
        });

        // Save changes
        document.getElementById('char-save')?.addEventListener('click', () => {
            if (isPlayer) {
                // Update player
                const updatedPlayer = {
                    name: document.getElementById('char-name').value,
                    sprite: document.getElementById('char-sprite').value,
                    startX: document.getElementById('char-start-x')?.value ? parseInt(document.getElementById('char-start-x').value) : null,
                    startY: document.getElementById('char-start-y')?.value ? parseInt(document.getElementById('char-start-y').value) : null
                };

                // Collect directional sprites if enabled
                if (document.getElementById('char-directional-enabled').checked) {
                    updatedPlayer.directionalSprites = {
                        up: document.getElementById('char-dir-up')?.value || '',
                        down: document.getElementById('char-dir-down')?.value || '',
                        left: document.getElementById('char-dir-left')?.value || '',
                        right: document.getElementById('char-dir-right')?.value || ''
                    };
                    updatedPlayer.autoFlip = {
                        horizontal: document.getElementById('char-autoflip-horizontal')?.checked || false,
                        vertical: document.getElementById('char-autoflip-vertical')?.checked || false
                    };
                } else {
                    updatedPlayer.directionalSprites = null;
                    updatedPlayer.autoFlip = null;
                }

                this.configManager.updatePlayer(updatedPlayer);
                alert('Player updated successfully!');
            } else {
                // Update NPC
                const updatedCharacter = {
                    name: document.getElementById('char-name').value,
                    sprite: document.getElementById('char-sprite').value,
                    gridX: document.getElementById('char-grid-x').value ? parseInt(document.getElementById('char-grid-x').value) : null,
                    gridY: document.getElementById('char-grid-y').value ? parseInt(document.getElementById('char-grid-y').value) : null,
                    gridOffsetX: document.getElementById('char-offset-x').value ? parseInt(document.getElementById('char-offset-x').value) : null,
                    gridOffsetY: document.getElementById('char-offset-y').value ? parseInt(document.getElementById('char-offset-y').value) : null,
                    dialogue: []
                };

                // Collect dialogue lines
                const dialogueInputs = document.querySelectorAll('.dialogue-line-input');
                dialogueInputs.forEach(input => {
                    if (input.value.trim()) {
                        updatedCharacter.dialogue.push(input.value);
                    }
                });

                // Collect directional sprites if enabled
                if (document.getElementById('char-directional-enabled').checked) {
                    updatedCharacter.directionalSprites = {
                        up: document.getElementById('char-dir-up')?.value || '',
                        down: document.getElementById('char-dir-down')?.value || '',
                        left: document.getElementById('char-dir-left')?.value || '',
                        right: document.getElementById('char-dir-right')?.value || ''
                    };
                    updatedCharacter.autoFlip = {
                        horizontal: document.getElementById('char-autoflip-horizontal')?.checked || false,
                        vertical: document.getElementById('char-autoflip-vertical')?.checked || false
                    };
                }

                // Update character in config
                this.configManager.updateNPC(roomKey, roomIndex, updatedCharacter);
                alert('Character updated successfully!');
            }
        });

        // Delete character
        document.getElementById('char-delete')?.addEventListener('click', () => {
            if (confirm(`Delete character "${character.name}"?`)) {
                this.configManager.deleteNPC(roomKey, roomIndex);
                // Clear editor
                this.render(null, document.querySelector('.character-editor')?.parentElement);
            }
        });
    }

    clear() {
        this.currentCharacter = null;
    }
}
