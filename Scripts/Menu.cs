using Godot;
using System;

public class Menu : MarginContainer
{
	private VBoxContainer mainContainer;
	private MarginContainer marginContainer;
	private VBoxContainer buttonContainer;
	private Button playButton;
	private Button quitButton;
	private LineEdit nameInput;
	private Label nameLabel;
	private TextureRect background;

	public override void _Ready()
	{
		// Set the size of the MarginContainer
		SetAnchorsAndMarginsPreset(LayoutPreset.Wide);

		// Create and setup background
		background = new TextureRect();
		background.Texture = (Texture)GD.Load("res://Assets/menu.jpeg");
		background.StretchMode = TextureRect.StretchModeEnum.Scale;
		background.Expand = true;
		AddChild(background);

		// Create main container
		mainContainer = new VBoxContainer();
		AddChild(mainContainer);

		// Set main container properties
		mainContainer.SetAnchorsPreset(Control.LayoutPreset.Center);
		mainContainer.SizeFlagsHorizontal = (int)Control.SizeFlags.Fill;
		mainContainer.SizeFlagsVertical = (int)Control.SizeFlags.Fill;
		mainContainer.AddConstantOverride("separation", 10);

		// Create margin container
		marginContainer = new MarginContainer();
		marginContainer.AddConstantOverride("margin_top", 50);
		mainContainer.AddChild(marginContainer);

		// Create child container for buttons and input
		buttonContainer = new VBoxContainer();
		marginContainer.AddChild(buttonContainer);

		// Set child container properties
		buttonContainer.SetAnchorsPreset(Control.LayoutPreset.Center);
		buttonContainer.SizeFlagsHorizontal = (int)Control.SizeFlags.Fill;
		buttonContainer.SizeFlagsVertical = (int)Control.SizeFlags.Fill;
		buttonContainer.AddConstantOverride("separation", 10);

		// Create and setup name input
		nameLabel = new Label();
		nameLabel.Text = "Enter your name:";
		nameLabel.SizeFlagsHorizontal = (int)Control.SizeFlags.ShrinkCenter;
		buttonContainer.AddChild(nameLabel);

		nameInput = new LineEdit();
		nameInput.SizeFlagsHorizontal = (int)Control.SizeFlags.ShrinkCenter;
		nameInput.Connect("text_entered", this, nameof(OnNameEntered));
		buttonContainer.AddChild(nameInput);

		// Create and setup buttons
		playButton = CreateButton("Play");
		quitButton = CreateButton("Quit");

		// Connect button signals
		playButton.Connect("pressed", this, nameof(OnPlayPressed));
		quitButton.Connect("pressed", this, nameof(OnQuitPressed));
	}

	private Button CreateButton(string text)
	{
		var button = new Button();
		button.Text = text;
		button.RectMinSize = new Vector2(200, 50);
		button.SizeFlagsHorizontal = (int)Control.SizeFlags.ShrinkCenter;
		buttonContainer.AddChild(button);
		return button;
	}

	private void OnNameEntered(string text)
	{
		GD.Print("User entered name: " + text);
		// Store the entered name in the Global singleton
		Global.PlayerName = text;
	}

	private void OnPlayPressed()
	{
		OnNameEntered(nameInput.Text);
		GetTree().ChangeScene("res://Scenes/Main.tscn");
	}

	private void OnQuitPressed()
	{
		GetTree().Quit();
	}
}
