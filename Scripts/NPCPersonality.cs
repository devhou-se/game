using System;
using System.Collections.Generic;

[Serializable]
public class NPCPersonality
{
	public string BlogPostUrl { get; set; }
	
	public string BlogPostTitle { get; set; }
	
	public DateTime BlogPostDate { get; set; }
	
	public string AuthorName { get; set; }
	
	public string PersonalityType { get; set; }
	
	public Dictionary<string, float> TraitScores { get; set; } = new Dictionary<string, float>
	{
		{"openness", 0.5f},
		{"conscientiousness", 0.5f},
		{"extraversion", 0.5f},
		{"agreeableness", 0.5f},
		{"neuroticism", 0.5f}
	};
	
	public string BackgroundStory { get; set; }
	
	public string Occupation { get; set; }
	
	public List<string> Interests { get; set; } = new List<string>();
	
	public List<string> Hobbies { get; set; } = new List<string>();
	
	public string SpeechPattern { get; set; }
	
	public string VoiceCharacteristics { get; set; }
	
	public Dictionary<string, string> EmotionalResponses { get; set; } = new Dictionary<string, string>
	{
		{"happy", ""},
		{"sad", ""},
		{"angry", ""},
		{"surprised", ""},
		{"fearful", ""},
		{"neutral", ""}
	};
	
	public List<string> CatchPhrases { get; set; } = new List<string>();
	
	public List<string> ConversationTopics { get; set; } = new List<string>();
	
	public string Motivation { get; set; }
	
	public string Fear { get; set; }
	
	public string Goal { get; set; }
	
	public Dictionary<string, string> RelationshipToTopics { get; set; } = new Dictionary<string, string>();
	
	public string MoodBaseline { get; set; } = "neutral";
	
	public float EnergyLevel { get; set; } = 0.5f;
	
	public float Talkativeness { get; set; } = 0.5f;
	
	public float Humor { get; set; } = 0.5f;
	
	public float Formality { get; set; } = 0.5f;
	
	public List<string> KnowledgeDomains { get; set; } = new List<string>();
	
	public string WorldView { get; set; }
	
	public List<string> GeneratedDialogueLines { get; set; } = new List<string>();
	
	public string VoiceModelId { get; set; }
	
	public string VoiceAudioUrl { get; set; }
	
	public List<string> MemorableQuotes { get; set; } = new List<string>();
	
	public Dictionary<string, object> CustomAttributes { get; set; } = new Dictionary<string, object>();
}