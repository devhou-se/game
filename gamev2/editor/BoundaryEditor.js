// BoundaryEditor - Handles polygon boundary editing for rooms
class BoundaryEditor {
    constructor(gridEditor) {
        this.gridEditor = gridEditor;
        this.boundaryVertices = [];
        this.selectedVertexIndex = null;
        this.hoveredVertexIndex = null;
        this.isDraggingVertex = false;
    }

    // Load boundary from current room config
    loadBoundary() {
        const currentRoom = this.gridEditor.currentRoom;
        if (!currentRoom) {
            this.boundaryVertices = [];
            return;
        }

        const room = this.gridEditor.configManager.getRoom(currentRoom);
        if (room.boundary && Array.isArray(room.boundary)) {
            // Deep copy
            this.boundaryVertices = room.boundary.map(v => [v[0], v[1]]);
        } else {
            // Create default boundary
            const maxGridX = Math.floor(this.gridEditor.worldWidth / this.gridEditor.gridSize);
            const maxGridY = Math.floor(this.gridEditor.worldHeight / this.gridEditor.gridSize);
            this.boundaryVertices = [
                [0, 0],
                [maxGridX, 0],
                [maxGridX, maxGridY],
                [0, maxGridY]
            ];
        }
    }

    // Save boundary to current room config
    saveBoundary() {
        const currentRoom = this.gridEditor.currentRoom;
        if (!currentRoom) return;

        const room = this.gridEditor.configManager.getRoom(currentRoom);
        room.boundary = this.boundaryVertices.map(v => [v[0], v[1]]);
    }

    // Convert client coordinates to grid position for boundary vertices (rounds to nearest grid line)
    getBoundaryGridPosition(clientX, clientY) {
        const rect = this.gridEditor.canvas.getBoundingClientRect();
        const x = (clientX - rect.left - this.gridEditor.offsetX) / this.gridEditor.scale;
        const y = (clientY - rect.top - this.gridEditor.offsetY) / this.gridEditor.scale;
        const gridX = Math.round(x / this.gridEditor.gridSize);
        const gridY = Math.round(y / this.gridEditor.gridSize);
        return { gridX, gridY };
    }

    // Handle mouse down in boundary editing mode
    handleMouseDown(e) {
        const { gridX, gridY } = this.getBoundaryGridPosition(e.clientX, e.clientY);

        // Check if clicking on a vertex
        const vertexRadius = 0.5; // In grid units
        for (let i = 0; i < this.boundaryVertices.length; i++) {
            const vertex = this.boundaryVertices[i];
            const dist = Math.sqrt(
                Math.pow(gridX - vertex[0], 2) + Math.pow(gridY - vertex[1], 2)
            );
            if (dist < vertexRadius) {
                this.selectedVertexIndex = i;
                this.isDraggingVertex = true;
                return true; // Handled
            }
        }

        // Otherwise add a new vertex
        this.boundaryVertices.push([gridX, gridY]);
        this.saveBoundary();
        return true; // Handled
    }

    // Handle mouse move in boundary editing mode
    handleMouseMove(e) {
        // Handle vertex dragging
        if (this.isDraggingVertex && this.selectedVertexIndex !== null) {
            const { gridX, gridY } = this.getBoundaryGridPosition(e.clientX, e.clientY);
            this.boundaryVertices[this.selectedVertexIndex] = [gridX, gridY];
            this.saveBoundary();
            return true; // Handled
        }

        // Check for vertex hover
        if (!this.isDraggingVertex) {
            const { gridX, gridY } = this.getBoundaryGridPosition(e.clientX, e.clientY);
            const vertexRadius = 0.5;
            let foundHover = false;
            for (let i = 0; i < this.boundaryVertices.length; i++) {
                const vertex = this.boundaryVertices[i];
                const dist = Math.sqrt(
                    Math.pow(gridX - vertex[0], 2) + Math.pow(gridY - vertex[1], 2)
                );
                if (dist < vertexRadius) {
                    if (this.hoveredVertexIndex !== i) {
                        this.hoveredVertexIndex = i;
                        return true; // Needs render
                    }
                    foundHover = true;
                    break;
                }
            }
            if (!foundHover && this.hoveredVertexIndex !== null) {
                this.hoveredVertexIndex = null;
                return true; // Needs render
            }
        }

        return false; // Not handled
    }

    // Handle mouse up
    handleMouseUp(e) {
        this.isDraggingVertex = false;
    }

    // Handle right-click context menu
    handleContextMenu(e) {
        if (this.hoveredVertexIndex !== null) {
            // Delete the hovered vertex (must have at least 3 vertices for a polygon)
            if (this.boundaryVertices.length > 3) {
                this.boundaryVertices.splice(this.hoveredVertexIndex, 1);
                this.hoveredVertexIndex = null;
                this.selectedVertexIndex = null;
                this.saveBoundary();
                return true; // Handled
            }
        }
        return false; // Not handled
    }

    // Handle key down
    handleKeyDown(e) {
        // Delete key to remove selected or hovered vertex
        if ((e.key === 'Delete' || e.key === 'Backspace')) {
            const indexToDelete = this.selectedVertexIndex !== null ?
                this.selectedVertexIndex : this.hoveredVertexIndex;

            if (indexToDelete !== null && this.boundaryVertices.length > 3) {
                this.boundaryVertices.splice(indexToDelete, 1);
                this.hoveredVertexIndex = null;
                this.selectedVertexIndex = null;
                this.saveBoundary();
                return true; // Handled
            }
        }
        return false; // Not handled
    }

    // Draw boundary polygon
    draw(ctx, gridSize) {
        if (this.boundaryVertices.length < 2) return;

        // Draw polygon lines
        ctx.strokeStyle = '#00ff00';
        ctx.lineWidth = 3;
        ctx.setLineDash([]);

        ctx.beginPath();
        const firstVertex = this.boundaryVertices[0];
        ctx.moveTo(firstVertex[0] * gridSize, firstVertex[1] * gridSize);

        for (let i = 1; i < this.boundaryVertices.length; i++) {
            const vertex = this.boundaryVertices[i];
            ctx.lineTo(vertex[0] * gridSize, vertex[1] * gridSize);
        }
        ctx.closePath();
        ctx.stroke();

        // Draw vertices
        for (let i = 0; i < this.boundaryVertices.length; i++) {
            const vertex = this.boundaryVertices[i];
            const x = vertex[0] * gridSize;
            const y = vertex[1] * gridSize;

            // Determine vertex color and size based on state
            let fillColor = '#00ff00'; // default green
            let radius = 6;
            let glowColor = null;

            if (i === this.selectedVertexIndex) {
                // Selected vertex - yellow with larger radius
                fillColor = '#ffff00';
                radius = 8;
            } else if (i === this.hoveredVertexIndex) {
                // Hovered vertex - cyan/light blue with glow
                fillColor = '#00ffff';
                radius = 7;
                glowColor = 'rgba(0, 255, 255, 0.5)';
            }

            // Draw glow for hovered vertex
            if (glowColor) {
                ctx.fillStyle = glowColor;
                ctx.beginPath();
                ctx.arc(x, y, radius + 4, 0, Math.PI * 2);
                ctx.fill();
            }

            // Draw vertex circle
            ctx.fillStyle = fillColor;
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.arc(x, y, radius, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();

            // Draw vertex number
            ctx.fillStyle = i === this.hoveredVertexIndex || i === this.selectedVertexIndex ? '#000000' : '#000000';
            ctx.font = 'bold 10px monospace';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(i.toString(), x, y);
        }
    }

    // Reset state
    reset() {
        this.boundaryVertices = [];
        this.selectedVertexIndex = null;
        this.hoveredVertexIndex = null;
        this.isDraggingVertex = false;
    }
}
