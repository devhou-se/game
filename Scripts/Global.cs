using Godot;
using System;

public class Global : Node
{
    public static string PlayerName { get; set; } = "";
    public static GameController Controller;

    // Conversation cooldown to prevent rapid-fire NPC interactions
    public static float ConversationCooldown { get; set; } = 0.0f;

    public override void _Process(float delta)
    {
        if (ConversationCooldown > 0)
        {
            ConversationCooldown -= delta;
        }
    }
}