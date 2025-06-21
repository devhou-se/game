using Godot;
using System;
using System.Collections.Generic;
using DevHouse;

// Build-time resource loading version
public class NPCDefinitions : Node
{
    private Dictionary<string, NPCDefinition> _loadedDefinitions = new Dictionary<string, NPCDefinition>();
    private const string RESOURCES_PATH = "res://NPCDefinitions/Resources/";
    
    public override void _Ready()
    {
        GD.Print("NPCDefinitions autoload ready");
        LoadAllDefinitions();
        GD.Print($"NPCDefinitions: Total definitions loaded: {_loadedDefinitions.Count}");
        foreach (var kvp in _loadedDefinitions)
        {
            GD.Print($"  - {kvp.Key}: {kvp.Value.Name}");
        }
    }
    
    public void LoadAllDefinitions()
    {
        // Try to load from resources first
        var dir = new Godot.Directory();
        bool foundResources = false;
        
        if (dir.Open(RESOURCES_PATH) == Error.Ok)
        {
            dir.ListDirBegin();
            var fileName = dir.GetNext();
            
            while (!string.IsNullOrEmpty(fileName))
            {
                if (fileName.EndsWith(".tres"))
                {
                    LoadResourceDefinition(RESOURCES_PATH + fileName);
                    foundResources = true;
                }
                fileName = dir.GetNext();
            }
            
            dir.ListDirEnd();
        }
        
        // If no resources found, fall back to JSON
        if (!foundResources)
        {
            GD.Print("No .tres resources found, loading from JSON files");
            LoadAllDefinitionsFromJSON();
        }
        else
        {
            GD.Print($"Loaded {_loadedDefinitions.Count} NPC definitions from resources");
        }
    }
    
    private void LoadResourceDefinition(string resourcePath)
    {
        try
        {
            var resource = GD.Load<NPCDefinitionResource>(resourcePath);
            if (resource != null)
            {
                var definition = resource.ToNPCDefinition();
                if (!string.IsNullOrEmpty(definition.Id))
                {
                    _loadedDefinitions[definition.Id] = definition;
                    GD.Print($"Loaded NPC resource: {definition.Name} (ID: {definition.Id})");
                }
            }
        }
        catch (Exception e)
        {
            GD.PrintErr($"Error loading NPC resource from {resourcePath}: {e.Message}");
        }
    }
    
    // Fallback method for development - loads from JSON if resources aren't built
    private void LoadAllDefinitionsFromJSON()
    {
        GD.PrintErr("Resources not found, falling back to JSON loading for development");
        var dir = new Godot.Directory();
        var jsonPath = "res://NPCDefinitions/";
        
        if (!dir.DirExists(jsonPath))
        {
            GD.PrintErr($"NPC definitions directory not found: {jsonPath}");
            return;
        }
        
        if (dir.Open(jsonPath) == Error.Ok)
        {
            dir.ListDirBegin();
            var fileName = dir.GetNext();
            
            while (!string.IsNullOrEmpty(fileName))
            {
                if (fileName.EndsWith(".json") && !fileName.StartsWith("ai_template"))
                {
                    LoadDefinition(jsonPath + fileName);
                }
                fileName = dir.GetNext();
            }
            
            dir.ListDirEnd();
        }
        
        GD.Print($"Loaded {_loadedDefinitions.Count} NPC definitions from JSON");
    }
    
    private void LoadDefinition(string filePath)
    {
        try
        {
            var file = new Godot.File();
            if (file.Open(filePath, Godot.File.ModeFlags.Read) != Error.Ok)
            {
                GD.PrintErr($"Failed to open NPC definition file: {filePath}");
                return;
            }
            
            var jsonContent = file.GetAsText();
            file.Close();
            
            var json = JSON.Parse(jsonContent);
            if (json.Error != Error.Ok)
            {
                GD.PrintErr($"Failed to parse JSON from {filePath}: {json.ErrorString}");
                return;
            }
            
            var dict = json.Result as Godot.Collections.Dictionary;
            if (dict != null && dict.Contains("Id"))
            {
                var definition = DeserializeNPCDefinition(dict);
                if (definition != null && !string.IsNullOrEmpty(definition.Id))
                {
                    _loadedDefinitions[definition.Id] = definition;
                    GD.Print($"Loaded NPC definition: {definition.Name} (ID: {definition.Id})");
                }
            }
        }
        catch (Exception e)
        {
            GD.PrintErr($"Error loading NPC definition from {filePath}: {e.Message}");
        }
    }
    
    public NPCDefinition GetDefinition(string npcId)
    {
        GD.Print($"GetDefinition called for: {npcId}, Available definitions: {_loadedDefinitions.Count}");
        if (_loadedDefinitions.ContainsKey(npcId))
        {
            GD.Print($"Found definition for {npcId}");
            return _loadedDefinitions[npcId];
        }
        GD.PrintErr($"Definition not found for {npcId}");
        return null;
    }
    
    public bool HasDefinition(string npcId)
    {
        return _loadedDefinitions.ContainsKey(npcId);
    }
    
    // Helper method to safely get values from Godot dictionaries
    private T GetDictValue<T>(Godot.Collections.Dictionary dict, string key, T defaultValue)
    {
        if (dict.Contains(key))
        {
            try
            {
                if (typeof(T) == typeof(string))
                {
                    return (T)(object)dict[key].ToString();
                }
                else if (typeof(T) == typeof(float))
                {
                    return (T)(object)Convert.ToSingle(dict[key]);
                }
                else if (typeof(T) == typeof(bool))
                {
                    return (T)(object)Convert.ToBoolean(dict[key]);
                }
                else if (typeof(T) == typeof(int))
                {
                    return (T)(object)Convert.ToInt32(dict[key]);
                }
                return (T)dict[key];
            }
            catch
            {
                return defaultValue;
            }
        }
        return defaultValue;
    }
    
    private NPCDefinition DeserializeNPCDefinition(Godot.Collections.Dictionary dict)
    {
        if (dict == null) return null;
        
        var def = new NPCDefinition();
        
        // Basic Information
        def.Id = GetDictValue(dict, "Id", "");
        def.Name = GetDictValue(dict, "Name", "");
        def.Description = GetDictValue(dict, "Description", "");
        def.Personality = GetDictValue(dict, "Personality", "");
        def.BackgroundStory = GetDictValue(dict, "BackgroundStory", "");
        
        // Visual Properties
        if (dict.Contains("Visual") && dict["Visual"] is Godot.Collections.Dictionary visual)
        {
            def.Visual.SpriteSheetPath = GetDictValue(visual, "SpriteSheetPath", "");
            def.Visual.PortraitPath = GetDictValue(visual, "PortraitPath", "");
            def.Visual.Scale = GetDictValue(visual, "Scale", 1.0f);
            def.Visual.TintColor = GetDictValue(visual, "TintColor", "#FFFFFF");
            def.Visual.UseCustomShader = GetDictValue(visual, "UseCustomShader", false);
            def.Visual.CustomShaderPath = GetDictValue(visual, "CustomShaderPath", "");
        }
        
        // Behavior Properties
        if (dict.Contains("Behavior") && dict["Behavior"] is Godot.Collections.Dictionary behavior)
        {
            def.Behavior.EnableFullInteraction = GetDictValue(behavior, "EnableFullInteraction", true);
            def.Behavior.CaresAboutBaileyButlerOfficeStatus = GetDictValue(behavior, "CaresAboutBaileyButlerOfficeStatus", false);
            def.Behavior.InteractionRadius = GetDictValue(behavior, "InteractionRadius", 32.0f);
            def.Behavior.CanBePickedUp = GetDictValue(behavior, "CanBePickedUp", false);
            def.Behavior.ReactsToWeather = GetDictValue(behavior, "ReactsToWeather", false);
            def.Behavior.ReactsToTimeOfDay = GetDictValue(behavior, "ReactsToTimeOfDay", false);
        }
        
        // Dialogue Properties
        if (dict.Contains("Dialogue") && dict["Dialogue"] is Godot.Collections.Dictionary dialogue)
        {
            var typeStr = GetDictValue(dialogue, "Type", "Simple");
            if (typeStr == "Simple")
            {
                def.Dialogue.Type = DialogueType.Simple;
                if (dialogue.Contains("SimpleDialogueLines") && dialogue["SimpleDialogueLines"] is Godot.Collections.Array lines)
                {
                    def.Dialogue.SimpleDialogueLines.Clear();
                    foreach (var line in lines)
                    {
                        def.Dialogue.SimpleDialogueLines.Add(line.ToString());
                    }
                }
            }
            else if (typeStr == "Complex")
            {
                def.Dialogue.Type = DialogueType.Complex;
                if (dialogue.Contains("ComplexDialogueTree") && dialogue["ComplexDialogueTree"] is Godot.Collections.Dictionary treeDict)
                {
                    def.Dialogue.ComplexDialogueTree = DeserializeDialogueTree(treeDict);
                }
            }
        }
        
        // Movement Properties
        if (dict.Contains("Movement") && dict["Movement"] is Godot.Collections.Dictionary movement)
        {
            var patternStr = GetDictValue(movement, "Pattern", "Random");
            if (Enum.TryParse<MovementPattern>(patternStr, out var movementPattern))
            {
                def.Movement.Pattern = movementPattern;
            }
            
            def.Movement.MoveSpeed = GetDictValue(movement, "MoveSpeed", 50.0f);
            def.Movement.WaitTimeBetweenMoves = GetDictValue(movement, "WaitTimeBetweenMoves", 3.0f);
            def.Movement.CanChasePlayer = GetDictValue(movement, "CanChasePlayer", false);
            def.Movement.ChaseSpeed = GetDictValue(movement, "ChaseSpeed", 100.0f);
            def.Movement.ChaseRadius = GetDictValue(movement, "ChaseRadius", 150.0f);
            def.Movement.AvoidObstacles = GetDictValue(movement, "AvoidObstacles", true);
        }
        
        return def;
    }
    
    private DialogueTree DeserializeDialogueTree(Godot.Collections.Dictionary dict)
    {
        if (dict == null) return null;
        
        var tree = new DialogueTree();
        tree.StartNodeId = GetDictValue(dict, "StartNodeId", "");
        
        if (dict.Contains("Nodes") && dict["Nodes"] is Godot.Collections.Dictionary nodes)
        {
            foreach (var key in nodes.Keys)
            {
                if (nodes[key] is Godot.Collections.Dictionary nodeDict)
                {
                    var node = new DialogueNode();
                    node.Id = GetDictValue(nodeDict, "Id", "");
                    node.Text = GetDictValue(nodeDict, "Text", "");
                    node.NextNodeId = GetDictValue(nodeDict, "NextNodeId", "");
                    node.IsEndNode = GetDictValue(nodeDict, "IsEndNode", false);
                    
                    if (nodeDict.Contains("Choices") && nodeDict["Choices"] is Godot.Collections.Array choices)
                    {
                        node.Choices = new List<DialogueChoice>();
                        foreach (var choice in choices)
                        {
                            if (choice is Godot.Collections.Dictionary choiceDict)
                            {
                                var dialogueChoice = new DialogueChoice();
                                dialogueChoice.Text = GetDictValue(choiceDict, "Text", "");
                                dialogueChoice.NextNodeId = GetDictValue(choiceDict, "NextNodeId", "");
                                dialogueChoice.RequiredFlag = GetDictValue(choiceDict, "RequiredFlag", "");
                                dialogueChoice.SetFlag = GetDictValue(choiceDict, "SetFlag", "");
                                node.Choices.Add(dialogueChoice);
                            }
                        }
                    }
                    
                    tree.Nodes[key.ToString()] = node;
                }
            }
        }
        
        return tree;
    }
    
    public void ApplyDefinitionToNPC(NPC npc, NPCDefinition definition)
    {
        if (npc == null || definition == null) return;
        
        // Basic properties
        npc.NPCName = definition.Name;
        npc.NPCDefinitionId = definition.Id;
        
        // Behavior properties
        npc.EnableFullInteraction = definition.Behavior.EnableFullInteraction;
        npc.CaresAboutBaileyButlerBeingInTheOffice = definition.Behavior.CaresAboutBaileyButlerOfficeStatus;
        
        // Dialogue properties
        if (definition.Dialogue.Type == DialogueType.Simple && 
            definition.Dialogue.SimpleDialogueLines != null && 
            definition.Dialogue.SimpleDialogueLines.Count > 0)
        {
            npc.UseDialogueTree = false;
            npc.DialogueLines = definition.Dialogue.SimpleDialogueLines.ToArray();
        }
        else if (definition.Dialogue.Type == DialogueType.Complex && 
                 definition.Dialogue.ComplexDialogueTree != null)
        {
            npc.UseDialogueTree = true;
            npc.SetDialogueTree(definition.Dialogue.ComplexDialogueTree);
        }
        
        // Visual properties (if sprite exists)
        if (!string.IsNullOrEmpty(definition.Visual.SpriteSheetPath))
        {
            var spriteResource = GD.Load<SpriteFrames>(definition.Visual.SpriteSheetPath);
            if (spriteResource != null)
            {
                var animatedSprite = npc.GetNode<AnimatedSprite>("AnimatedSprite");
                if (animatedSprite != null)
                {
                    animatedSprite.Frames = spriteResource;
                    animatedSprite.Scale = Vector2.One * definition.Visual.Scale;
                    
                    if (!string.IsNullOrEmpty(definition.Visual.TintColor))
                    {
                        animatedSprite.Modulate = new Color(definition.Visual.TintColor);
                    }
                }
            }
        }
        
        // Movement properties
        npc.MovementPattern = definition.Movement.Pattern;
        npc.MoveSpeed = definition.Movement.MoveSpeed;
        npc.WaitTimeBetweenMoves = definition.Movement.WaitTimeBetweenMoves;
        
        // Store the full definition for later reference
        npc.Definition = definition;
        
        GD.Print($"Applied definition to NPC: {definition.Name}");
    }
}