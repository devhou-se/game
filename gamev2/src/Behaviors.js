/**
 * Behaviors - Modular behavior system for GameObject interactions
 * Each behavior defines how an object interacts with the player
 */

const Behaviors = {
    /**
     * TELEPORT - Moves player to different location/room
     * Properties: target {room, gridX, gridY}
     */
    teleport: {
        requiresInteraction: false,
        execute(player, scene, object) {
            const target = object.properties.target;
            if (!target) {
                console.warn('Teleporter missing target property');
                return;
            }

            if (target.room && target.room !== scene.currentRoom) {
                // Cross-room teleport
                scene.changeRoom(target.room, target.gridX, target.gridY);
            } else {
                // Same-room teleport
                player.setGridPosition(target.gridX, target.gridY, true);
            }

            scene.playSound('teleport');
        }
    },

    /**
     * SPEED BOOST - Temporarily increases player movement speed
     * Properties: multiplier (default 2), duration (default 5000ms)
     */
    speedBoost: {
        requiresInteraction: false,
        execute(player, scene, object) {
            const multiplier = object.properties.multiplier || 2;
            const duration = object.properties.duration || 5000;

            player.applySpeedBoost(multiplier, duration);
            scene.showFloatingText('+Speed!', object.gridX, object.gridY, '#00ff00');
            scene.removeObject(object);
            scene.playSound('powerup');
        }
    },

    /**
     * HEALTH RESTORE - Restores player health
     * Properties: healAmount (default 25)
     */
    healthRestore: {
        requiresInteraction: false,
        execute(player, scene, object) {
            const amount = object.properties.healAmount || 25;
            const actualHealed = player.heal(amount);

            if (actualHealed > 0) {
                scene.showFloatingText(`+${actualHealed} HP`, object.gridX, object.gridY, '#ff0000');
                scene.removeObject(object);
                scene.playSound('heal');
            }
        }
    },

    /**
     * ENERGY RESTORE - Restores player energy
     * Properties: energyAmount (default 25)
     */
    energyRestore: {
        requiresInteraction: false,
        execute(player, scene, object) {
            const amount = object.properties.energyAmount || 25;
            const actualRestored = player.restoreEnergy(amount);

            if (actualRestored > 0) {
                scene.showFloatingText(`+${actualRestored} Energy`, object.gridX, object.gridY, '#0088ff');
                scene.removeObject(object);
                scene.playSound('energy');
            }
        }
    },

    /**
     * VENDING MACHINE - Dispenses items with cooldown
     * Properties: dispensedItem (type), cooldown (ms), dispenseOffset (grid cells)
     */
    vendingMachine: {
        requiresInteraction: true,
        execute(player, scene, object) {
            const now = Date.now();
            const nextDispenseTime = object.state.nextDispenseTime || 0;

            if (now < nextDispenseTime) {
                const remaining = Math.ceil((nextDispenseTime - now) / 1000);
                scene.showMessage(`Machine cooling down... ${remaining}s`);
                return;
            }

            const itemType = object.properties.dispensedItem;
            if (!itemType) {
                console.warn('Vending machine missing dispensedItem property');
                return;
            }

            const offsetY = object.properties.dispenseOffset || 1;
            scene.spawnObject(itemType, object.gridX, object.gridY + offsetY);

            object.state.nextDispenseTime = now + (object.properties.cooldown || 2000);
            scene.playSound('dispense');
            scene.showMessage('Item dispensed!');
        }
    },

    /**
     * DOOR - Room transition with optional lock
     * Properties: targetRoom, entryX, entryY, keyId, lockedMessage
     */
    door: {
        requiresInteraction: true,
        execute(player, scene, object) {
            // Check if door is locked
            if (object.state.locked === undefined) {
                object.state.locked = object.properties.keyId ? true : false;
            }

            if (object.state.locked) {
                const keyId = object.properties.keyId;
                if (!player.hasItem(keyId)) {
                    scene.showMessage(object.properties.lockedMessage || "This door is locked!");
                    scene.playSound('locked');
                    return;
                }

                // Unlock the door
                object.state.locked = false;
                scene.updateObjectSprite(object, object.properties.unlockedSprite || object.sprite);
                scene.showMessage('Door unlocked!');
                scene.playSound('unlock');
            }

            // Transition to target room
            scene.changeRoom(
                object.properties.targetRoom,
                object.properties.entryX,
                object.properties.entryY
            );
        }
    },

    /**
     * COLLECTIBLE - Adds item to player inventory
     * Properties: itemId, quantity (default 1), displayName
     */
    collectible: {
        requiresInteraction: false,
        execute(player, scene, object) {
            const itemId = object.properties.itemId;
            const quantity = object.properties.quantity || 1;
            const displayName = object.properties.displayName || itemId;

            player.addItem(itemId, quantity);
            scene.showFloatingText(`+${displayName}`, object.gridX, object.gridY, '#ffff00');
            scene.removeObject(object);
            scene.playSound('collect');
        }
    },

    /**
     * SWITCH - Toggles state and triggers other objects
     * Properties: triggers (array of object IDs)
     */
    switch: {
        requiresInteraction: true,
        execute(player, scene, object) {
            object.state.active = !object.state.active;

            // Update sprite based on state
            const spriteKey = object.state.active ?
                (object.properties.activeSprite || object.sprite) :
                (object.properties.inactiveSprite || object.sprite);
            scene.updateObjectSprite(object, spriteKey);

            // Trigger connected objects
            const triggers = object.properties.triggers || [];
            triggers.forEach(targetId => {
                const target = scene.getObjectById(targetId);
                if (target) {
                    target.state.triggered = object.state.active;
                    scene.onObjectTriggered(target);
                }
            });

            scene.playSound('switch');
        }
    },

    /**
     * CHECKPOINT - Save player progress
     * Properties: none
     */
    checkpoint: {
        requiresInteraction: true,
        execute(player, scene, object) {
            if (object.state.activated) {
                scene.showMessage('Already activated!');
                return;
            }

            player.saveCheckpoint(scene.currentRoom, object.gridX, object.gridY);
            object.state.activated = true;
            scene.updateObjectSprite(object, object.properties.activatedSprite || object.sprite);
            scene.showMessage('Progress saved!');
            scene.playSound('save');
        }
    },

    /**
     * BOUNCER - Pushes player away
     * Properties: direction ('away'|'up'|'down'|'left'|'right'), force (cells)
     */
    bouncer: {
        requiresInteraction: false,
        execute(player, scene, object) {
            const direction = object.properties.direction || 'away';
            const force = object.properties.force || 3;

            let dx = 0, dy = 0;

            if (direction === 'away') {
                // Push away from object
                dx = Math.sign(player.gridX - object.gridX) * force;
                dy = Math.sign(player.gridY - object.gridY) * force;
            } else {
                // Specific direction
                const dirs = {
                    up: [0, -force],
                    down: [0, force],
                    left: [-force, 0],
                    right: [force, 0]
                };
                [dx, dy] = dirs[direction] || [0, 0];
            }

            player.knockback(dx, dy);
            scene.playSound('bounce');
        }
    },

    /**
     * SIGN - Displays message
     * Properties: message, title (default "Sign")
     */
    sign: {
        requiresInteraction: true,
        execute(player, scene, object) {
            const message = object.properties.message || "...";
            const title = object.properties.title || "Sign";
            scene.showDialogue(message, title);
        }
    },

    /**
     * TERMINAL - Interactive terminal with API support
     * Properties: apiEndpoint (optional), staticMessage
     */
    terminal: {
        requiresInteraction: true,
        async execute(player, scene, object) {
            if (object.properties.apiEndpoint) {
                try {
                    scene.showMessage('Connecting...');
                    const response = await fetch(object.properties.apiEndpoint);
                    const data = await response.json();
                    const message = data.message || JSON.stringify(data);
                    scene.showDialogue(message, object.properties.title || "Terminal");
                } catch (error) {
                    console.error('Terminal API error:', error);
                    scene.showDialogue('Connection failed.', 'Terminal Error');
                }
            } else {
                const message = object.properties.staticMessage || "No data available.";
                scene.showDialogue(message, object.properties.title || "Terminal");
            }
        }
    },

    /**
     * DAMAGE_ZONE - Damages player on contact
     * Properties: damageAmount (default 10), damageInterval (ms, default 1000)
     */
    damageZone: {
        requiresInteraction: false,
        execute(player, scene, object) {
            const now = Date.now();
            const lastDamageTime = object.state.lastDamageTime || 0;
            const damageInterval = object.properties.damageInterval || 1000;

            if (now - lastDamageTime < damageInterval) {
                return; // Still in cooldown
            }

            const damage = object.properties.damageAmount || 10;
            player.takeDamage(damage);
            object.state.lastDamageTime = now;
            scene.showFloatingText(`-${damage} HP`, player.gridX, player.gridY, '#ff0000');
            scene.playSound('damage');
        }
    },

    /**
     * CONDITIONAL - Object behavior changes based on trigger state
     * Used with switches - doesn't execute directly
     */
    conditional: {
        requiresInteraction: false,
        execute(player, scene, object) {
            // This behavior is triggered by switches
            // The actual logic is in scene.onObjectTriggered()
        }
    }
};
