using Godot;
using System;

public partial class TestScript : Node
{
    private float timer = 0.0f;
    
    public override void _Ready()
    {
        GD.Print("=== TestScript Started ===");
        
        // Check for DayNightController
        var main = GetNodeOrNull("/root/Main");
        if (main != null)
        {
            GD.Print($"Main found at: {main.GetPath()}");
            var dayNight = main.GetParent()?.GetNodeOrNull<DayNightController>("DayNightController");
            if (dayNight != null)
            {
                GD.Print($"DayNightController found at: {dayNight.GetPath()}");
            }
            else
            {
                GD.Print("DayNightController NOT found");
            }
        }
        
        // Check for CanvasModulate
        foreach (Node child in GetTree().Root.GetChildren())
        {
            if (child is CanvasModulate cm)
            {
                GD.Print($"Found CanvasModulate: {cm.Name} at {cm.GetPath()}, Color: {cm.Color}");
            }
        }
        
        // Check for HUD
        var hud = GetNodeOrNull("/root/Main/UI/HUD");
        if (hud != null)
        {
            GD.Print($"HUD found at: {hud.GetPath()}, Script: {hud.GetScript()}");
        }
    }
    
    public override void _Process(float delta)
    {
        timer += delta;
        if (timer >= 3.0f) // Every 3 seconds
        {
            timer = 0.0f;
            
            // Check canvas modulate color
            foreach (Node child in GetTree().Root.GetChildren())
            {
                if (child is CanvasModulate cm)
                {
                    GD.Print($"CanvasModulate Color: {cm.Color}");
                    break;
                }
            }
        }
    }
}