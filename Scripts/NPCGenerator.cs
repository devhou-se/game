using Godot;
using System;
using System.Collections.Generic;
using DevHouse;

/// <summary>
/// Utility class for AI to generate NPCs from blog posts or other content
/// </summary>
public static class NPCGenerator
{
    /// <summary>
    /// Generate an NPC definition from a blog post
    /// </summary>
    public static NPCDefinition GenerateFromBlogPost(string title, string content, string url)
    {
        // This is where AI would analyze the blog post and generate appropriate NPC properties
        var def = new NPCDefinition();
        
        // Generate unique ID from title
        def.Id = title.ToLower().Replace(" ", "_").Replace("-", "_");
        def.Name = ExtractCharacterName(title, content);
        def.Description = $"An NPC created from the blog post: {title}";
        
        // AI would analyze content to determine personality
        def.Personality = "knowledgeable, helpful, enthusiastic about their topic";
        def.BackgroundStory = $"This character embodies the essence of the blog post '{title}'. They're passionate about sharing their knowledge and experiences.";
        
        // Visual (AI would determine appropriate sprite based on content)
        def.Visual.SpriteSheetPath = "res://Assets/16x16/default_npc_spritesheet.tres";
        def.Visual.Scale = 1.0f;
        def.Visual.TintColor = GenerateColorFromContent(content);
        
        // Behavior
        def.Behavior.EnableFullInteraction = true;
        def.Behavior.CaresAboutBaileyButlerOfficeStatus = false;
        def.Behavior.ReactsToTimeOfDay = true;
        def.Behavior.CustomFlags = ExtractTopicsAsFlags(content);
        
        // Dialogue (AI would generate contextual dialogue)
        def.Dialogue.Type = DialogueType.Simple;
        def.Dialogue.SimpleDialogueLines = GenerateDialogueFromContent(title, content);
        def.Dialogue.DefaultGreeting = $"Hello! Want to hear about {title}?";
        def.Dialogue.DefaultFarewell = "Thanks for listening!";
        def.Dialogue.TextDisplaySpeed = 0.05f;
        def.Dialogue.UseTypewriterEffect = true;
        
        // Movement
        def.Movement.Pattern = DetermineMovementPattern(content);
        def.Movement.MoveSpeed = 50.0f;
        def.Movement.WaitTimeBetweenMoves = 3.0f;
        
        // Audio
        def.Audio.VoiceId = $"voice_{def.Id}";
        def.Audio.VoicePitch = 1.0f + (float)(new Random().NextDouble() * 0.3 - 0.15); // Slight variation
        def.Audio.VoiceVolume = 1.0f;
        def.Audio.EnableVoiceSynthesis = true;
        
        // Game Data
        def.GameData.SpawnLocation = "center";
        def.GameData.SpawnWorld = "World";
        
        // Metadata
        def.Metadata.CreatedBy = "AI";
        def.Metadata.CreatedAt = DateTime.Now;
        def.Metadata.BlogPostUrl = url;
        def.Metadata.BlogPostTitle = title;
        def.Metadata.Tags = ExtractTopicsAsFlags(content);
        def.Metadata.Version = "1.0.0";
        
        return def;
    }
    
    /// <summary>
    /// Generate a complex dialogue tree from content
    /// </summary>
    public static DialogueTree GenerateDialogueTree(string topic, List<string> keyPoints, Dictionary<string, string> qaMap)
    {
        var tree = new DialogueTree();
        tree.StartNodeId = "start";
        
        // Create start node
        var startNode = new DialogueNode
        {
            Id = "start",
            Text = $"I'd love to talk about {topic}! What would you like to know?",
            Choices = new List<DialogueChoice>()
        };
        
        // Add choices for each key point
        int index = 0;
        foreach (var point in keyPoints)
        {
            startNode.Choices.Add(new DialogueChoice
            {
                Text = $"Tell me about {point}",
                NextNodeId = $"point_{index}"
            });
            
            // Create node for this point
            var pointNode = new DialogueNode
            {
                Id = $"point_{index}",
                Text = qaMap.ContainsKey(point) ? qaMap[point] : $"Let me explain {point}...",
                Choices = new List<DialogueChoice>
                {
                    new DialogueChoice { Text = "Tell me more", NextNodeId = $"detail_{index}" },
                    new DialogueChoice { Text = "What else can you tell me?", NextNodeId = "start" }
                }
            };
            
            tree.Nodes[$"point_{index}"] = pointNode;
            
            // Create detail node
            var detailNode = new DialogueNode
            {
                Id = $"detail_{index}",
                Text = $"Here's a deeper dive into {point}...",
                NextNodeId = "end",
                IsEndNode = false
            };
            
            tree.Nodes[$"detail_{index}"] = detailNode;
            index++;
        }
        
        // Add general options
        startNode.Choices.Add(new DialogueChoice
        {
            Text = "Just give me an overview",
            NextNodeId = "overview"
        });
        
        // Create overview node
        var overviewNode = new DialogueNode
        {
            Id = "overview",
            Text = $"Here's what you need to know about {topic}...",
            NextNodeId = "end"
        };
        
        // Create end node
        var endNode = new DialogueNode
        {
            Id = "end",
            Text = "I hope that was helpful! Feel free to ask me anything else.",
            IsEndNode = true
        };
        
        // Add all nodes to tree
        tree.Nodes["start"] = startNode;
        tree.Nodes["overview"] = overviewNode;
        tree.Nodes["end"] = endNode;
        
        return tree;
    }
    
    // Helper methods (these would be replaced by actual AI analysis)
    
    private static string ExtractCharacterName(string title, string content)
    {
        // AI would extract or generate an appropriate character name
        var words = title.Split(' ');
        if (words.Length > 0)
        {
            return words[0] + " Expert";
        }
        return "Knowledge Keeper";
    }
    
    private static string GenerateColorFromContent(string content)
    {
        // AI would analyze content mood/theme to pick a color
        var hash = content.GetHashCode();
        var hue = (hash % 360) / 360.0f;
        var color = Color.FromHsv(hue, 0.5f, 0.9f);
        return color.ToHtml();
    }
    
    private static List<string> ExtractTopicsAsFlags(string content)
    {
        // AI would extract key topics as flags
        return new List<string> { "knowledgeable", "blog_based", "interactive" };
    }
    
    private static List<string> GenerateDialogueFromContent(string title, string content)
    {
        // AI would generate contextual dialogue based on the blog post
        return new List<string>
        {
            $"Hi! I'm here to share insights from '{title}'",
            "I love discussing this topic with curious minds!",
            "There's so much to explore about this subject.",
            "What specific aspect interests you the most?",
            "I've learned so much from this experience.",
            "Let me share my favorite insight with you..."
        };
    }
    
    private static MovementPattern DetermineMovementPattern(string content)
    {
        // AI would analyze content to determine appropriate movement
        // Technical posts might be more static, adventure posts more dynamic
        if (content.Contains("adventure") || content.Contains("explore"))
        {
            return MovementPattern.Patrol;
        }
        else if (content.Contains("follow") || content.Contains("guide"))
        {
            return MovementPattern.Follow;
        }
        else if (content.Contains("research") || content.Contains("study"))
        {
            return MovementPattern.Static;
        }
        return MovementPattern.Random;
    }
    
    /// <summary>
    /// Example of how to create and save an NPC
    /// </summary>
    public static void CreateNPCFromBlogPost(string title, string content, string url)
    {
        // Generate the definition
        var definition = GenerateFromBlogPost(title, content, url);
        
        // Save to file
        var definitionsPath = "res://NPCDefinitions/";
        var filePath = definitionsPath + definition.Id + ".json";
        
        // Convert to dictionary manually for now
        var dict = new Godot.Collections.Dictionary();
        dict["Id"] = definition.Id;
        dict["Name"] = definition.Name;
        dict["Description"] = definition.Description;
        dict["Personality"] = definition.Personality;
        dict["BackgroundStory"] = definition.BackgroundStory;
        
        // Add visual data
        var visualDict = new Godot.Collections.Dictionary();
        visualDict["SpriteSheetPath"] = definition.Visual.SpriteSheetPath;
        visualDict["Scale"] = definition.Visual.Scale;
        visualDict["TintColor"] = definition.Visual.TintColor;
        dict["Visual"] = visualDict;
        
        // Add dialogue data
        var dialogueDict = new Godot.Collections.Dictionary();
        dialogueDict["Type"] = definition.Dialogue.Type.ToString();
        dialogueDict["SimpleDialogueLines"] = new Godot.Collections.Array(definition.Dialogue.SimpleDialogueLines);
        dialogueDict["DefaultGreeting"] = definition.Dialogue.DefaultGreeting;
        dialogueDict["DefaultFarewell"] = definition.Dialogue.DefaultFarewell;
        dialogueDict["TextDisplaySpeed"] = definition.Dialogue.TextDisplaySpeed;
        dialogueDict["UseTypewriterEffect"] = definition.Dialogue.UseTypewriterEffect;
        dict["Dialogue"] = dialogueDict;
        
        // Add other basic properties
        dict["MovementPattern"] = definition.Movement.Pattern.ToString();
        dict["MoveSpeed"] = definition.Movement.MoveSpeed;
        dict["WaitTimeBetweenMoves"] = definition.Movement.WaitTimeBetweenMoves;
        
        // Save JSON
        var json = new Godot.File();
        if (json.Open(filePath, Godot.File.ModeFlags.Write) == Error.Ok)
        {
            json.StoreString(JSON.Print(dict));
            json.Close();
            GD.Print($"Successfully created NPC: {definition.Name} from blog post: {title}");
            
            // Optionally spawn the NPC immediately
            NPCLocationManager.Instance.PlaceNPCFromDefinitionAtCoords(definition.Id, Vector2.Zero);
        }
        else
        {
            GD.PrintErr($"Failed to save NPC definition: {definition.Id}");
        }
    }
}