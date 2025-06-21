using Godot;
using System;
using System.Collections.Generic;
using DevHouse;

namespace DevHouse
{
    /// <summary>
    /// Comprehensive NPC definition structure for AI-generated NPCs
    /// </summary>
    [Serializable]
    public class NPCDefinition
    {
        // Basic Information
        public string Id { get; set; }
        public string Name { get; set; }
        public string Description { get; set; }
        public string Personality { get; set; }
        public string BackgroundStory { get; set; }
        
        // Visual Properties
        public NPCVisualData Visual { get; set; }
        
        // Behavioral Properties
        public NPCBehaviorData Behavior { get; set; }
        
        // Dialogue System
        public NPCDialogueData Dialogue { get; set; }
        
        // Movement Patterns
        public NPCMovementData Movement { get; set; }
        
        // Audio Properties
        public NPCAudioData Audio { get; set; }
        
        // Game Integration
        public NPCGameData GameData { get; set; }
        
        // Metadata
        public NPCMetadata Metadata { get; set; }
        
        public NPCDefinition()
        {
            Visual = new NPCVisualData();
            Behavior = new NPCBehaviorData();
            Dialogue = new NPCDialogueData();
            Movement = new NPCMovementData();
            Audio = new NPCAudioData();
            GameData = new NPCGameData();
            Metadata = new NPCMetadata();
        }
    }
    
    [Serializable]
    public class NPCVisualData
    {
        public string SpriteSheetPath { get; set; }
        public string PortraitPath { get; set; }
        public float Scale { get; set; } = 1.0f;
        public string TintColor { get; set; } = "#FFFFFF";
        public Dictionary<string, string> AnimationOverrides { get; set; }
        public bool UseCustomShader { get; set; }
        public string CustomShaderPath { get; set; }
        
        public NPCVisualData()
        {
            AnimationOverrides = new Dictionary<string, string>();
        }
    }
    
    [Serializable]
    public class NPCBehaviorData
    {
        public bool EnableFullInteraction { get; set; } = true;
        public bool CaresAboutBaileyButlerOfficeStatus { get; set; }
        public float InteractionRadius { get; set; } = 32.0f;
        public bool CanBePickedUp { get; set; }
        public bool ReactsToWeather { get; set; }
        public bool ReactsToTimeOfDay { get; set; }
        public List<string> CustomFlags { get; set; }
        public Dictionary<string, object> CustomProperties { get; set; }
        
        public NPCBehaviorData()
        {
            CustomFlags = new List<string>();
            CustomProperties = new Dictionary<string, object>();
        }
    }
    
    [Serializable]
    public class NPCDialogueData
    {
        public DialogueType Type { get; set; } = DialogueType.Simple;
        public List<string> SimpleDialogueLines { get; set; }
        public DialogueTree ComplexDialogueTree { get; set; }
        public Dictionary<string, List<string>> ConditionalDialogue { get; set; }
        public Dictionary<string, string> CollisionResponses { get; set; }
        public string DefaultGreeting { get; set; }
        public string DefaultFarewell { get; set; }
        public float TextDisplaySpeed { get; set; } = 0.05f;
        public bool UseTypewriterEffect { get; set; } = true;
        
        public NPCDialogueData()
        {
            SimpleDialogueLines = new List<string>();
            ConditionalDialogue = new Dictionary<string, List<string>>();
            CollisionResponses = new Dictionary<string, string>();
        }
    }
    
    public enum DialogueType
    {
        Simple,
        Complex,
        Dynamic
    }
    
    [Serializable]
    public class NPCMovementData
    {
        public MovementPattern Pattern { get; set; } = MovementPattern.Random;
        public float MoveSpeed { get; set; } = 50.0f;
        public float WaitTimeBetweenMoves { get; set; } = 3.0f;
        public List<Vector2> PatrolPoints { get; set; }
        public bool CanChasePlayer { get; set; }
        public float ChaseSpeed { get; set; } = 100.0f;
        public float ChaseRadius { get; set; } = 150.0f;
        public bool AvoidObstacles { get; set; } = true;
        public Dictionary<string, float> MovementModifiers { get; set; }
        
        public NPCMovementData()
        {
            PatrolPoints = new List<Vector2>();
            MovementModifiers = new Dictionary<string, float>();
        }
    }
    
    public enum MovementPattern
    {
        Static,
        Random,
        Patrol,
        Follow,
        Flee,
        Custom
    }
    
    [Serializable]
    public class NPCAudioData
    {
        public string VoiceId { get; set; } // ElevenLabs voice ID
        public float VoicePitch { get; set; } = 1.0f;
        public float VoiceVolume { get; set; } = 1.0f;
        public Dictionary<string, string> SoundEffects { get; set; }
        public string FootstepSound { get; set; }
        public string InteractionSound { get; set; }
        public bool EnableVoiceSynthesis { get; set; } = true;
        
        public NPCAudioData()
        {
            SoundEffects = new Dictionary<string, string>();
        }
    }
    
    [Serializable]
    public class NPCGameData
    {
        public string SpawnLocation { get; set; }
        public string SpawnWorld { get; set; } = "World";
        public List<string> RequiredItems { get; set; }
        public List<string> GivesItems { get; set; }
        public Dictionary<string, int> Stats { get; set; }
        public List<string> QuestIds { get; set; }
        public bool IsMerchant { get; set; }
        public List<NPCShopItem> ShopInventory { get; set; }
        
        public NPCGameData()
        {
            RequiredItems = new List<string>();
            GivesItems = new List<string>();
            Stats = new Dictionary<string, int>();
            QuestIds = new List<string>();
            ShopInventory = new List<NPCShopItem>();
        }
    }
    
    [Serializable]
    public class NPCShopItem
    {
        public string ItemId { get; set; }
        public int Price { get; set; }
        public int Quantity { get; set; } = -1; // -1 for unlimited
        public string RequiredFlag { get; set; }
    }
    
    [Serializable]
    public class NPCMetadata
    {
        public string CreatedBy { get; set; } = "AI";
        public DateTime CreatedAt { get; set; } = DateTime.Now;
        public string BlogPostUrl { get; set; }
        public string BlogPostTitle { get; set; }
        public List<string> Tags { get; set; }
        public string Version { get; set; } = "1.0.0";
        public Dictionary<string, string> AdditionalData { get; set; }
        
        public NPCMetadata()
        {
            Tags = new List<string>();
            AdditionalData = new Dictionary<string, string>();
        }
    }
}