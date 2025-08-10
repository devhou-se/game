# Scripts Directory Structure

This directory contains all game scripts organized by feature/system.

## 📁 Folder Structure

### Characters/
Character behaviors and controllers.
- `Player.cs` - Player input and movement
- `NPC.cs` - NPC AI and dialogue
- `Character.cs/gd` - Base character functionality

### Systems/
Core game systems and managers.
- `Global.cs` - Singleton game state manager
- `GameController.cs` - Main game loop
- Environment and weather controllers
- Save/load system

### UI/
User interface controllers.
- HUD updates
- Menu navigation
- Dialog systems

### Objects/
Interactive object behaviors.
- Doors, items, pickups
- Vending machines
- Props and decorations

### Levels/
Level-specific scripts.
- Level initialization
- Area-specific mechanics
- Cutscene controllers

### Utils/
Helper functions and utilities.
- Math helpers
- Extension methods
- Debug tools

## 🔤 Language Guidelines

### C# Scripts (.cs)
- Primary language for complex logic
- Used for: Core systems, NPCs, Player
- Follow C# naming conventions:
  ```csharp
  public class PlayerController : Node2D
  {
      private int _health;
      public int MaxHealth { get; set; }
      
      public void TakeDamage(int amount)
      {
          // Method implementation
      }
  }
  ```

### GDScript (.gd)
- Used for simpler components
- Quick prototyping
- Environmental effects
- Follow GDScript conventions:
  ```gdscript
  extends Node2D

  var speed = 200
  
  func _ready():
      print("Ready!")
  ```

## 🎯 Best Practices

1. **Single Responsibility**
   - Each script should have one clear purpose
   - Split complex behaviors into components

2. **Use Godot's Node System**
   - Prefer composition over inheritance
   - Communicate via signals when possible

3. **Consistent Naming**
   - Scripts match their scene names
   - Use descriptive variable names
   - Follow language conventions

4. **Performance Considerations**
   - Cache node references in _Ready()
   - Use object pooling for spawned objects
   - Avoid creating objects in _Process()

5. **Error Handling**
   - Check for null references
   - Use Godot's built-in logging
   - Handle edge cases gracefully

## 🔧 Common Patterns

### Singleton Pattern (Global.cs)
```csharp
public class Global : Node
{
    private static Global _instance;
    public static Global Instance => _instance;
    
    public override void _Ready()
    {
        _instance = this;
    }
}
```

### Signal Connection
```csharp
// Connecting signals in C#
button.Connect("pressed", this, nameof(OnButtonPressed));
```

```gdscript
# Connecting signals in GDScript
button.connect("pressed", self, "_on_button_pressed")
```

### Node Reference Caching
```csharp
private AnimationPlayer _animationPlayer;

public override void _Ready()
{
    _animationPlayer = GetNode<AnimationPlayer>("AnimationPlayer");
}
```

## 📝 Documentation

Always include header comments:
```csharp
/// <summary>
/// Controls player movement and input handling
/// </summary>
public class PlayerController : KinematicBody2D
{
    // Implementation
}
```