using Godot;
using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading.Tasks;
using DevHouse;

public class NPC : Character, Bumper
{
	[Export]
	public bool CaresAboutBaileyButlerBeingInTheOffice { get; set; } 
	
	[Export]
	public bool EnableFullInteraction { get; set; } = true;
	
	[Export]
	public string NPCName { get; set; }
	
	[Export(PropertyHint.MultilineText)]
	public string[] DialogueLines { get; set; } = {
		"Hello there!",
		"Nice to meet you.",
		"How can I help you today?"
	};
	
	[Export]
	public bool UseDialogueTree { get; set; } = false;
	
	[Export]
	public string NPCDefinitionId { get; set; }
	
	// New properties for definition system
	public NPCDefinition Definition { get; set; }
	public MovementPattern MovementPattern { get; set; } = MovementPattern.Random;
	public float MoveSpeed { get; set; } = 50.0f;
	public float WaitTimeBetweenMoves { get; set; } = 3.0f;
	
	private DialogueTree _dialogueTree;
	private DialogueManager _dialogueManager;
	
	private bool _isBaileyButlerInTheOffice;
	public bool IsBaileyButlerInTheOffice => _isBaileyButlerInTheOffice;

	private float _textTimeLeft = 0.0f;
	private Control _control;
	private PackedScene _interactionScreenScene;

	public override void _Ready()
	{
		base._Ready();
		_control = GetNode<Control>("Control");
		
		// Load the interaction screen scene
		_interactionScreenScene = GD.Load<PackedScene>("res://Scenes/InteractionScreen.tscn");

		// NPCs must be defined via JSON - either through NPCDefinitionId or by NPCName
		string definitionId = !string.IsNullOrEmpty(NPCDefinitionId) ? NPCDefinitionId : 
							  !string.IsNullOrEmpty(NPCName) ? NPCName.ToLower().Replace(" ", "_") : null;
		
		if (!string.IsNullOrEmpty(definitionId))
		{
			// Defer loading to ensure autoload is ready
			CallDeferred("LoadDefinition", definitionId);
		}
		else
		{
			GD.PrintErr("NPC has no definition ID or name! NPCs must be defined via JSON files.");
			NPCName = "Unknown";
			DialogueLines = new string[] { "ERROR: No NPC definition found!" };
			var nameLabel = GetNode<Label>("Title");
			nameLabel.Text = NPCName;
		}
		
		if (CaresAboutBaileyButlerBeingInTheOffice)
		{
			CheckIfBaileyButlerIsInTheOffice();
		}
		
		// Initialize dialogue system
		_dialogueManager = new DialogueManager();
		if (!UseDialogueTree && DialogueLines != null && DialogueLines.Length > 0)
		{
			// Convert simple dialogue lines to a tree structure
			_dialogueTree = DialogueTree.CreateSimpleTree(DialogueLines);
		}
		// Dialogue tree should be set by ApplyDefinitionToNPC if using complex dialogue
	}

	public override void _Process(float delta)
	{
		base._Process(delta);

		_nextMoveWaitTime -= delta;

		if (_textTimeLeft > 0)
		{
			_textTimeLeft -= delta;
			if (_textTimeLeft <= 0)
			{
				_control.Visible = false;
			}
		}
	}

	public override void _PhysicsProcess(float delta)
	{
		UpdateInputVector();
		base._PhysicsProcess(delta);
	}
	
	public void Bump()
	{
		if (_textTimeLeft > 0)
		{
			return;
		}
		
		// Check if we should use full interaction screen
		if (EnableFullInteraction && _interactionScreenScene != null)
		{
			// Create a new instance of the interaction screen
			var interactionScreen = _interactionScreenScene.Instance<InteractionScreen>();
			
			// Find the UI CanvasLayer and add it there to ensure viewport-relative positioning
			var uiLayer = GetNode<CanvasLayer>("/root/Main/UI");
			if (uiLayer != null)
			{
				uiLayer.AddChild(interactionScreen);
			}
			else
			{
				// Fallback to current scene if UI layer not found
				GetTree().CurrentScene.AddChild(interactionScreen);
			}
			
			// Show the interaction screen
			interactionScreen.ShowInteraction(this);
			return;
		}
	}
	
	public DialogueTree GetDialogueTree()
	{
		return _dialogueTree;
	}
	
	public DialogueManager GetDialogueManager()
	{
		return _dialogueManager;
	}
	
	public void SetDialogueTree(DialogueTree tree)
	{
		_dialogueTree = tree;
		UseDialogueTree = tree != null;
	}
	
	private void LoadDefinition(string definitionId)
	{
		GD.Print($"NPC trying to load definition: {definitionId}");
		
		// Get the NPCDefinitions autoload
		var npcDefinitions = GetNode<NPCDefinitions>("/root/NPCDefinitions");
		if (npcDefinitions == null)
		{
			GD.PrintErr("NPCDefinitions autoload not found!");
			SetDefaultValues();
			return;
		}
		
		// Try to get the definition from the autoload
		var definition = npcDefinitions.GetDefinition(definitionId);
		if (definition != null)
		{
			Definition = definition;
			// Apply all NPC properties from the definition
			npcDefinitions.ApplyDefinitionToNPC(this, definition);
			GD.Print($"Successfully loaded NPC definition for: {NPCName} (ID: {definitionId})");
		}
		else
		{
			GD.PrintErr($"NPC definition not found: {definitionId}");
			GD.PrintErr($"Available definitions: {npcDefinitions.HasDefinition(definitionId)}");
			SetDefaultValues();
		}
		
		var nameLabel = GetNode<Label>("Title");
		nameLabel.Text = NPCName;
	}
	
	private void SetDefaultValues()
	{
		// Set minimal defaults to prevent errors
		if (string.IsNullOrEmpty(NPCName)) NPCName = "Unknown";
		if (DialogueLines == null || DialogueLines.Length == 0)
		{
			DialogueLines = new string[] { "ERROR: No NPC definition found!" };
		}
	}
	
	public void UpdateDialogueRuntimeValues()
	{
		if (_dialogueTree == null || _dialogueTree.Nodes == null) return;
		
		foreach (var node in _dialogueTree.Nodes.Values)
		{
			if (!string.IsNullOrEmpty(node.Text))
			{
				// Replace office status placeholder for Bailey
				if (NPCName == "Bailey" && node.Text.Contains("{{OFFICE_STATUS}}"))
				{
					node.Text = node.Text.Replace("{{OFFICE_STATUS}}", 
						_isBaileyButlerInTheOffice ? "in the office today" : "working remotely today");
				}
				
				// Add more runtime replacements as needed
			}
		}
	}
	
	
	
	private async void CheckIfBaileyButlerIsInTheOffice()
	{
		using (HttpClient client = new HttpClient())
		{
			try
			{
				string response = await client.GetStringAsync("http://isbaileybutlerintheoffice.today/raw");
				_isBaileyButlerInTheOffice = response.Equals("yes");
				
				// Update dialogue with runtime values after status check
				UpdateDialogueRuntimeValues();
			}
			catch (Exception ex)
			{
				GD.PrintErr("Error checking if Bailey Butler is in the office: ", ex.Message);
			}
		}
	}

	private float _nextMoveWaitTime = 3f;
	
	private static readonly Vector2[] Vectors = {Vector2.Left, Vector2.Right, Vector2.Up, Vector2.Down};

	private void UpdateInputVector()
	{
		if (_nextMoveWaitTime > 0)
		{
			return;
		}

		_nextMoveWaitTime = WaitTimeBetweenMoves;

		switch (MovementPattern)
		{
			case MovementPattern.Static:
				InputVector = Vector2.Zero;
				break;
			case MovementPattern.Random:
				Random r = new Random();
				int index = r.Next(Vectors.Length);
				InputVector = Vectors[index];
				break;
			case MovementPattern.Patrol:
				// TODO: Implement patrol movement with waypoints
				InputVector = Vector2.Zero;
				break;
			case MovementPattern.Follow:
				// TODO: Implement follow player behavior
				InputVector = Vector2.Zero;
				break;
			case MovementPattern.Flee:
				// TODO: Implement flee from player behavior
				InputVector = Vector2.Zero;
				break;
			default:
				InputVector = Vector2.Zero;
				break;
		}
	}
}
