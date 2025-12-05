using Godot;
using System;

public class GameController : Node
{
	private Player player;
	private Player currentPlayer;
	private Node2D level;
	private Node2D levelParent;
	private DayNightController dayNightController;
	
	public override void _Ready()
	{
		Global.Controller = this;
		levelParent = GetNode<Node2D>("../CurrentLevel");
		player = GD.Load<PackedScene>("res://Scenes/Player.tscn").Instance<Player>();
		
		// Initialize day/night system
		InitializeDayNightSystem();
		
		Goto("World");
		
		// Demonstrate NPC placement - place Bailey at vending machine
		CallDeferred("PlaceBaileyAtVendingMachine");
	}
	
	private void PlaceBaileyAtVendingMachine()
	{
		// Place Bailey at the vending machine location
		NPCLocationManager.Instance.PlaceNPC("Bailey", "World", "vending machine");
	}
	
	public override void _Process(float delta)
	{
		if (coolDown > 0.0f)
			coolDown -= delta;
	}
	
	private float coolDown = 0.0f;
	
	public void Goto(string scene)
	{
		if (coolDown > 0.0f)
			return;
		coolDown = 0.2f;
		
		if (currentPlayer != null)
		{
			var parent = currentPlayer.GetParent();
			parent.RemoveChild(currentPlayer);
		}
		
		if (level != null)
			level.QueueFree();
		
		var ls = GD.Load<PackedScene>($"res://Scenes/{scene}.tscn");
		level = ls.Instance<Node2D>();
		levelParent.AddChild(level);
		
		var ySort = level.GetNode("Characters");

		if (currentPlayer == null)
			currentPlayer = player;
		
		ySort.AddChild(player);
		
		player.Teleport(Vector2.Zero);
		
		// Setup day/night effects for outdoor scenes
		SetupSceneDayNight(scene);
	}

	public enum TimeOfDay
	{
		Morning,
		Day,
		Evening,
		Night,
	}
	private TimeOfDay timeOfDay;

	public TimeOfDay GetTime()
	{
		return timeOfDay;
	}
	public void SetTime(TimeOfDay time)
	{
		timeOfDay = time;
	}
	
	private void InitializeDayNightSystem()
	{
		// Create day/night controller (use CallDeferred to avoid timing issues)
		dayNightController = new DayNightController();
		dayNightController.Name = "DayNightController";
		GetParent().CallDeferred("add_child", dayNightController);
	}
	
	private void SetupSceneDayNight(string sceneName)
	{
		// Only apply day/night effects to outdoor scenes
		string[] outdoorScenes = { "World", "Town", "tokyo_overworld" };
		bool isOutdoor = false;
		
		foreach (string outdoorScene in outdoorScenes)
		{
			if (sceneName.Equals(outdoorScene, StringComparison.OrdinalIgnoreCase))
			{
				isOutdoor = true;
				break;
			}
		}
		
		if (isOutdoor && dayNightController != null)
		{
			// Setup street lights for this scene (deferred to avoid timing issues)
			CallDeferred("SetupSceneLighting", level);
			
			// Add environment controller if particles exist
			var environmentController = new EnvironmentController();
			environmentController.Name = "EnvironmentController";
			level.CallDeferred("add_child", environmentController);
			
			// Ensure CanvasModulate is working for this scene (deferred to avoid timing issues)
			CallDeferred("EnsureSceneCanvasModulate");
		}
	}
	
	private void SetupSceneLighting(Node2D scene)
	{
		if (dayNightController != null && scene != null)
		{
			dayNightController.SetupStreetLights(scene);
		}
	}
	
	private void EnsureSceneCanvasModulate()
	{
		if (dayNightController != null)
		{
			dayNightController.EnsureCanvasModulate();
		}
	}
	
	// Public methods for other systems to access day/night info
	public DayNightController GetDayNightController()
	{
		return dayNightController;
	}
	
	public bool IsNightTime()
	{
		return dayNightController?.IsNightTime() ?? false;
	}
	
	public string GetCurrentWeather()
	{
		return dayNightController?.GetCurrentWeather() ?? "Sunny";
	}
}
