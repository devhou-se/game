# Interactive Object System

The game now features a powerful interactive object system that supports various behaviors like teleportation, speed boosts, vending machines, switches, and more.

## Overview

Objects are defined in `config.json` under two sections:
1. **`objectTypes`** - Define object type templates with sprites, behaviors, and properties
2. **Room `objects` arrays** - Place specific object instances in rooms

## Core Components

### 1. GameObject Class (`src/GameObject.js`)
Base class for all interactive objects with:
- Grid-based positioning
- Collision detection
- Interaction range detection
- State management
- Modular behavior system

### 2. Behaviors System (`src/Behaviors.js`)
Predefined behaviors that can be mixed and matched:
- `teleport` - Move player to different location/room
- `speedBoost` - Temporary speed increase
- `healthRestore` - Restore player health
- `energyRestore` - Restore player energy
- `vendingMachine` - Dispense items with cooldown
- `door` - Room transitions with optional locks
- `collectible` - Add items to inventory
- `switch` - Toggle state and trigger other objects
- `checkpoint` - Save player progress
- `bouncer` - Push player away
- `sign` - Display message
- `terminal` - Interactive terminal with API support
- `damageZone` - Damage player on contact
- `conditional` - State changes based on triggers

### 3. Enhanced Character (`src/Character.js`)
Player now has:
- Inventory system (Map of itemId → quantity)
- Health/Energy tracking
- Speed boost mechanics
- Knockback physics
- Checkpoint save/load
- Instant teleportation via `setGridPosition()`

### 4. Floating Text (`src/FloatingText.js`)
Visual feedback system for pickups, damage, etc.

## Configuration Example

### Define Object Types

```json
{
  "objectTypes": {
    "drinkCan": {
      "sprite": "drink_can",
      "behaviors": ["speedBoost"],
      "properties": {
        "multiplier": 2,
        "duration": 5000
      }
    },
    "vendingMachine": {
      "sprite": "vending_machine",
      "behaviors": ["vendingMachine"],
      "interactionRange": 1,
      "properties": {
        "dispensedItem": "drinkCan",
        "cooldown": 2000,
        "dispenseOffset": 1
      }
    },
    "teleporter": {
      "sprite": "teleporter",
      "behaviors": ["teleport"],
      "properties": {
        "target": {
          "room": "SecretRoom",
          "gridX": 7,
          "gridY": 5
        }
      }
    },
    "lockedDoor": {
      "sprite": "door_locked",
      "behaviors": ["door"],
      "interactionRange": 1,
      "initialState": {
        "locked": true
      },
      "properties": {
        "keyId": "blueKey",
        "targetRoom": "Vault",
        "entryX": 2,
        "entryY": 5,
        "lockedMessage": "You need the blue key!",
        "unlockedSprite": "door_unlocked"
      }
    },
    "blueKey": {
      "sprite": "key_blue",
      "behaviors": ["collectible"],
      "properties": {
        "itemId": "blueKey",
        "quantity": 1,
        "displayName": "Blue Key"
      }
    },
    "healthPotion": {
      "sprite": "potion_red",
      "behaviors": ["healthRestore"],
      "properties": {
        "healAmount": 50
      }
    },
    "pressurePlate": {
      "sprite": "plate_off",
      "behaviors": ["switch"],
      "properties": {
        "triggers": ["bridge_01", "gate_02"],
        "activeSprite": "plate_on",
        "inactiveSprite": "plate_off"
      }
    },
    "checkpoint": {
      "sprite": "checkpoint_inactive",
      "behaviors": ["checkpoint"],
      "interactionRange": 1,
      "properties": {
        "activatedSprite": "checkpoint_active"
      }
    }
  }
}
```

### Place Objects in Rooms

```json
{
  "rooms": {
    "Tokyo": {
      "name": "Tokyo",
      "objects": [
        {
          "type": "vendingMachine",
          "gridX": 5,
          "gridY": 3
        },
        {
          "type": "teleporter",
          "gridOffsetX": -2,
          "gridOffsetY": 0
        },
        {
          "type": "blueKey",
          "gridX": 10,
          "gridY": 2
        },
        {
          "type": "lockedDoor",
          "gridX": 12,
          "gridY": 5
        }
      ]
    }
  }
}
```

## Behavior Details

### Automatic vs Interaction-Required

- **Automatic** (`requiresInteraction: false`): Trigger on collision
  - `teleport`, `speedBoost`, `healthRestore`, `collectible`, `bouncer`, `damageZone`

- **Interaction Required** (`requiresInteraction: true`): Press spacebar when near
  - `vendingMachine`, `door`, `switch`, `checkpoint`, `sign`, `terminal`

### Interaction Range

- `interactionRange: 0` - Must be standing on object (collision)
- `interactionRange: 1` - Can interact from adjacent cell (Manhattan distance)
- `interactionRange: 2+` - Can interact from further away

### Object Properties Reference

#### Teleport
```json
"properties": {
  "target": {
    "room": "RoomName",  // Optional, omit for same-room teleport
    "gridX": 5,
    "gridY": 5
  }
}
```

#### Speed Boost
```json
"properties": {
  "multiplier": 2,      // Speed multiplier (2 = 2x speed)
  "duration": 5000      // Duration in milliseconds
}
```

#### Vending Machine
```json
"properties": {
  "dispensedItem": "drinkCan",  // Object type to spawn
  "cooldown": 2000,             // Cooldown in ms
  "dispenseOffset": 1           // Grid cells below machine
}
```

#### Door
```json
"properties": {
  "targetRoom": "Vault",
  "entryX": 2,
  "entryY": 5,
  "keyId": "blueKey",          // Optional, omit for unlocked door
  "lockedMessage": "Locked!",
  "unlockedSprite": "door_open"
}
```

#### Switch/Trigger
```json
"properties": {
  "triggers": ["bridge_01", "gate_02"],  // IDs of objects to trigger
  "activeSprite": "switch_on",
  "inactiveSprite": "switch_off"
}
```

## Player Interaction

### Controls
- **Arrow Keys / WASD** - Move
- **Shift** - Sprint (2x speed, stacks with speed boosts)
- **Spacebar** - Interact with nearby objects
- **ESC** - Menu

### Inventory
Access player inventory in console:
```javascript
scene.player.inventory.get('blueKey')  // Get count of item
scene.player.hasItem('blueKey')        // Check if player has item
```

### Health/Energy
Player starts with 100 health and 100 energy. These can be modified by:
- Health potions (`healthRestore`)
- Energy items (`energyRestore`)
- Damage zones (`damageZone`)

### Checkpoints
Interact with checkpoint objects to save progress. Data is stored in `localStorage`.

## Creating Custom Behaviors

Add new behaviors to `src/Behaviors.js`:

```javascript
Behaviors.myCustomBehavior = {
    requiresInteraction: true,  // or false
    execute(player, scene, object) {
        // Your behavior logic here
        scene.showMessage("Custom behavior triggered!");
    }
};
```

Then reference it in object types:
```json
{
  "customObject": {
    "sprite": "custom_sprite",
    "behaviors": ["myCustomBehavior"],
    "properties": {
      // Custom properties
    }
  }
}
```

## API Integration

Terminal objects can call external APIs:

```json
{
  "apiTerminal": {
    "sprite": "terminal",
    "behaviors": ["terminal"],
    "interactionRange": 1,
    "properties": {
      "apiEndpoint": "https://api.example.com/status",
      "title": "System Status"
    }
  }
}
```

## Sound Effects

The system includes placeholders for sound effects. To implement:
1. Load audio assets in `GameScene.preload()`
2. Update `playSound()` method in GameScene.js to play actual sounds

Current sound hooks:
- `teleport`, `powerup`, `heal`, `energy`, `dispense`, `locked`, `unlock`
- `switch`, `save`, `bounce`, `collect`, `damage`

## Debugging

Enable console logging to see object interactions:
- Inventory changes logged to console
- Health/Energy changes logged
- Speed boost state changes logged
- Object interactions trigger console messages

## Performance

- Objects update only when needed (behaviors drive updates)
- Collision checks use grid-based Manhattan distance
- Sprites pooled and reused between room transitions
- Game state serializable for save/load
