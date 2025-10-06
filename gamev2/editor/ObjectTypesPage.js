// ObjectTypesPage - Main controller for the object types management interface
class ObjectTypesPage {
    constructor(configManager, gridEditor) {
        this.configManager = configManager;
        this.gridEditor = gridEditor;
        this.selectedTypeId = null;
        this.container = document.getElementById('object-types-view');

        // Listen for object type changes and sprite changes
        this.configManager.addEventListener((event, data) => {
            if (event.includes('object-type')) {
                this.refreshObjectTypesList();
                if (this.selectedTypeId === data?.id) {
                    this.loadObjectType(this.selectedTypeId);
                }
            }
            // Refresh when sprites are added (in case default sprites load after page renders)
            if (event.includes('sprite')) {
                this.refreshObjectTypesList();
                if (this.selectedTypeId) {
                    this.loadObjectType(this.selectedTypeId);
                }
            }
        });
    }

    render() {
        this.container.innerHTML = `
            <div class="object-types-page">
                <!-- Left Panel: Object Types List -->
                <div class="object-types-sidebar">
                    <div class="object-types-sidebar-header">
                        <h3>Object Types</h3>
                        <div class="object-types-toolbar">
                            <button id="object-types-add-btn" class="btn btn-small btn-primary" title="Add Object Type">+</button>
                            <input type="text" id="object-types-search" class="object-types-search" placeholder="Search...">
                        </div>
                    </div>
                    <div id="object-types-list-container" class="object-types-list"></div>
                </div>

                <!-- Center Panel: Object Type Editor -->
                <div class="object-types-editor-area">
                    <div id="object-type-editor-container" class="object-type-editor-empty">
                        <div class="empty-state">
                            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="3" width="7" height="7"/>
                                <rect x="14" y="3" width="7" height="7"/>
                                <rect x="14" y="14" width="7" height="7"/>
                                <rect x="3" y="14" width="7" height="7"/>
                            </svg>
                            <p>Select an object type or create a new one to get started</p>
                        </div>
                    </div>
                </div>

                <!-- Right Panel: Preview -->
                <div class="object-types-properties-panel">
                    <div class="object-types-properties-content" id="object-type-properties-content">
                        <div class="empty-state-small">
                            <p>No object type selected</p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.attachEventListeners();
        this.refreshObjectTypesList();
    }

    attachEventListeners() {
        // Add button
        const addBtn = document.getElementById('object-types-add-btn');
        addBtn?.addEventListener('click', () => {
            this.createNewObjectType();
        });

        // Search
        const searchInput = document.getElementById('object-types-search');
        searchInput?.addEventListener('input', (e) => {
            this.filterObjectTypes(e.target.value);
        });
    }

    refreshObjectTypesList() {
        const container = document.getElementById('object-types-list-container');
        if (!container) return;

        const objectTypes = this.configManager.getAllObjectTypes();

        if (objectTypes.length === 0) {
            container.innerHTML = '<div class="empty-state-small"><p>No object types yet</p></div>';
            return;
        }

        container.innerHTML = '';
        objectTypes.forEach(objType => {
            const item = document.createElement('div');
            item.className = 'object-type-list-item';
            if (objType.id === this.selectedTypeId) {
                item.classList.add('selected');
            }

            // Get sprite thumbnail
            let spriteData = this.configManager.getSprite(objType.sprite);

            // If sprite not in manager yet, try to get it from metadata
            if (!spriteData) {
                const metadata = this.configManager.getSpriteMetadata(objType.sprite);
                if (metadata && metadata.frames && metadata.frames.length > 0) {
                    spriteData = metadata.frames[0];
                }
            }

            // Fallback to trying direct asset path for default sprites
            if (!spriteData && ['object-tile', 'tile', 'npc-tile', 'transporter'].includes(objType.sprite)) {
                spriteData = `../assets/${objType.sprite}.png`;
            }

            const thumbnailHTML = spriteData
                ? `<img src="${spriteData}" alt="${objType.sprite}" onerror="this.parentElement.innerHTML='<div class=\\'object-type-no-sprite\\'>?</div>'">`
                : `<div class="object-type-no-sprite">?</div>`;

            item.innerHTML = `
                <div class="object-type-list-preview">
                    ${thumbnailHTML}
                </div>
                <div class="object-type-list-info">
                    <div class="object-type-list-name">${objType.name}</div>
                    <div class="object-type-list-meta">
                        ${objType.sprite}
                    </div>
                </div>
                <button class="object-type-list-delete" data-id="${objType.id}" title="Delete object type">×</button>
            `;

            item.addEventListener('click', (e) => {
                if (!e.target.classList.contains('object-type-list-delete')) {
                    this.selectObjectType(objType.id);
                }
            });

            const deleteBtn = item.querySelector('.object-type-list-delete');
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (confirm(`Delete object type "${objType.name}"?`)) {
                    this.configManager.deleteObjectType(objType.id);
                    if (this.selectedTypeId === objType.id) {
                        this.selectedTypeId = null;
                        this.clearEditor();
                    }
                }
            });

            container.appendChild(item);
        });
    }

    selectObjectType(id) {
        this.selectedTypeId = id;
        this.refreshObjectTypesList();
        this.loadObjectType(id);
    }

    loadObjectType(id) {
        const objType = this.configManager.getObjectType(id);
        if (!objType) return;

        const editorContainer = document.getElementById('object-type-editor-container');
        const propertiesContent = document.getElementById('object-type-properties-content');

        // Editor content
        editorContainer.innerHTML = `
            <div class="object-type-editor-content">
                <h3>${objType.name}</h3>
                <div class="form-group">
                    <label>ID:</label>
                    <input type="text" class="form-control" id="objtype-id" value="${objType.id}" disabled>
                </div>
                <div class="form-group">
                    <label>Name:</label>
                    <input type="text" class="form-control" id="objtype-name" value="${objType.name}">
                </div>
                <div class="form-group">
                    <label>Sprite:</label>
                    <select class="form-control" id="objtype-sprite">
                        ${this.getSpriteOptions(objType.sprite)}
                    </select>
                </div>
                <div class="form-group">
                    <label>Description:</label>
                    <textarea class="form-control" id="objtype-description" rows="3">${objType.description || ''}</textarea>
                </div>
                <button class="btn btn-primary" id="objtype-save">Save Changes</button>
            </div>
        `;

        // Preview content - get sprite with fallbacks
        let spriteData = this.configManager.getSprite(objType.sprite);

        if (!spriteData) {
            const metadata = this.configManager.getSpriteMetadata(objType.sprite);
            if (metadata && metadata.frames && metadata.frames.length > 0) {
                spriteData = metadata.frames[0];
            }
        }

        if (!spriteData && ['object-tile', 'tile', 'npc-tile', 'transporter'].includes(objType.sprite)) {
            spriteData = `../assets/${objType.sprite}.png`;
        }

        propertiesContent.innerHTML = `
            <div class="object-type-preview">
                <h4>Preview</h4>
                <div class="object-type-preview-sprite">
                    ${spriteData ? `<img src="${spriteData}" alt="${objType.sprite}" onerror="this.parentElement.innerHTML='<div class=\\'no-sprite\\'>No sprite</div>'">` : '<div class="no-sprite">No sprite</div>'}
                </div>
                <div class="object-type-info">
                    <strong>ID:</strong> ${objType.id}<br>
                    <strong>Sprite:</strong> ${objType.sprite}
                </div>
            </div>
        `;

        // Attach save handler
        document.getElementById('objtype-save')?.addEventListener('click', () => {
            this.saveObjectType(id);
        });

        // Auto-save on input
        ['objtype-name', 'objtype-sprite', 'objtype-description'].forEach(inputId => {
            document.getElementById(inputId)?.addEventListener('change', () => {
                this.saveObjectType(id);
            });
        });
    }

    saveObjectType(id) {
        const name = document.getElementById('objtype-name')?.value;
        const sprite = document.getElementById('objtype-sprite')?.value;
        const description = document.getElementById('objtype-description')?.value;

        if (!name || !sprite) {
            alert('Name and sprite are required');
            return;
        }

        this.configManager.updateObjectType(id, {
            name,
            sprite,
            description
        });

        // Refresh preview
        this.loadObjectType(id);
    }

    getSpriteOptions(selectedSprite) {
        const sprites = this.configManager.getAllSpriteMetadata();
        let options = '<option value="">-- Select Sprite --</option>';
        sprites.forEach(({ key }) => {
            const selected = key === selectedSprite ? 'selected' : '';
            options += `<option value="${key}" ${selected}>${key}</option>`;
        });
        return options;
    }

    createNewObjectType() {
        const id = prompt('Enter object type ID (e.g., "tree", "rock"):');
        if (!id) return;

        const name = prompt('Enter object type name:', id);
        if (!name) return;

        if (this.configManager.addObjectType(id, { name })) {
            this.selectObjectType(id);
        } else {
            alert('Object type with this ID already exists');
        }
    }

    clearEditor() {
        const editorContainer = document.getElementById('object-type-editor-container');
        const propertiesContent = document.getElementById('object-type-properties-content');

        editorContainer.innerHTML = `
            <div class="object-type-editor-empty">
                <div class="empty-state">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="3" width="7" height="7"/>
                        <rect x="14" y="3" width="7" height="7"/>
                        <rect x="14" y="14" width="7" height="7"/>
                        <rect x="3" y="14" width="7" height="7"/>
                    </svg>
                    <p>Select an object type or create a new one to get started</p>
                </div>
            </div>
        `;

        propertiesContent.innerHTML = `
            <div class="empty-state-small">
                <p>No object type selected</p>
            </div>
        `;
    }

    filterObjectTypes(query) {
        const items = document.querySelectorAll('.object-type-list-item');
        const lowerQuery = query.toLowerCase();

        items.forEach(item => {
            const name = item.querySelector('.object-type-list-name')?.textContent.toLowerCase();
            const meta = item.querySelector('.object-type-list-meta')?.textContent.toLowerCase();

            if (name?.includes(lowerQuery) || meta?.includes(lowerQuery)) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        });
    }
}
