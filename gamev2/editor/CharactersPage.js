// CharactersPage - Main controller for the character management interface
class CharactersPage {
    constructor(configManager, gridEditor) {
        this.configManager = configManager;
        this.gridEditor = gridEditor;
        this.selectedCharacter = null;
        this.characterEditor = null;
        this.container = document.getElementById('characters-page-container');

        // Listen for character changes
        this.configManager.addEventListener((event, data) => {
            if (event.includes('npc') || event.includes('character') || event.includes('player')) {
                this.refreshCharacterList();
                // Re-render if we're currently viewing the updated character
                if (this.selectedCharacter) {
                    if (event.includes('player') && this.selectedCharacter.isPlayer) {
                        this.loadCharacter(this.configManager.getAllCharacters()[0]);
                    }
                }
            }
        });
    }

    render() {
        this.container.innerHTML = `
            <div class="characters-page">
                <!-- Left Panel: Character List -->
                <div class="characters-sidebar">
                    <div class="characters-sidebar-header">
                        <h3>Characters</h3>
                        <div class="characters-toolbar">
                            <input type="text" id="characters-search" class="characters-search" placeholder="Search...">
                        </div>
                    </div>
                    <div id="characters-list-container" class="characters-list"></div>
                </div>

                <!-- Center Panel: Character Preview -->
                <div class="characters-editor-area">
                    <div id="character-preview-container" class="character-preview-empty">
                        <div class="empty-state">
                            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="8" r="4"/>
                                <path d="M6 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2"/>
                            </svg>
                            <p>Select a character to edit</p>
                        </div>
                    </div>
                </div>

                <!-- Right Panel: Character Editor -->
                <div class="characters-properties-panel">
                    <div class="characters-properties-content" id="character-editor-content">
                        <div class="empty-state-small">
                            <p>No character selected</p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.attachEventListeners();
        this.refreshCharacterList();
    }

    attachEventListeners() {
        // Search
        const searchInput = document.getElementById('characters-search');
        searchInput?.addEventListener('input', (e) => {
            this.filterCharacters(e.target.value);
        });
    }

    refreshCharacterList() {
        const container = document.getElementById('characters-list-container');
        if (!container) return;

        const characters = this.configManager.getAllCharacters();

        if (characters.length === 0) {
            container.innerHTML = '<div class="empty-state-small"><p>No characters yet</p><p>Add NPCs in the Editor tab</p></div>';
            return;
        }

        container.innerHTML = '';
        characters.forEach((character) => {
            const item = document.createElement('div');
            item.className = 'character-list-item';
            if (this.selectedCharacter?.id === character.id) {
                item.classList.add('selected');
            }

            // Get sprite preview
            const spriteKey = character.sprite || 'tile';
            const spriteMetadata = this.configManager.getSpriteMetadata(spriteKey);
            const spritePreview = spriteMetadata?.frames[0] || '';

            item.innerHTML = `
                <div class="character-list-preview">
                    ${spritePreview ? `<img src="${spritePreview}" alt="${character.name}">` : '<div class="no-preview">?</div>'}
                </div>
                <div class="character-list-info">
                    <div class="character-list-name">
                        ${character.isPlayer ? '👤 ' : ''}${character.name || 'Unnamed'}
                    </div>
                    <div class="character-list-meta">
                        ${character.isPlayer ? 'Player' : character.roomKey}
                        ${character.directionalSprites ? '• Directional' : ''}
                    </div>
                </div>
            `;

            item.addEventListener('click', () => {
                this.selectCharacter(character);
            });

            container.appendChild(item);
        });
    }

    filterCharacters(searchTerm) {
        const items = document.querySelectorAll('.character-list-item');
        const term = searchTerm.toLowerCase();

        items.forEach(item => {
            const name = item.querySelector('.character-list-name').textContent.toLowerCase();
            const meta = item.querySelector('.character-list-meta').textContent.toLowerCase();
            if (name.includes(term) || meta.includes(term)) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        });
    }

    selectCharacter(character) {
        this.selectedCharacter = character;
        this.refreshCharacterList(); // Update selection highlight
        this.loadCharacter(character);
    }

    loadCharacter(character) {
        const previewContainer = document.getElementById('character-preview-container');
        const editorContainer = document.getElementById('character-editor-content');

        if (!character) {
            previewContainer.className = 'character-preview-empty';
            previewContainer.innerHTML = `
                <div class="empty-state">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="8" r="4"/>
                        <path d="M6 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2"/>
                    </svg>
                    <p>Select a character to edit</p>
                </div>
            `;
            editorContainer.innerHTML = `
                <div class="empty-state-small">
                    <p>No character selected</p>
                </div>
            `;
            return;
        }

        // Update preview container
        previewContainer.className = 'character-preview-active';
        this.renderCharacterPreview(character, previewContainer);

        // Initialize character editor
        if (!this.characterEditor) {
            this.characterEditor = new CharacterEditor(this.configManager);
        }
        this.characterEditor.render(character, editorContainer);
    }

    renderCharacterPreview(character, container) {
        const spriteKey = character.sprite || 'tile';
        const spriteMetadata = this.configManager.getSpriteMetadata(spriteKey);
        const spritePreview = spriteMetadata?.frames[0] || '';
        const spriteScale = spriteMetadata?.scale || 1;

        const directionalSprites = character.directionalSprites || {};
        const hasDirectional = character.directionalSprites &&
            (directionalSprites.up || directionalSprites.down || directionalSprites.left || directionalSprites.right);

        container.innerHTML = `
            <div class="character-preview">
                <h3>${character.name || 'Unnamed Character'}</h3>

                <div class="character-preview-sprite">
                    <div class="preview-sprite-main">
                        ${spritePreview ? `<img src="${spritePreview}" alt="${character.name}" style="transform: scale(${spriteScale}); image-rendering: pixelated;">` : '<div class="no-preview">?</div>'}
                        <div class="preview-sprite-label">Default</div>
                    </div>
                </div>

                ${hasDirectional ? this.renderDirectionalPreview(character, directionalSprites) : ''}

                <div class="character-preview-info">
                    <div class="preview-info-item">
                        <strong>Room:</strong> ${character.roomKey}
                    </div>
                    <div class="preview-info-item">
                        <strong>Sprite:</strong> ${spriteKey}
                    </div>
                    ${character.dialogue && character.dialogue.length > 0 ? `
                        <div class="preview-info-item">
                            <strong>Dialogue:</strong> ${character.dialogue.length} lines
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    renderDirectionalPreview(character, directionalSprites) {
        const getPreview = (spriteKey) => {
            if (!spriteKey) return '<div class="no-preview">-</div>';
            const metadata = this.configManager.getSpriteMetadata(spriteKey);
            if (!metadata?.frames[0]) return '<div class="no-preview">?</div>';
            const scale = metadata.scale || 1;
            return `<img src="${metadata.frames[0]}" alt="${spriteKey}" style="transform: scale(${scale}); image-rendering: pixelated;">`;
        };

        return `
            <div class="character-preview-directional">
                <h4>Directional Sprites</h4>
                <div class="directional-preview-grid">
                    <div class="directional-preview-cell empty"></div>
                    <div class="directional-preview-cell">
                        <div class="preview-sprite-mini">
                            ${getPreview(directionalSprites.up)}
                        </div>
                        <div class="preview-label">↑ Up</div>
                    </div>
                    <div class="directional-preview-cell empty"></div>

                    <div class="directional-preview-cell">
                        <div class="preview-sprite-mini">
                            ${getPreview(directionalSprites.left)}
                        </div>
                        <div class="preview-label">← Left</div>
                    </div>
                    <div class="directional-preview-cell center">
                        <div class="preview-sprite-mini">
                            ${getPreview(character.sprite)}
                        </div>
                        <div class="preview-label">Center</div>
                    </div>
                    <div class="directional-preview-cell">
                        <div class="preview-sprite-mini">
                            ${getPreview(directionalSprites.right)}
                        </div>
                        <div class="preview-label">→ Right</div>
                    </div>

                    <div class="directional-preview-cell empty"></div>
                    <div class="directional-preview-cell">
                        <div class="preview-sprite-mini">
                            ${getPreview(directionalSprites.down)}
                        </div>
                        <div class="preview-label">↓ Down</div>
                    </div>
                    <div class="directional-preview-cell empty"></div>
                </div>
            </div>
        `;
    }

    clearEditor() {
        this.selectedCharacter = null;
        this.loadCharacter(null);
    }
}
