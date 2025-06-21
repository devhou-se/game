using Godot;
using System;

public class Menu : MarginContainer
{
	private VBoxContainer mainContainer;
	private Button playButton;
	private Button quitButton;
	private LineEdit nameInput;
	private Label nameLabel;

	public override void _Ready()
	{
		// Get the existing VBoxContainer from the scene
		mainContainer = GetNode<VBoxContainer>("VBoxContainer");
		
		// Create a container for the menu items with proper centering
		var centerContainer = new CenterContainer();
		mainContainer.AddChild(centerContainer);
		
		var menuContainer = new VBoxContainer();
		menuContainer.AddConstantOverride("separation", 20);
		centerContainer.AddChild(menuContainer);
		
		// Add some top margin
		var topSpacer = new Control();
		topSpacer.RectMinSize = new Vector2(0, 100);
		menuContainer.AddChild(topSpacer);
		
		// Create and setup name input
		nameLabel = new Label();
		nameLabel.Text = "Enter your name:";
		nameLabel.Modulate = new Color(1, 1, 1);
		menuContainer.AddChild(nameLabel);
		
		nameInput = new LineEdit();
		nameInput.RectMinSize = new Vector2(300, 40);
		nameInput.PlaceholderText = "Your name";
		nameInput.Connect("text_entered", this, nameof(OnNameEntered));
		menuContainer.AddChild(nameInput);
		
		// Add some spacing
		var spacer = new Control();
		spacer.RectMinSize = new Vector2(0, 20);
		menuContainer.AddChild(spacer);
		
		// Create and setup buttons
		playButton = CreateButton("Play", menuContainer);
		quitButton = CreateButton("Quit", menuContainer);
		
		// Connect button signals
		playButton.Connect("pressed", this, nameof(OnPlayPressed));
		quitButton.Connect("pressed", this, nameof(OnQuitPressed));
		
		// Give focus to name input
		nameInput.CallDeferred("grab_focus");
	}
	
	private Button CreateButton(string text, VBoxContainer parent)
	{
		var button = new Button();
		button.Text = text;
		button.RectMinSize = new Vector2(200, 50);
		parent.AddChild(button);
		return button;
	}

	private void OnNameEntered(string text)
	{
		if (!string.IsNullOrEmpty(text))
		{
			OnPlayPressed();
		}
	}

	private void OnPlayPressed()
	{
		string playerName = nameInput.Text;
		if (string.IsNullOrEmpty(playerName))
		{
			playerName = "Player";
		}
		
		GD.Print("User entered name: " + playerName);
		Global.PlayerName = playerName;
		
		// Change to the main game scene
		GetTree().ChangeScene("res://Scenes/Main.tscn");
	}

	private void OnQuitPressed()
	{
		GetTree().Quit();
	}
}