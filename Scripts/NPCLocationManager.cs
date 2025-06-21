using Godot;
using System.Collections.Generic;

public class NPCLocationManager : Node
{
    private static NPCLocationManager _instance;
    public static NPCLocationManager Instance
    {
        get
        {
            if (_instance == null)
            {
                _instance = new NPCLocationManager();
            }
            return _instance;
        }
    }
    
    private Dictionary<string, Dictionary<string, Vector2>> locationMappings;
    
    public NPCLocationManager()
    {
        InitializeLocationMappings();
    }
    
    private void InitializeLocationMappings()
    {
        locationMappings = new Dictionary<string, Dictionary<string, Vector2>>();
        
        // World locations
        var worldLocations = new Dictionary<string, Vector2>();
        worldLocations["vending machine"] = new Vector2(-200, -150); // Top left corner - more visible location
        worldLocations["center"] = new Vector2(0, 0);
        worldLocations["north entrance"] = new Vector2(0, -100);
        worldLocations["south entrance"] = new Vector2(0, 100);
        worldLocations["east plaza"] = new Vector2(100, 0);
        worldLocations["west plaza"] = new Vector2(-100, 0);
        worldLocations["top left corner"] = new Vector2(-200, -150);
        worldLocations["top right corner"] = new Vector2(200, -150);
        worldLocations["bottom left corner"] = new Vector2(-200, 150);
        worldLocations["bottom right corner"] = new Vector2(200, 150);
        
        locationMappings["World"] = worldLocations;
        
        // Tokyo Overworld locations (for future use)
        var tokyoLocations = new Dictionary<string, Vector2>();
        tokyoLocations["7-11"] = new Vector2(200, 50);
        tokyoLocations["station"] = new Vector2(-150, -80);
        tokyoLocations["ramen shop"] = new Vector2(80, -40);
        
        locationMappings["Tokyo"] = tokyoLocations;
    }
    
    public Vector2? GetLocation(string world, string area)
    {
        if (locationMappings.ContainsKey(world) && locationMappings[world].ContainsKey(area))
        {
            return locationMappings[world][area];
        }
        
        GD.PrintErr($"Location not found: {world} - {area}");
        return null;
    }
    
    public void PlaceNPC(string npcName, string world, string area)
    {
        var coords = GetLocation(world, area);
        if (!coords.HasValue)
        {
            GD.PrintErr($"Cannot place NPC {npcName}: location not found");
            return;
        }
        
        PlaceNPCAtCoords(npcName, coords.Value);
    }
    
    public void PlaceNPCAtCoords(string npcName, Vector2 coords)
    {
        // Get the current scene
        var currentScene = GetTree()?.CurrentScene;
        if (currentScene == null)
        {
            GD.PrintErr("No current scene found");
            return;
        }
        
        // Find the Characters node (with YSort)
        var charactersNode = currentScene.GetNode("Characters");
        if (charactersNode == null)
        {
            // Try alternative path
            charactersNode = currentScene.GetNode("YSort/Characters");
            if (charactersNode == null)
            {
                GD.PrintErr("Characters node not found in current scene");
                return;
            }
        }
        
        // Check if NPC already exists
        foreach (Node child in charactersNode.GetChildren())
        {
            if (child is NPC npc && npc.NPCName == npcName)
            {
                // Move existing NPC
                npc.Position = coords;
                GD.Print($"Moved existing NPC {npcName} to {coords}");
                return;
            }
        }
        
        // Create new NPC if not found
        var npcScene = GD.Load<PackedScene>("res://Scenes/NPC.tscn");
        if (npcScene == null)
        {
            GD.PrintErr("Failed to load NPC scene");
            return;
        }
        
        var newNPC = npcScene.Instance() as NPC;
        if (newNPC == null)
        {
            GD.PrintErr("Failed to instantiate NPC");
            return;
        }
        
        // Configure the NPC
        newNPC.Name = npcName;
        newNPC.NPCName = npcName;
        newNPC.Position = coords;
        
        // Add to scene
        charactersNode.AddChild(newNPC);
        GD.Print($"Created new NPC {npcName} at {coords}");
    }
    
    public void PlaceNPCFromDefinition(string definitionId, string world, string area)
    {
        var coords = GetLocation(world, area);
        if (!coords.HasValue)
        {
            GD.PrintErr($"Cannot place NPC from definition {definitionId}: location not found");
            return;
        }
        
        PlaceNPCFromDefinitionAtCoords(definitionId, coords.Value);
    }
    
    public void PlaceNPCFromDefinitionAtCoords(string definitionId, Vector2 coords)
    {
        // Load NPC scene
        var npcScene = GD.Load<PackedScene>("res://Scenes/NPC.tscn");
        if (npcScene == null)
        {
            GD.PrintErr("Failed to load NPC scene");
            return;
        }
        
        var npc = npcScene.Instance() as NPC;
        if (npc == null)
        {
            GD.PrintErr("Failed to instantiate NPC");
            return;
        }
        
        // Set the definition ID so the NPC can load its data
        npc.NPCDefinitionId = definitionId;
        
        // Get the current scene
        var currentScene = GetTree()?.CurrentScene;
        if (currentScene == null)
        {
            GD.PrintErr("No current scene found");
            npc.QueueFree();
            return;
        }
        
        // Find the Characters node (with YSort)
        var charactersNode = currentScene.GetNode("Characters");
        if (charactersNode == null)
        {
            // Try alternative path
            charactersNode = currentScene.GetNode("YSort/Characters");
            if (charactersNode == null)
            {
                GD.PrintErr("Characters node not found in current scene");
                npc.QueueFree();
                return;
            }
        }
        
        // Set position and add to scene
        npc.Position = coords;
        charactersNode.AddChild(npc);
        GD.Print($"Created NPC {npc.NPCName} from definition at {coords}");
    }
}