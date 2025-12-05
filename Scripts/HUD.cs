using Godot;
using System;

public partial class HUD : CanvasLayer
{
	private LineEdit nameInput;
	private ProgressBar staminaBar;
	private ProgressBar energyBar;
	private Label timeLabel;
	private Label weatherLabel;
	private Player player;

	public override void _Ready()
	{
		GD.Print("HUD._Ready() called - using HUD.cs script");

		// Get UI elements
		if (HasNode("MarginContainer/CenterContainer/HBoxContainer/Stamina"))
			staminaBar = GetNode<ProgressBar>("MarginContainer/CenterContainer/HBoxContainer/Stamina");

		if (HasNode("MarginContainer/CenterContainer/HBoxContainer/Energy"))
			energyBar = GetNode<ProgressBar>("MarginContainer/CenterContainer/HBoxContainer/Energy");

		if (HasNode("MarginContainer/CenterContainer/HBoxContainer/InfoPanel/HBoxContainer2/TimeLabel"))
		{
			timeLabel = GetNode<Label>("MarginContainer/CenterContainer/HBoxContainer/InfoPanel/HBoxContainer2/TimeLabel");
			GD.Print("Found TimeLabel");
		}

		if (HasNode("MarginContainer/CenterContainer/HBoxContainer/InfoPanel/HBoxContainer2/WeatherLabel"))
		{
			weatherLabel = GetNode<Label>("MarginContainer/CenterContainer/HBoxContainer/InfoPanel/HBoxContainer2/WeatherLabel");
			GD.Print($"Found WeatherLabel with text: {weatherLabel.Text}");
		}

		// Check if LineEdit exists before trying to get it
		if (HasNode("MarginContainer/CenterContainer/HBoxContainer/LineEdit"))
		{
			nameInput = GetNode<LineEdit>("MarginContainer/CenterContainer/HBoxContainer/LineEdit");
			nameInput.Connect("text_entered", this, nameof(OnNameEntered));
		}
		else if (HasNode("LineEdit"))
		{
			nameInput = GetNode<LineEdit>("LineEdit");
			nameInput.Connect("text_entered", this, nameof(OnNameEntered));
		}

		// Find player
		CallDeferred(nameof(FindPlayer));
	}
	
	private void FindPlayer()
	{
		// Try to find player in the scene
		var players = GetTree().GetNodesInGroup("player");
		if (players.Count > 0)
		{
			player = players[0] as Player;
			if (player != null)
			{
				player.Connect("StaminaChanged", this, nameof(OnStaminaChanged));
			}
		}
	}
	
	public override void _Process(float delta)
	{
		// Update time if we have a day/night controller
		// First try to get it from the expected location
		DayNightController dayNightController = null;
		
		// Try different paths to find the controller
		if (GetNodeOrNull("/root/Main") != null)
		{
			// The controller is added as a sibling to Main, not as a child
			var main = GetNode("/root/Main");
			dayNightController = main.GetParent()?.GetNodeOrNull<DayNightController>("DayNightController");
		}
		
		// If still not found, try through the GameController
		if (dayNightController == null && Global.Controller != null)
		{
			dayNightController = Global.Controller.GetDayNightController();
		}
		
		if (dayNightController != null && timeLabel != null)
		{
			var hour = dayNightController.GetCurrentHour();
			var displayHour = Mathf.FloorToInt(hour) % 12;
			if (displayHour == 0) displayHour = 12;
			var minute = Mathf.FloorToInt((hour - Mathf.Floor(hour)) * 60);
			var ampm = hour >= 12 ? "PM" : "AM";
			timeLabel.Text = $"{displayHour}:{minute:D2} {ampm}";
			
			// Update weather
			if (weatherLabel != null)
			{
				var weather = dayNightController.GetCurrentWeather();
				weatherLabel.Text = weather + " :)";
			}
		}
		else
		{
			// Debug when not found
			if (Engine.GetFramesDrawn() % 120 == 0) // Every 2 seconds at 60fps
			{
				GD.Print($"HUD: DayNightController={dayNightController != null}, TimeLabel={timeLabel != null}, WeatherLabel={weatherLabel != null}");
			}
		}
	}

	private void OnNameEntered(string text)
	{
		GD.Print("User entered name: " + text);
		// Store the entered name in the Global singleton
		Global.PlayerName = text;
	}
	
	private void OnStaminaChanged(float current, float max)
	{
		if (staminaBar != null)
		{
			staminaBar.MaxValue = max;
			staminaBar.Value = current;
		}
	}
}
