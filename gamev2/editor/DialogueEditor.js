// DialogueEditor - Handles dialogue editing modal
class DialogueEditor {
    constructor() {
        this.modal = document.getElementById('dialogue-modal');
        this.container = document.getElementById('dialogue-lines');
        this.addBtn = document.getElementById('add-dialogue-line');
        this.saveBtn = document.getElementById('save-dialogue');
    }

    // Show dialogue editor modal
    show(dialogue, onSave) {
        this.container.innerHTML = '';
        dialogue.forEach((line, index) => {
            this.addDialogueLine(line, index);
        });

        this.addBtn.onclick = () => {
            this.addDialogueLine('', dialogue.length);
        };

        this.saveBtn.onclick = () => {
            const lines = Array.from(this.container.querySelectorAll('input'))
                .map(input => input.value)
                .filter(line => line.trim() !== '');
            onSave(lines);
            this.modal.style.display = 'none';
        };

        this.modal.style.display = 'flex';
    }

    // Add a dialogue line input
    addDialogueLine(text, index) {
        const div = document.createElement('div');
        div.className = 'dialogue-line';
        div.innerHTML = `
            <input type="text" class="form-control" value="${text}" placeholder="Dialogue line ${index + 1}">
            <button type="button">×</button>
        `;
        div.querySelector('button').addEventListener('click', () => div.remove());
        this.container.appendChild(div);
    }
}
