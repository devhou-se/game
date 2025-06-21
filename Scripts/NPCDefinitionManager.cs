using Godot;
using System;
using System.Collections.Generic;
using DevHouse;

public class NPCDefinitionManager : Node
{
    private static NPCDefinitionManager _instance;
    private static readonly object _lock = new object();
    
    public static NPCDefinitionManager Instance
    {
        get
        {
            if (_instance == null)
            {
                lock (_lock)
                {
                    if (_instance == null)
                    {
                        // Create instance but don't add to scene tree here
                        _instance = new NPCDefinitionManager();
                        _instance.Name = "NPCDefinitionManager";
                        
                        // Try to add to scene tree if possible
                        var tree = Engine.GetMainLoop() as SceneTree;
                        if (tree?.Root != null && !_instance.IsInsideTree())
                        {
                            tree.Root.CallDeferred("add_child", _instance);
                        }
                    }
                }
            }
            return _instance;
        }
    }
    
    private Dictionary<string, NPCDefinition> _loadedDefinitions;
    private const string DEFINITIONS_PATH = "res://NPCDefinitions/";
    private bool _isInitialized = false;
    
    public NPCDefinitionManager()
    {
        _loadedDefinitions = new Dictionary<string, NPCDefinition>();
    }
    
    public override void _Ready()
    {
        // Set as singleton if we're the first
        if (_instance == null)
        {
            _instance = this;
        }
        else if (_instance != this)
        {
            QueueFree();
            return;
        }
        
        CallDeferred("LoadAllDefinitions");
    }
    
    /// <summary>
    /// Load all NPC definitions from the definitions directory
    /// </summary>
    public void LoadAllDefinitions()
    {
        if (_isInitialized) return;
        _isInitialized = true;
        var dir = new Godot.Directory();
        if (!dir.DirExists(DEFINITIONS_PATH))
        {
            GD.Print($"Creating NPC definitions directory at {DEFINITIONS_PATH}");
            dir.MakeDirRecursive(DEFINITIONS_PATH);
            return;
        }
        
        if (dir.Open(DEFINITIONS_PATH) == Error.Ok)
        {
            dir.ListDirBegin();
            var fileName = dir.GetNext();
            
            while (!string.IsNullOrEmpty(fileName))
            {
                if (fileName.EndsWith(".json") && !fileName.StartsWith("ai_template"))
                {
                    LoadDefinition(DEFINITIONS_PATH + fileName);
                }
                fileName = dir.GetNext();
            }
            
            dir.ListDirEnd();
        }
        
        GD.Print($"Loaded {_loadedDefinitions.Count} NPC definitions");
    }
    
    /// <summary>
    /// Load a single NPC definition from a JSON file
    /// </summary>
    public NPCDefinition LoadDefinition(string filePath)
    {
        try
        {
            var file = new Godot.File();
            if (file.Open(filePath, Godot.File.ModeFlags.Read) != Error.Ok)
            {
                GD.PrintErr($"Failed to open NPC definition file: {filePath}");
                return null;
            }
            
            var jsonContent = file.GetAsText();
            file.Close();
            
            var json = JSON.Parse(jsonContent);
            if (json.Error != Error.Ok)
            {
                GD.PrintErr($"Failed to parse JSON from {filePath}: {json.ErrorString}");
                return null;
            }
            
            var definition = DeserializeNPCDefinition(json.Result as Godot.Collections.Dictionary);
            if (definition != null && !string.IsNullOrEmpty(definition.Id))
            {
                _loadedDefinitions[definition.Id] = definition;
                GD.Print($"Loaded NPC definition: {definition.Name} (ID: {definition.Id})");
                return definition;
            }
        }
        catch (Exception e)
        {
            GD.PrintErr($"Error loading NPC definition from {filePath}: {e.Message}");
        }
        
        return null;
    }
    
    /// <summary>
    /// Save an NPC definition to a JSON file
    /// </summary>
    public bool SaveDefinition(NPCDefinition definition)
    {
        if (definition == null || string.IsNullOrEmpty(definition.Id))
        {
            GD.PrintErr("Cannot save NPC definition: Invalid definition or missing ID");
            return false;
        }
        
        try
        {
            var filePath = $"{DEFINITIONS_PATH}{definition.Id}.json";
            var dict = SerializeNPCDefinition(definition);
            var jsonContent = JSON.Print(dict, "  ");
            
            var file = new Godot.File();
            if (file.Open(filePath, Godot.File.ModeFlags.Write) != Error.Ok)
            {
                GD.PrintErr($"Failed to create NPC definition file: {filePath}");
                return false;
            }
            
            file.StoreString(jsonContent);
            file.Close();
            
            _loadedDefinitions[definition.Id] = definition;
            GD.Print($"Saved NPC definition: {definition.Name} to {filePath}");
            return true;
        }
        catch (Exception e)
        {
            GD.PrintErr($"Error saving NPC definition: {e.Message}");
            return false;
        }
    }
    
    /// <summary>
    /// Get an NPC definition by ID
    /// </summary>
    public NPCDefinition GetDefinition(string npcId)
    {
        if (!_isInitialized)
        {
            GD.PrintErr($"NPCDefinitionManager not initialized when requesting definition: {npcId}");
            return null;
        }
        
        if (_loadedDefinitions == null || !_loadedDefinitions.ContainsKey(npcId))
        {
            return null;
        }
        
        return _loadedDefinitions[npcId];
    }
    
    /// <summary>
    /// Get all loaded NPC definitions
    /// </summary>
    public Dictionary<string, NPCDefinition> GetAllDefinitions()
    {
        return new Dictionary<string, NPCDefinition>(_loadedDefinitions);
    }
    
    /// <summary>
    /// Create an NPC instance from a definition
    /// </summary>
    public NPC CreateNPCFromDefinition(string npcId)
    {
        var definition = GetDefinition(npcId);
        if (definition == null)
        {
            GD.PrintErr($"NPC definition not found: {npcId}");
            return null;
        }
        
        return CreateNPCFromDefinition(definition);
    }
    
    /// <summary>
    /// Create an NPC instance from a definition object
    /// </summary>
    public NPC CreateNPCFromDefinition(NPCDefinition definition)
    {
        var npcScene = GD.Load<PackedScene>("res://Scenes/NPC.tscn");
        if (npcScene == null)
        {
            GD.PrintErr("Failed to load NPC scene");
            return null;
        }
        
        var npc = npcScene.Instance() as NPC;
        if (npc == null)
        {
            GD.PrintErr("Failed to instantiate NPC");
            return null;
        }
        
        // Apply definition to NPC
        ApplyDefinitionToNPC(npc, definition);
        
        return npc;
    }
    
    /// <summary>
    /// Apply a definition to an existing NPC instance
    /// </summary>
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
    
    /// <summary>
    /// Generate a definition from an existing NPC (for migration)
    /// </summary>
    public NPCDefinition GenerateDefinitionFromNPC(NPC npc)
    {
        if (npc == null) return null;
        
        var definition = new NPCDefinition
        {
            Id = npc.NPCName.ToLower().Replace(" ", "_"),
            Name = npc.NPCName,
            Description = $"Auto-generated definition for {npc.NPCName}"
        };
        
        // Behavior
        definition.Behavior.EnableFullInteraction = npc.EnableFullInteraction;
        definition.Behavior.CaresAboutBaileyButlerOfficeStatus = npc.CaresAboutBaileyButlerBeingInTheOffice;
        
        // Dialogue
        if (!npc.UseDialogueTree && npc.DialogueLines != null)
        {
            definition.Dialogue.Type = DialogueType.Simple;
            definition.Dialogue.SimpleDialogueLines = new List<string>(npc.DialogueLines);
        }
        else if (npc.UseDialogueTree && npc.GetDialogueTree() != null)
        {
            definition.Dialogue.Type = DialogueType.Complex;
            definition.Dialogue.ComplexDialogueTree = npc.GetDialogueTree();
        }
        
        // Movement (from current NPC state)
        definition.Movement.Pattern = npc.MovementPattern;
        definition.Movement.MoveSpeed = npc.MoveSpeed;
        definition.Movement.WaitTimeBetweenMoves = npc.WaitTimeBetweenMoves;
        
        // Visual (try to extract current sprite info)
        var animatedSprite = npc.GetNode<AnimatedSprite>("AnimatedSprite2D");
        if (animatedSprite != null && animatedSprite.Frames != null)
        {
            definition.Visual.Scale = animatedSprite.Scale.x;
            definition.Visual.TintColor = animatedSprite.Modulate.ToHtml();
        }
        
        // Metadata
        definition.Metadata.CreatedBy = "Migration";
        definition.Metadata.CreatedAt = DateTime.Now;
        
        return definition;
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
    
    private Godot.Collections.Dictionary SerializeNPCDefinition(NPCDefinition def)
    {
        var dict = new Godot.Collections.Dictionary();
        
        // Basic Information
        dict["Id"] = def.Id ?? "";
        dict["Name"] = def.Name ?? "";
        dict["Description"] = def.Description ?? "";
        dict["Personality"] = def.Personality ?? "";
        dict["BackgroundStory"] = def.BackgroundStory ?? "";
        
        // Visual Properties
        var visual = new Godot.Collections.Dictionary();
        visual["SpriteSheetPath"] = def.Visual.SpriteSheetPath ?? "";
        visual["PortraitPath"] = def.Visual.PortraitPath ?? "";
        visual["Scale"] = def.Visual.Scale;
        visual["TintColor"] = def.Visual.TintColor ?? "#FFFFFF";
        visual["UseCustomShader"] = def.Visual.UseCustomShader;
        visual["CustomShaderPath"] = def.Visual.CustomShaderPath ?? "";
        dict["Visual"] = visual;
        
        // Behavior Properties
        var behavior = new Godot.Collections.Dictionary();
        behavior["EnableFullInteraction"] = def.Behavior.EnableFullInteraction;
        behavior["CaresAboutBaileyButlerOfficeStatus"] = def.Behavior.CaresAboutBaileyButlerOfficeStatus;
        behavior["InteractionRadius"] = def.Behavior.InteractionRadius;
        behavior["CanBePickedUp"] = def.Behavior.CanBePickedUp;
        behavior["ReactsToWeather"] = def.Behavior.ReactsToWeather;
        behavior["ReactsToTimeOfDay"] = def.Behavior.ReactsToTimeOfDay;
        
        var customFlags = new Godot.Collections.Array();
        foreach (var flag in def.Behavior.CustomFlags)
        {
            customFlags.Add(flag);
        }
        behavior["CustomFlags"] = customFlags;
        dict["Behavior"] = behavior;
        
        // Dialogue Properties
        var dialogue = new Godot.Collections.Dictionary();
        dialogue["Type"] = def.Dialogue.Type.ToString();
        
        var dialogueLines = new Godot.Collections.Array();
        foreach (var line in def.Dialogue.SimpleDialogueLines)
        {
            dialogueLines.Add(line);
        }
        dialogue["SimpleDialogueLines"] = dialogueLines;
        
        if (def.Dialogue.ComplexDialogueTree != null)
        {
            dialogue["ComplexDialogueTree"] = SerializeDialogueTree(def.Dialogue.ComplexDialogueTree);
        }
        
        dialogue["DefaultGreeting"] = def.Dialogue.DefaultGreeting ?? "";
        dialogue["DefaultFarewell"] = def.Dialogue.DefaultFarewell ?? "";
        dialogue["TextDisplaySpeed"] = def.Dialogue.TextDisplaySpeed;
        dialogue["UseTypewriterEffect"] = def.Dialogue.UseTypewriterEffect;
        dict["Dialogue"] = dialogue;
        
        // Movement Properties
        var movement = new Godot.Collections.Dictionary();
        movement["Pattern"] = def.Movement.Pattern.ToString();
        movement["MoveSpeed"] = def.Movement.MoveSpeed;
        movement["WaitTimeBetweenMoves"] = def.Movement.WaitTimeBetweenMoves;
        
        var patrolPoints = new Godot.Collections.Array();
        foreach (var point in def.Movement.PatrolPoints)
        {
            var pointDict = new Godot.Collections.Dictionary();
            pointDict["x"] = point.x;
            pointDict["y"] = point.y;
            patrolPoints.Add(pointDict);
        }
        movement["PatrolPoints"] = patrolPoints;
        movement["CanChasePlayer"] = def.Movement.CanChasePlayer;
        movement["ChaseSpeed"] = def.Movement.ChaseSpeed;
        movement["ChaseRadius"] = def.Movement.ChaseRadius;
        movement["AvoidObstacles"] = def.Movement.AvoidObstacles;
        dict["Movement"] = movement;
        
        // Audio Properties
        var audio = new Godot.Collections.Dictionary();
        audio["VoiceId"] = def.Audio.VoiceId ?? "";
        audio["VoicePitch"] = def.Audio.VoicePitch;
        audio["VoiceVolume"] = def.Audio.VoiceVolume;
        audio["FootstepSound"] = def.Audio.FootstepSound ?? "";
        audio["InteractionSound"] = def.Audio.InteractionSound ?? "";
        audio["EnableVoiceSynthesis"] = def.Audio.EnableVoiceSynthesis;
        dict["Audio"] = audio;
        
        // Game Data
        var gameData = new Godot.Collections.Dictionary();
        gameData["SpawnLocation"] = def.GameData.SpawnLocation ?? "";
        gameData["SpawnWorld"] = def.GameData.SpawnWorld ?? "World";
        
        var requiredItems = new Godot.Collections.Array();
        foreach (var item in def.GameData.RequiredItems)
        {
            requiredItems.Add(item);
        }
        gameData["RequiredItems"] = requiredItems;
        
        var givesItems = new Godot.Collections.Array();
        foreach (var item in def.GameData.GivesItems)
        {
            givesItems.Add(item);
        }
        gameData["GivesItems"] = givesItems;
        
        var questIds = new Godot.Collections.Array();
        foreach (var quest in def.GameData.QuestIds)
        {
            questIds.Add(quest);
        }
        gameData["QuestIds"] = questIds;
        
        gameData["IsMerchant"] = def.GameData.IsMerchant;
        dict["GameData"] = gameData;
        
        // Metadata
        var metadata = new Godot.Collections.Dictionary();
        metadata["CreatedBy"] = def.Metadata.CreatedBy ?? "AI";
        metadata["CreatedAt"] = def.Metadata.CreatedAt.ToString("yyyy-MM-ddTHH:mm:ssZ");
        metadata["BlogPostUrl"] = def.Metadata.BlogPostUrl ?? "";
        metadata["BlogPostTitle"] = def.Metadata.BlogPostTitle ?? "";
        metadata["Version"] = def.Metadata.Version ?? "1.0.0";
        
        var tags = new Godot.Collections.Array();
        foreach (var tag in def.Metadata.Tags)
        {
            tags.Add(tag);
        }
        metadata["Tags"] = tags;
        dict["Metadata"] = metadata;
        
        return dict;
    }
    
    private Godot.Collections.Dictionary SerializeDialogueTree(DialogueTree tree)
    {
        var dict = new Godot.Collections.Dictionary();
        dict["StartNodeId"] = tree.StartNodeId ?? "";
        
        var nodes = new Godot.Collections.Dictionary();
        foreach (var kvp in tree.Nodes)
        {
            var nodeDict = new Godot.Collections.Dictionary();
            nodeDict["Id"] = kvp.Value.Id ?? "";
            nodeDict["Text"] = kvp.Value.Text ?? "";
            nodeDict["NextNodeId"] = kvp.Value.NextNodeId ?? "";
            nodeDict["IsEndNode"] = kvp.Value.IsEndNode;
            
            var choices = new Godot.Collections.Array();
            foreach (var choice in kvp.Value.Choices)
            {
                var choiceDict = new Godot.Collections.Dictionary();
                choiceDict["Text"] = choice.Text ?? "";
                choiceDict["NextNodeId"] = choice.NextNodeId ?? "";
                choiceDict["RequiredFlag"] = choice.RequiredFlag ?? "";
                choiceDict["SetFlag"] = choice.SetFlag ?? "";
                choices.Add(choiceDict);
            }
            nodeDict["Choices"] = choices;
            
            nodes[kvp.Key] = nodeDict;
        }
        dict["Nodes"] = nodes;
        
        return dict;
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
            
            if (behavior.Contains("CustomFlags") && behavior["CustomFlags"] is Godot.Collections.Array flags)
            {
                def.Behavior.CustomFlags.Clear();
                foreach (var flag in flags)
                {
                    def.Behavior.CustomFlags.Add(flag.ToString());
                }
            }
        }
        
        // Dialogue Properties
        if (dict.Contains("Dialogue") && dict["Dialogue"] is Godot.Collections.Dictionary dialogue)
        {
            var typeStr = GetDictValue(dialogue, "Type", "Simple");
            DialogueType dialogueType;
            if (Enum.TryParse<DialogueType>(typeStr, out dialogueType))
            {
                def.Dialogue.Type = dialogueType;
            }
            
            if (dialogue.Contains("SimpleDialogueLines") && dialogue["SimpleDialogueLines"] is Godot.Collections.Array lines)
            {
                def.Dialogue.SimpleDialogueLines.Clear();
                foreach (var line in lines)
                {
                    def.Dialogue.SimpleDialogueLines.Add(line.ToString());
                }
            }
            
            if (dialogue.Contains("ComplexDialogueTree") && dialogue["ComplexDialogueTree"] is Godot.Collections.Dictionary treeDict)
            {
                def.Dialogue.ComplexDialogueTree = DeserializeDialogueTree(treeDict);
            }
            
            def.Dialogue.DefaultGreeting = GetDictValue(dialogue, "DefaultGreeting", "");
            def.Dialogue.DefaultFarewell = GetDictValue(dialogue, "DefaultFarewell", "");
            def.Dialogue.TextDisplaySpeed = GetDictValue(dialogue, "TextDisplaySpeed", 0.05f);
            def.Dialogue.UseTypewriterEffect = GetDictValue(dialogue, "UseTypewriterEffect", true);
        }
        
        // Movement Properties
        if (dict.Contains("Movement") && dict["Movement"] is Godot.Collections.Dictionary movement)
        {
            var patternStr = GetDictValue(movement, "Pattern", "Random");
            MovementPattern movementPattern;
            if (Enum.TryParse<MovementPattern>(patternStr, out movementPattern))
            {
                def.Movement.Pattern = movementPattern;
            }
            
            def.Movement.MoveSpeed = GetDictValue(movement, "MoveSpeed", 50.0f);
            def.Movement.WaitTimeBetweenMoves = GetDictValue(movement, "WaitTimeBetweenMoves", 3.0f);
            def.Movement.CanChasePlayer = GetDictValue(movement, "CanChasePlayer", false);
            def.Movement.ChaseSpeed = GetDictValue(movement, "ChaseSpeed", 100.0f);
            def.Movement.ChaseRadius = GetDictValue(movement, "ChaseRadius", 150.0f);
            def.Movement.AvoidObstacles = GetDictValue(movement, "AvoidObstacles", true);
            
            if (movement.Contains("PatrolPoints") && movement["PatrolPoints"] is Godot.Collections.Array points)
            {
                def.Movement.PatrolPoints.Clear();
                foreach (var point in points)
                {
                    if (point is Godot.Collections.Dictionary pointDict)
                    {
                        var x = GetDictValue(pointDict, "x", 0f);
                        var y = GetDictValue(pointDict, "y", 0f);
                        def.Movement.PatrolPoints.Add(new Vector2(x, y));
                    }
                }
            }
        }
        
        // Audio Properties
        if (dict.Contains("Audio") && dict["Audio"] is Godot.Collections.Dictionary audio)
        {
            def.Audio.VoiceId = GetDictValue(audio, "VoiceId", "");
            def.Audio.VoicePitch = GetDictValue(audio, "VoicePitch", 1.0f);
            def.Audio.VoiceVolume = GetDictValue(audio, "VoiceVolume", 1.0f);
            def.Audio.FootstepSound = GetDictValue(audio, "FootstepSound", "");
            def.Audio.InteractionSound = GetDictValue(audio, "InteractionSound", "");
            def.Audio.EnableVoiceSynthesis = GetDictValue(audio, "EnableVoiceSynthesis", true);
        }
        
        // Game Data
        if (dict.Contains("GameData") && dict["GameData"] is Godot.Collections.Dictionary gameData)
        {
            def.GameData.SpawnLocation = GetDictValue(gameData, "SpawnLocation", "");
            def.GameData.SpawnWorld = GetDictValue(gameData, "SpawnWorld", "World");
            def.GameData.IsMerchant = GetDictValue(gameData, "IsMerchant", false);
            
            if (gameData.Contains("RequiredItems") && gameData["RequiredItems"] is Godot.Collections.Array items)
            {
                def.GameData.RequiredItems.Clear();
                foreach (var item in items)
                {
                    def.GameData.RequiredItems.Add(item.ToString());
                }
            }
            
            if (gameData.Contains("GivesItems") && gameData["GivesItems"] is Godot.Collections.Array giveItems)
            {
                def.GameData.GivesItems.Clear();
                foreach (var item in giveItems)
                {
                    def.GameData.GivesItems.Add(item.ToString());
                }
            }
            
            if (gameData.Contains("QuestIds") && gameData["QuestIds"] is Godot.Collections.Array quests)
            {
                def.GameData.QuestIds.Clear();
                foreach (var quest in quests)
                {
                    def.GameData.QuestIds.Add(quest.ToString());
                }
            }
        }
        
        // Metadata
        if (dict.Contains("Metadata") && dict["Metadata"] is Godot.Collections.Dictionary metadata)
        {
            def.Metadata.CreatedBy = GetDictValue(metadata, "CreatedBy", "AI");
            def.Metadata.BlogPostUrl = GetDictValue(metadata, "BlogPostUrl", "");
            def.Metadata.BlogPostTitle = GetDictValue(metadata, "BlogPostTitle", "");
            def.Metadata.Version = GetDictValue(metadata, "Version", "1.0.0");
            
            if (metadata.Contains("CreatedAt"))
            {
                if (DateTime.TryParse(metadata["CreatedAt"].ToString(), out var createdAt))
                {
                    def.Metadata.CreatedAt = createdAt;
                }
            }
            
            if (metadata.Contains("Tags") && metadata["Tags"] is Godot.Collections.Array tags)
            {
                def.Metadata.Tags.Clear();
                foreach (var tag in tags)
                {
                    def.Metadata.Tags.Add(tag.ToString());
                }
            }
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
}