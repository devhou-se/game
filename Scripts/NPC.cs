using Godot;
using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading.Tasks;

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
	
	public NPCPersonality Personality { get; set; } = new NPCPersonality();
	
	private bool _isBaileyButlerInTheOffice;

	private float _textTimeLeft = 0.0f;
	private Control _control;
	private PackedScene _interactionScreenScene;

	public override void _Ready()
	{
		base._Ready();
		_control = GetNode<Control>("Control");
		
		// Load the interaction screen scene
		_interactionScreenScene = GD.Load<PackedScene>("res://Scenes/InteractionScreen.tscn");

		var nameLabel = GetNode<Label>("Title");
		nameLabel.Text = NPCName;
		
		CheckIfBaileyButlerIsInTheOffice();
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
	
	public void Bump(Character bumper)
	{
		// Only respond if bumped by a Player
		if (!(bumper is Player))
		{
			return;
		}

		// Check global conversation cooldown
		if (Global.ConversationCooldown > 0)
		{
			return;
		}

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

			// Connect to know when conversation ends
			interactionScreen.Connect("tree_exiting", this, nameof(OnConversationEnded));
			return;
		}
	}

	private void OnConversationEnded()
	{
		// Set 1-second cooldown after conversation closes
		Global.ConversationCooldown = 1.0f;
	}
	
	private async void CheckIfBaileyButlerIsInTheOffice()
	{
		using (HttpClient client = new HttpClient())
		{
			try
			{
				string response = await client.GetStringAsync("http://isbaileybutlerintheoffice.today/raw");
				_isBaileyButlerInTheOffice = response.Equals("yes");
			}
			catch (Exception ex)
			{
				GD.PrintErr("Error checking if Bailey Butler is in the office: ", ex.Message);
			}
		}
	}

	private const float MoveWaitTime = 3f;
	private float _nextMoveWaitTime = 3f;
	
	private static readonly Vector2[] Vectors = {Vector2.Left, Vector2.Right, Vector2.Up, Vector2.Down};

	private void UpdateInputVector()
	{
		if (_nextMoveWaitTime > 0)
		{
			return;
		}

		_nextMoveWaitTime = MoveWaitTime;

		Random r = new Random();
		int index = r.Next(Vectors.Length);
		InputVector = Vectors[index];
	}
}
