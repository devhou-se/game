using Godot;
using System;

public class GameController : Node
{
	private Player player;
	private Player currentPlayer;
	private Node2D level;
	private Node2D levelParent;
	
	public override void _Ready()
	{
		Global.Controller = this;
		levelParent = GetNode<Node2D>("../CurrentLevel");
		player = GD.Load<PackedScene>("res://Scenes/Player.tscn").Instance<Player>();
		Goto("World");
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
}
