using Godot;
using System.Collections.Generic;
using System.Linq;
using DevHouse;

[Tool]
public class NPCDefinitionResource : Resource
{
    // Basic Information
    [Export] public string Id { get; set; } = "";
    [Export] public string Name { get; set; } = "";
    [Export] public string Description { get; set; } = "";
    [Export] public string Personality { get; set; } = "";
    [Export(PropertyHint.MultilineText)] public string BackgroundStory { get; set; } = "";
    
    // Dialogue
    [Export] public DialogueType DialogueType { get; set; } = DialogueType.Simple;
    [Export] public string[] SimpleDialogueLines { get; set; } = new string[0];
    
    // Behavior
    [Export] public bool EnableFullInteraction { get; set; } = true;
    [Export] public bool CaresAboutBaileyButlerOfficeStatus { get; set; } = false;
    
    // Movement
    [Export] public MovementPattern MovementPattern { get; set; } = MovementPattern.Static;
    [Export] public float WaitTimeBetweenMoves { get; set; } = 3f;
    
    // Visual Properties
    [Export] public string SpriteTexturePath { get; set; } = "";
    [Export] public string AnimationSet { get; set; } = "default";
    [Export] public Color BaseColor { get; set; } = Colors.White;
    [Export] public Color HairColor { get; set; } = new Color(0.5f, 0.3f, 0.1f);
    [Export] public Color SkinColor { get; set; } = new Color(1.0f, 0.85f, 0.7f);
    [Export] public Color ShirtColor { get; set; } = new Color(0.2f, 0.4f, 0.8f);
    [Export] public Color PantsColor { get; set; } = new Color(0.3f, 0.3f, 0.3f);
    
    // Audio
    [Export] public bool UseVoiceSynthesis { get; set; } = false;
    [Export] public string VoiceId { get; set; } = "";
    [Export] public float VoicePitch { get; set; } = 1.0f;
    [Export] public float VoiceSpeed { get; set; } = 1.0f;
    
    // Game Integration
    [Export] public string SpawnWorld { get; set; } = "";
    [Export] public string SpawnLocation { get; set; } = "";
    [Export] public string[] Tags { get; set; } = new string[0];
    
    // Convert to NPCDefinition for compatibility
    public NPCDefinition ToNPCDefinition()
    {
        var def = new NPCDefinition
        {
            Id = Id,
            Name = Name,
            Description = Description,
            Personality = Personality,
            BackgroundStory = BackgroundStory
        };
        
        // Dialogue
        def.Dialogue.Type = DialogueType;
        if (SimpleDialogueLines != null && SimpleDialogueLines.Length > 0)
        {
            def.Dialogue.SimpleDialogueLines = new List<string>(SimpleDialogueLines);
        }
        
        // Behavior
        def.Behavior.EnableFullInteraction = EnableFullInteraction;
        def.Behavior.CaresAboutBaileyButlerOfficeStatus = CaresAboutBaileyButlerOfficeStatus;
        
        // Movement
        def.Movement.Pattern = MovementPattern;
        def.Movement.WaitTimeBetweenMoves = WaitTimeBetweenMoves;
        
        // Visual
        def.Visual.SpriteSheetPath = SpriteTexturePath;
        def.Visual.TintColor = "#" + BaseColor.ToHtml(false);
        // Store animation set and color properties in custom properties if needed
        if (!string.IsNullOrEmpty(AnimationSet))
        {
            def.Visual.AnimationOverrides["set"] = AnimationSet;
        }
        
        // Audio
        def.Audio.EnableVoiceSynthesis = UseVoiceSynthesis;
        def.Audio.VoiceId = VoiceId;
        def.Audio.VoicePitch = VoicePitch;
        def.Audio.VoiceVolume = VoiceSpeed; // Map speed to volume for now
        
        // Game Integration
        def.GameData.SpawnWorld = SpawnWorld;
        def.GameData.SpawnLocation = SpawnLocation;
        // Store tags in metadata instead
        if (Tags != null && Tags.Length > 0)
        {
            def.Metadata.Tags = new List<string>(Tags);
        }
        
        return def;
    }
}