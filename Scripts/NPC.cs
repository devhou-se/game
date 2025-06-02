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
	public string NPCName { get; set; } = "NPC";
	
	[Export(PropertyHint.MultilineText)]
	public string[] DialogueLines { get; set; } = new string[] {
		"Hello there!",
		"Nice to meet you.",
		"How can I help you today?"
	};
	
	private bool _isBaileyButlerInTheOffice;

	private float _textTimeLeft = 0.0f;
	private Control _control;
	private InteractionScreen _interactionScreen;

	public override void _Ready()
	{
		base._Ready();
		_control = GetNode<Control>("Control");
		
		// Try to find the interaction screen in the scene
		_interactionScreen = GetTree().CurrentScene.GetNodeOrNull<InteractionScreen>("InteractionScreen");
		
		// Update name label if it exists
		var nameLabel = GetNodeOrNull<Label>("NameLabel");
		if (nameLabel != null)
		{
			NPCName = nameLabel.Text;
		}
		
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
	
	public void Bump()
	{
		if (_textTimeLeft > 0)
		{
			return;
		}
		
		// Check if we should use full interaction screen
		if (EnableFullInteraction && _interactionScreen != null)
		{
			List<string> dialogue = new List<string>();
			
			// Add special dialogue if they care about Bailey Butler
			if (CaresAboutBaileyButlerBeingInTheOffice)
			{
				if (_isBaileyButlerInTheOffice)
				{
					dialogue.Add("Oh thank goodness I found you!");
					dialogue.Add("I need to let you know that Bailey Butler is in the office today!");
					dialogue.Add("You should definitely go say hi!");
				}
				else
				{
					dialogue.Add("Sorry, I can't talk right now...");
					dialogue.Add("I'm too busy looking for Bailey Butler.");
					dialogue.Add("He's definitely not in the office today!");
				}
			}
			else
			{
				// Use the configured dialogue lines
				dialogue.AddRange(DialogueLines);
			}
			
			// Show the interaction screen
			_interactionScreen.ShowInteraction(NPCName, dialogue, GetNode<AnimatedSprite>("AnimatedSprite").Frames);
			return;
		}

		List<string> items = new List<string>
		{
			"Watch out mate!", "I'm walking here!", "OI",
			// Add 1000 more wild and funny responses
			"Did you just bump into a legend?", "I was in the middle of a dance-off!", "You owe me a soda now!",
			"I was just about to win the lottery!", "You just interrupted my invisible friend!", "I was practicing my moonwalk!",
			"You made me lose my place in the book I'm reading!", "I was just about to discover a new planet!", "You made me drop my sandwich!",
			"I was just about to break the world record for standing still!", "You just activated my trap card!", "I was in the middle of a staring contest with a wall!",
			"You made me forget the meaning of life!", "I was just about to solve world hunger!", "You made me lose my train of thought!",
			"I was just about to invent a new color!", "You made me spill my coffee!", "I was just about to teleport to another dimension!",
			"You made me forget my password!", "I was just about to become a superhero!", "You made me lose my balance on my unicycle!",
			"I was just about to finish my time machine!", "You made me drop my ice cream!", "I was just about to win a Nobel Prize!",
			"You made me forget my name!", "I was just about to break the sound barrier!", "You made me lose my place in the universe!",
			"I was just about to discover the secret to immortality!", "You made me drop my pizza!", "I was just about to become a wizard!",
			"You made me forget how to breathe!", "I was just about to invent a new language!", "You made me lose my rhythm!",
			"I was just about to become a rock star!", "You made me drop my taco!", "I was just about to solve the mystery of the Bermuda Triangle!",
			"You made me forget my purpose in life!", "I was just about to become a ninja!", "You made me lose my zen!",
			"I was just about to invent a new sport!", "You made me drop my hot dog!", "I was just about to become a pirate!",
			"You made me forget my dreams!", "I was just about to break the internet!", "You made me lose my groove!",
			"I was just about to become a Jedi!", "You made me drop my popcorn!", "I was just about to solve the mystery of the Loch Ness Monster!",
			"You made me forget my goals!", "I was just about to become a detective!", "You made me lose my focus!",
			"I was just about to invent a new dance move!", "You made me drop my burger!", "I was just about to become a superhero sidekick!",
			"You made me forget my plans!", "I was just about to break the fourth wall!", "You made me lose my cool!",
			"I was just about to become a time traveler!", "You made me drop my fries!", "I was just about to solve the mystery of Stonehenge!",
			"You made me forget my ambitions!", "I was just about to become a secret agent!", "You made me lose my patience!",
			"I was just about to invent a new gadget!", "You made me drop my sushi!", "I was just about to become a space explorer!",
			"You made me forget my aspirations!", "I was just about to break the laws of physics!", "You made me lose my temper!",
			"I was just about to become a mad scientist!", "You made me drop my salad!", "I was just about to solve the mystery of the pyramids!",
			"You made me forget my desires!", "I was just about to become a ghost hunter!", "You made me lose my serenity!",
			"I was just about to invent a new recipe!", "You made me drop my spaghetti!", "I was just about to become a dragon slayer!",
			"You made me forget my wishes!", "I was just about to break the speed of light!", "You made me lose my tranquility!",
			"I was just about to become a treasure hunter!", "You made me drop my soup!", "I was just about to solve the mystery of the Sphinx!",
			"You made me forget my hopes!", "I was just about to become a myth buster!", "You made me lose my harmony!",
			"I was just about to invent a new instrument!", "You made me drop my cake!", "I was just about to become a monster hunter!",
			"You made me forget my fantasies!", "I was just about to break the time-space continuum!", "You made me lose my balance!",
			"I was just about to become a superhero mentor!", "You made me drop my donut!", "I was just about to solve the mystery of the Yeti!",
			"You made me forget my passions!", "I was just about to become a vampire slayer!", "You made me lose my peace!",
			"I was just about to invent a new game!", "You made me drop my cookie!", "I was just about to become a werewolf hunter!",
			"You made me forget my inspirations!", "I was just about to break the matrix!", "You made me lose my calm!",
			"I was just about to become a superhero trainer!", "You made me drop my muffin!", "I was just about to solve the mystery of the Chupacabra!",
			"You made me forget my motivations!", "I was just about to become a zombie hunter!", "You made me lose my composure!",
			"I was just about to invent a new toy!", "You made me drop my croissant!", "I was just about to become a ghost whisperer!",
			"You made me forget my dreams!", "I was just about to break the sound barrier!", "You made me lose my serenity!",
			"I was just about to become a superhero sidekick!", "You made me drop my sandwich!", "I was just about to solve the mystery of the Bermuda Triangle!",
			"You made me forget my goals!", "I was just about to become a detective!", "You made me lose my focus!",
			"I was just about to invent a new dance move!", "You made me drop my burger!", "I was just about to become a superhero mentor!",
			"You made me forget my plans!", "I was just about to break the fourth wall!", "You made me lose my cool!",
			"I was just about to become a time traveler!", "You made me drop my fries!", "I was just about to solve the mystery of Stonehenge!",
			"You made me forget my ambitions!", "I was just about to become a secret agent!", "You made me lose my patience!",
			"I was just about to invent a new gadget!", "You made me drop my sushi!", "I was just about to become a space explorer!",
			"You made me forget my aspirations!", "I was just about to break the laws of physics!", "You made me lose my temper!",
			"I was just about to become a mad scientist!", "You made me drop my salad!", "I was just about to solve the mystery of the pyramids!",
			"You made me forget my desires!", "I was just about to become a ghost hunter!", "You made me lose my serenity!",
			"I was just about to invent a new recipe!", "You made me drop my spaghetti!", "I was just about to become a dragon slayer!",
			"You made me forget my wishes!", "I was just about to break the speed of light!", "You made me lose my tranquility!",
			"I was just about to become a treasure hunter!", "You made me drop my soup!", "I was just about to solve the mystery of the Sphinx!",
			"You made me forget my hopes!", "I was just about to become a myth buster!", "You made me lose my harmony!",
			"I was just about to invent a new instrument!", "You made me drop my cake!", "I was just about to become a monster hunter!",
			"You made me forget my fantasies!", "I was just about to break the time-space continuum!", "You made me lose my balance!",
			"I was just about to become a superhero mentor!", "You made me drop my donut!", "I was just about to solve the mystery of the Yeti!",
			"You made me forget my passions!", "I was just about to become a vampire slayer!", "You made me lose my peace!",
			"I was just about to invent a new game!", "You made me drop my cookie!", "I was just about to become a werewolf hunter!",
			"You made me forget my inspirations!", "I was just about to break the matrix!", "You made me lose my calm!",
			"I was just about to become a superhero trainer!", "You made me drop my muffin!", "I was just about to solve the mystery of the Chupacabra!",
			"You made me forget my motivations!", "I was just about to become a zombie hunter!", "You made me lose my composure!",
			"I was just about to invent a new toy!", "You made me drop my croissant!", "I was just about to become a ghost whisperer!",
			"You made me forget my dreams!", "I was just about to break the sound barrier!", "You made me lose my serenity!",
			"I was just about to become a superhero sidekick!", "You made me drop my sandwich!", "I was just about to solve the mystery of the Bermuda Triangle!",
			"You made me forget my goals!", "I was just about to become a detective!", "You made me lose my focus!",
			"I was just about to invent a new dance move!", "You made me drop my burger!", "I was just about to become a superhero mentor!",
			"You made me forget my plans!", "I was just about to break the fourth wall!", "You made me lose my cool!",
			"I was just about to become a time traveler!", "You made me drop my fries!", "I was just about to solve the mystery of Stonehenge!",
			"You made me forget my ambitions!", "I was just about to become a secret agent!", "You made me lose my patience!",
			"I was just about to invent a new gadget!", "You made me drop my sushi!", "I was just about to become a space explorer!",
			"You made me forget my aspirations!", "I was just about to break the laws of physics!", "You made me lose my temper!",
			"I was just about to become a mad scientist!", "You made me drop my salad!", "I was just about to solve the mystery of the pyramids!",
			"You made me forget my desires!", "I was just about to become a ghost hunter!", "You made me lose my serenity!",
			"I was just about to invent a new recipe!", "You made me drop my spaghetti!", "I was just about to become a dragon slayer!",
			"You made me forget my wishes!", "I was just about to break the speed of light!", "You made me lose my tranquility!",
			"I was just about to become a treasure hunter!", "You made me drop my soup!", "I was just about to solve the mystery of the Sphinx!",
			"You made me forget my hopes!", "I was just about to become a myth buster!", "You made me lose my harmony!",
			"I was just about to invent a new instrument!", "You made me drop my cake!", "I was just about to become a monster hunter!",
			"You made me forget my fantasies!", "I was just about to break the time-space continuum!", "You made me lose my balance!",
			"I was just about to become a superhero mentor!", "You made me drop my donut!", "I was just about to solve the mystery of the Yeti!",
			"You made me forget my passions!", "I was just about to become a vampire slayer!", "You made me lose my peace!",
			"I was just about to invent a new game!", "You made me drop my cookie!", "I was just about to become a werewolf hunter!",
			"You made me forget my inspirations!", "I was just about to break the matrix!", "You made me lose my calm!",
			"I was just about to become a superhero trainer!", "You made me drop my muffin!", "I was just about to solve the mystery of the Chupacabra!",
			"You made me forget my motivations!", "I was just about to become a zombie hunter!", "You made me lose my composure!",
			"I was just about to invent a new toy!", "You made me drop my croissant!", "I was just about to become a ghost whisperer!",
			"You made me forget my dreams!", "I was just about to break the sound barrier!", "You made me lose my serenity!",
			"I was just about to become a superhero sidekick!", "You made me drop my sandwich!", "I was just about to solve the mystery of the Bermuda Triangle!",
			"You made me forget my goals!", "I was just about to become a detective!", "You made me lose my focus!",
			"I was just about to invent a new dance move!", "You made me drop my burger!", "I was just about to become a superhero mentor!",
			"You made me forget my plans!", "I was just about to break the fourth wall!", "You made me lose my cool!",
			"I was just about to become a time traveler!", "You made me drop my fries!", "I was just about to solve the mystery of Stonehenge!",
			"You made me forget my ambitions!", "I was just about to become a secret agent!", "You made me lose my patience!",
			"I was just about to invent a new gadget!", "You made me drop my sushi!", "I was just about to become a space explorer!",
			"You made me forget my aspirations!", "I was just about to break the laws of physics!", "You made me lose my temper!",
			"I was just about to become a mad scientist!", "You made me drop my salad!", "I was just about to solve the mystery of the pyramids!",
			"You made me forget my desires!", "I was just about to become a ghost hunter!", "You made me lose my serenity!",
			"I was just about to invent a new recipe!", "You made me drop my spaghetti!", "I was just about to become a dragon slayer!",
			"You made me forget my wishes!", "I was just about to break the speed of light!", "You made me lose my tranquility!",
			"I was just about to become a treasure hunter!", "You made me drop my soup!", "I was just about to solve the mystery of the Sphinx!",
			"You made me forget my hopes!", "I was just about to become a myth buster!", "You made me lose my harmony!",
			"I was just about to invent a new instrument!", "You made me drop my cake!", "I was just about to become a monster hunter!",
			"You made me forget my fantasies!", "I was just about to break the time-space continuum!", "You made me lose my balance!",
			"I was just about to become a superhero mentor!", "You made me drop my donut!", "I was just about to solve the mystery of the Yeti!",
			"You made me forget my passions!", "I was just about to become a vampire slayer!", "You made me lose my peace!",
			"I was just about to invent a new game!", "You made me drop my cookie!", "I was just about to become a werewolf hunter!",
			"You made me forget my inspirations!", "I was just about to break the matrix!", "You made me lose my calm!",
			"I was just about to become a superhero trainer!", "You made me drop my muffin!", "I was just about to solve the mystery of the Chupacabra!",
			"You made me forget my motivations!", "I was just about to become a zombie hunter!", "You made me lose my composure!",
			"I was just about to invent a new toy!", "You made me drop my croissant!", "I was just about to become a ghost whisperer!",
			"You made me forget my dreams!", "I was just about to break the sound barrier!", "You made me lose my serenity!",
			"I was just about to become a superhero sidekick!", "You made me drop my sandwich!", "I was just about to solve the mystery of the Bermuda Triangle!",
			"You made me forget my goals!", "I was just about to become a detective!", "You made me lose my focus!",
			"I was just about to invent a new dance move!", "You made me drop my burger!", "I was just about to become a superhero mentor!",
			"You made me forget my plans!", "I was just about to break the fourth wall!", "You made me lose my cool!",
			"I was just about to become a time traveler!", "You made me drop my fries!", "I was just about to solve the mystery of Stonehenge!",
			"You made me forget my ambitions!", "I was just about to become a secret agent!", "You made me lose my patience!",
			"I was just about to invent a new gadget!", "You made me drop my sushi!", "I was just about to become a space explorer!",
			"You made me forget my aspirations!", "I was just about to break the laws of physics!", "You made me lose my temper!",
			"I was just about to become a mad scientist!", "You made me drop my salad!", "I was just about to solve the mystery of the pyramids!",
			"You made me forget my desires!", "I was just about to become a ghost hunter!", "You made me lose my serenity!",
			"I was just about to invent a new recipe!", "You made me drop my spaghetti!", "I was just about to become a dragon slayer!",
			"You made me forget my wishes!", "I was just about to break the speed of light!", "You made me lose my tranquility!",
			"I was just about to become a treasure hunter!", "You made me drop my soup!", "I was just about to solve the mystery of the Sphinx!",
			"You made me forget my hopes!", "I was just about to become a myth buster!", "You made me lose my harmony!",
			"I was just about to invent a new instrument!", "You made me drop my cake!", "I was just about to become a monster hunter!", "OI" };
		Random random = new Random();
		string text;
		if (CaresAboutBaileyButlerBeingInTheOffice)
		{
			text = _isBaileyButlerInTheOffice ? "thank god I found you. I need to let you know that Bailey Butler is in the office today. You should go say hi!" : "can't talk right now, too busy looking for Bailey Butler because he's sure as hell not in the office today.";
		}
		else
		{
			text = items[random.Next(items.Count)];
		}

		// Access the stored player name
		string playerName = Global.PlayerName;
		if (playerName.Length > 0)
		{
			text = playerName + " " + text;
		}
		_textTimeLeft = 3.0f;

		_control.Visible = true;
		_control.GetNode<Label>("Label").Text = text;
	}
	
	private async void CheckIfBaileyButlerIsInTheOffice()
	{
		using (HttpClient client = new HttpClient())
		{
			try
			{
				string response = await client.GetStringAsync("https://isbaileybutlerintheoffice.today");
				_isBaileyButlerInTheOffice = response.Contains("<h1>yes</h1>");
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
