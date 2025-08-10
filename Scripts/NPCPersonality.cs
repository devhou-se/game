using System;
using System.Collections.Generic;

/// <summary>
/// Represents the personality and characteristics of an NPC generated from blog post content.
/// This class is designed to be populated by an LLM based on blog post analysis.
/// </summary>
[Serializable]
public class NPCPersonality
{
	/// <summary>
	/// URL of the source blog post used to generate this NPC's personality
	/// </summary>
	public string BlogPostUrl { get; set; }
	
	/// <summary>
	/// Title of the blog post that inspired this NPC
	/// </summary>
	public string BlogPostTitle { get; set; }
	
	/// <summary>
	/// Publication date of the source blog post
	/// </summary>
	public DateTime BlogPostDate { get; set; }
	
	/// <summary>
	/// Author name from the blog post, may influence NPC's knowledge or perspective
	/// </summary>
	public string AuthorName { get; set; }
	
	/// <summary>
	/// Personality archetype (e.g., "INTJ", "The Mentor", "Cheerful Optimist")
	/// </summary>
	public string PersonalityType { get; set; }
	
	/// <summary>
	/// Big Five personality trait scores (0.0-1.0 scale)
	/// Keys: openness, conscientiousness, extraversion, agreeableness, neuroticism
	/// </summary>
	public Dictionary<string, float> TraitScores { get; set; } = new Dictionary<string, float>
	{
		{"openness", 0.5f},
		{"conscientiousness", 0.5f},
		{"extraversion", 0.5f},
		{"agreeableness", 0.5f},
		{"neuroticism", 0.5f}
	};
	
	/// <summary>
	/// NPC's backstory derived from blog post themes and content
	/// </summary>
	public string BackgroundStory { get; set; }
	
	/// <summary>
	/// NPC's profession or role, often related to blog post subject matter
	/// </summary>
	public string Occupation { get; set; }
	
	/// <summary>
	/// List of topics the NPC is interested in, extracted from blog content
	/// </summary>
	public List<string> Interests { get; set; } = new List<string>();
	
	/// <summary>
	/// Activities the NPC enjoys, can be mentioned in dialogue
	/// </summary>
	public List<string> Hobbies { get; set; } = new List<string>();
	
	/// <summary>
	/// Description of how the NPC speaks (e.g., "formal", "uses technical jargon", "speaks in questions")
	/// </summary>
	public string SpeechPattern { get; set; }
	
	/// <summary>
	/// Voice description for text-to-speech synthesis (e.g., "warm and friendly", "gruff", "melodic")
	/// </summary>
	public string VoiceCharacteristics { get; set; }
	
	/// <summary>
	/// Predefined responses for different emotional states
	/// Keys: happy, sad, angry, surprised, fearful, neutral
	/// </summary>
	public Dictionary<string, string> EmotionalResponses { get; set; } = new Dictionary<string, string>
	{
		{"happy", ""},
		{"sad", ""},
		{"angry", ""},
		{"surprised", ""},
		{"fearful", ""},
		{"neutral", ""}
	};
	
	/// <summary>
	/// Signature phrases or expressions the NPC frequently uses
	/// </summary>
	public List<string> CatchPhrases { get; set; } = new List<string>();
	
	/// <summary>
	/// Topics the NPC likes to discuss, derived from blog post themes
	/// </summary>
	public List<string> ConversationTopics { get; set; } = new List<string>();
	
	/// <summary>
	/// What drives this NPC, their primary motivation in life
	/// </summary>
	public string Motivation { get; set; }
	
	/// <summary>
	/// What the NPC is afraid of or tries to avoid
	/// </summary>
	public string Fear { get; set; }
	
	/// <summary>
	/// The NPC's primary objective or life goal
	/// </summary>
	public string Goal { get; set; }
	
	/// <summary>
	/// How the NPC relates to specific topics from the blog post
	/// Key: topic name, Value: relationship description
	/// </summary>
	public Dictionary<string, string> RelationshipToTopics { get; set; } = new Dictionary<string, string>();
	
	/// <summary>
	/// Default emotional state when not influenced by events (e.g., "neutral", "cheerful", "melancholic")
	/// </summary>
	public string MoodBaseline { get; set; } = "neutral";
	
	/// <summary>
	/// How energetic or active the NPC is (0.0 = lethargic, 1.0 = hyperactive)
	/// </summary>
	public float EnergyLevel { get; set; } = 0.5f;
	
	/// <summary>
	/// How much the NPC tends to talk (0.0 = silent, 1.0 = extremely chatty)
	/// </summary>
	public float Talkativeness { get; set; } = 0.5f;
	
	/// <summary>
	/// NPC's sense of humor level (0.0 = serious, 1.0 = comedian)
	/// </summary>
	public float Humor { get; set; } = 0.5f;
	
	/// <summary>
	/// How formal vs casual the NPC's speech is (0.0 = very casual, 1.0 = extremely formal)
	/// </summary>
	public float Formality { get; set; } = 0.5f;
	
	/// <summary>
	/// Areas of expertise the NPC can speak knowledgeably about
	/// </summary>
	public List<string> KnowledgeDomains { get; set; } = new List<string>();
	
	/// <summary>
	/// NPC's philosophical outlook or perspective on life
	/// </summary>
	public string WorldView { get; set; }
	
	/// <summary>
	/// Pre-generated dialogue lines specific to this NPC's personality
	/// </summary>
	public List<string> GeneratedDialogueLines { get; set; } = new List<string>();
	
	/// <summary>
	/// ElevenLabs voice model ID for text-to-speech synthesis
	/// </summary>
	public string VoiceModelId { get; set; }
	
	/// <summary>
	/// URL to stored audio file with NPC's synthesized voice greeting
	/// </summary>
	public string VoiceAudioUrl { get; set; }
	
	/// <summary>
	/// Notable quotes from the blog post that the NPC might reference
	/// </summary>
	public List<string> MemorableQuotes { get; set; } = new List<string>();
	
	/// <summary>
	/// Extensible storage for additional LLM-generated attributes not covered by other fields
	/// </summary>
	public Dictionary<string, object> CustomAttributes { get; set; } = new Dictionary<string, object>();
}