class MenuManager {
    constructor(scene) {
        this.scene = scene;
        this.visible = false;
        this.selectedIndex = 0;
        this.options = [];

        this.create();
    }

    create() {
        // Semi-transparent background overlay
        this.overlay = this.scene.add.graphics();
        this.overlay.fillStyle(0x000000, 0.85);
        this.overlay.fillRect(0, 0, this.scene.cameras.main.width, this.scene.cameras.main.height);
        this.overlay.setScrollFactor(0);
        this.overlay.setDepth(2000);
        this.overlay.setInteractive(
            new Phaser.Geom.Rectangle(0, 0, this.scene.cameras.main.width, this.scene.cameras.main.height),
            Phaser.Geom.Rectangle.Contains
        );
        this.overlay.on('pointerdown', () => this.hide());

        // Menu container
        this.container = this.scene.add.container(0, 0);
        this.container.setScrollFactor(0);
        this.container.setDepth(2001);

        // Menu panel
        const panelWidth = 300;
        const panelHeight = 250;
        const panelX = (this.scene.cameras.main.width - panelWidth) / 2;
        const panelY = (this.scene.cameras.main.height - panelHeight) / 2;

        const panel = this.scene.add.graphics();
        panel.fillStyle(0x1a1a1a, 1);
        panel.fillRect(panelX, panelY, panelWidth, panelHeight);
        panel.lineStyle(2, 0x666666, 1);
        panel.strokeRect(panelX, panelY, panelWidth, panelHeight);
        this.container.add(panel);

        // Menu title
        this.titleText = this.scene.add.text(
            this.scene.cameras.main.width / 2,
            panelY + 30,
            'MENU',
            {
                fontSize: '24px',
                fill: '#ffffff',
                fontFamily: 'PixelOperatorMonoBold'
            }
        );
        this.titleText.setOrigin(0.5, 0.5);
        this.titleText.setResolution(1);
        this.titleText.setScrollFactor(0);
        this.titleText.setDepth(2002);
        this.titleText.setVisible(false);

        // Menu options
        const menuOptions = [
            { text: 'Achievements', action: () => this.scene.showAchievements() },
            { text: 'Map', action: () => this.scene.showMap() },
            { text: 'Credits', action: () => this.scene.showCredits() }
        ];

        const startY = panelY + 80;
        const spacing = 50;

        this.options = [];

        menuOptions.forEach((option, index) => {
            const optionText = this.scene.add.text(
                this.scene.cameras.main.width / 2,
                startY + (index * spacing),
                option.text,
                {
                    fontSize: '24px',
                    fill: '#ffffff',
                    fontFamily: 'PixelOperatorMono'
                }
            );
            optionText.setOrigin(0.5, 0.5);
            optionText.setResolution(1);
            optionText.setScrollFactor(0);
            optionText.setDepth(2002);
            optionText.setInteractive({ useHandCursor: true });
            optionText.setVisible(false);

            // Store reference with action
            this.options.push({
                textObject: optionText,
                action: option.action,
                index: index
            });

            // Hover effects
            optionText.on('pointerover', () => {
                this.select(index);
            });
            optionText.on('pointerdown', () => {
                this.activate();
            });
        });

        // Hide menu initially
        this.container.setVisible(false);
        this.overlay.setVisible(false);
    }

    toggle() {
        if (this.visible) {
            this.hide();
        } else {
            this.show();
        }
    }

    show() {
        this.visible = true;
        this.overlay.setVisible(true);
        this.container.setVisible(true);
        this.titleText.setVisible(true);
        this.options.forEach(option => option.textObject.setVisible(true));
        this.selectedIndex = 0;
        this.updateSelection();
    }

    hide() {
        this.visible = false;
        this.overlay.setVisible(false);
        this.container.setVisible(false);
        this.titleText.setVisible(false);
        this.options.forEach(option => option.textObject.setVisible(false));
    }

    select(index) {
        this.selectedIndex = index;
        this.updateSelection();
    }

    updateSelection() {
        // Update visual feedback for all menu options
        this.options.forEach((option, index) => {
            if (index === this.selectedIndex) {
                option.textObject.setFill('#ffff00');
            } else {
                option.textObject.setFill('#ffffff');
            }
        });
    }

    activate() {
        const selectedOption = this.options[this.selectedIndex];
        if (selectedOption) {
            selectedOption.action();
            this.hide();
        }
    }

    selectPrevious() {
        this.selectedIndex = (this.selectedIndex - 1 + this.options.length) % this.options.length;
        this.updateSelection();
    }

    selectNext() {
        this.selectedIndex = (this.selectedIndex + 1) % this.options.length;
        this.updateSelection();
    }

    isVisible() {
        return this.visible;
    }
}
