using Godot;
using System;

public partial class VendingMachine : StaticBody2D
{
	[Export] public PackedScene DrinkCanScene;
	[Export] public float CanSpawnOffset = 32.0f;
	[Export] public int MaxCans = 3;
	[Export] public float CooldownTime = 2.0f;
	
	private int currentCans = 0;
	private float cooldownTimer = 0.0f;
	private bool playerNearby = false;
	private AnimatedSprite animatedSprite;
	private Area2D interactionArea;
	private Label promptLabel;
	
	[Signal] public delegate void CanDispensed();
	
	public override void _Ready()
	{
		// Get animated sprite if it exists
		if (HasNode("AnimatedSprite"))
			animatedSprite = GetNode<AnimatedSprite>("AnimatedSprite");
			
		// Create interaction area
		CreateInteractionArea();
		
		// Create prompt label
		CreatePromptLabel();
		
		// Load drink can scene if not set
		if (DrinkCanScene == null)
		{
			DrinkCanScene = GD.Load<PackedScene>("res://Scenes/DrinkCan.tscn");
		}
	}
	
	private void CreateInteractionArea()
	{
		interactionArea = new Area2D();
		interactionArea.Name = "InteractionArea";
		
		var collisionShape = new CollisionShape2D();
		var rectShape = new RectangleShape2D();
		rectShape.Extents = new Vector2(48, 48);
		collisionShape.Shape = rectShape;
		
		interactionArea.AddChild(collisionShape);
		AddChild(interactionArea);
		
		// Connect signals
		interactionArea.Connect("body_entered", this, nameof(OnBodyEntered));
		interactionArea.Connect("body_exited", this, nameof(OnBodyExited));
	}
	
	private void CreatePromptLabel()
	{
		promptLabel = new Label();
		promptLabel.Name = "PromptLabel";
		promptLabel.Text = "Press SPACE to buy drink";
		promptLabel.AddColorOverride("font_color", Colors.White);
		promptLabel.AddColorOverride("font_color_shadow", Colors.Black);
		promptLabel.AddConstantOverride("shadow_offset_x", 1);
		promptLabel.AddConstantOverride("shadow_offset_y", 1);
		promptLabel.SetPosition(new Vector2(-60, -40));
		promptLabel.Visible = false;
		AddChild(promptLabel);
	}
	
	public override void _Process(float delta)
	{
		// Update cooldown
		if (cooldownTimer > 0)
		{
			cooldownTimer -= delta;
		}
		
		// Update prompt visibility
		if (playerNearby && promptLabel != null)
		{
			promptLabel.Visible = cooldownTimer <= 0 && currentCans < MaxCans;
		}
	}
	
	private void OnBodyEntered(Node body)
	{
		if (body is Player)
		{
			playerNearby = true;
			if (promptLabel != null)
				promptLabel.Visible = cooldownTimer <= 0 && currentCans < MaxCans;
		}
	}
	
	private void OnBodyExited(Node body)
	{
		if (body is Player)
		{
			playerNearby = false;
			if (promptLabel != null)
				promptLabel.Visible = false;
		}
	}
	
	// Called by the player's interaction system
	public void Interact(Player player)
	{
		DispenseCan();
	}
	
	private void DispenseCan()
	{
		// Check if we can dispense
		if (cooldownTimer > 0 || currentCans >= MaxCans || DrinkCanScene == null)
		{
			GD.Print("VendingMachine: Cannot dispense - on cooldown or max cans reached");
			return;
		}
		
		// Create and spawn the can
		var can = DrinkCanScene.Instance() as DrinkCan;
		if (can == null)
		{
			GD.PrintErr("VendingMachine: Failed to instance DrinkCan");
			return;
		}
		
		// Set can position below the vending machine
		can.GlobalPosition = GlobalPosition + Vector2.Down * CanSpawnOffset;
		
		// Add to scene
		GetParent().AddChild(can);
		
		// Update state
		currentCans++;
		cooldownTimer = CooldownTime;
		
		// Play animation if available
		if (animatedSprite != null)
		{
			animatedSprite.Play("dispense");
		}
		
		// Connect to can's tree_exited signal to track when it's collected
		can.Connect("tree_exited", this, nameof(OnCanCollected));
		
		EmitSignal(nameof(CanDispensed));
		GD.Print($"VendingMachine: Dispensed can! Total: {currentCans}/{MaxCans}");
	}
	
	private void OnCanCollected()
	{
		currentCans = Math.Max(0, currentCans - 1);
		GD.Print($"VendingMachine: Can collected! Remaining: {currentCans}/{MaxCans}");
	}
}