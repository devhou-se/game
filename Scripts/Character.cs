using Godot;
using System;
using System.Collections.Generic;
using Object = Godot.Object;

/// <summary>
/// Represents a player character that can move on a grid-based system using MoveAndCollide
/// </summary>
public partial class Character : KinematicBody2D
{
	private float _speedMultiplier = 1;
	private float _speedDurationRemaining = 0;
	
	private float _shiftMultiplier = 1;
	public float ShiftMultiplier
	{
		set => _shiftMultiplier = value;
	}

	private const float GridSize = 16;
	private const float Speed = 48;
	private Vector2 _targetPosition;

	private const float BufferTimeMax = 0.05f;
	private Vector2 _bufferedVector = Vector2.Zero;
	private float _bufferTimeRemaining = 0;
	
	private ShapeCast2D _shapeCast;
	private AnimatedSprite _animatedSprite;
	
	private const float AnimationSpeed = 0.8f * Speed/GridSize;
	private string _currentAnimation = "idle";
	private string _currentDirection = "";
	private bool _currentFlip = false;
	private Vector2 _animationVector = Vector2.Zero;

	private CollisionShape2D _collider;

	private const string Idle = "idle";
	private const string Walk = "walk";
	
	private static readonly Godot.Collections.Dictionary<Vector2, string> DirectionAnimations = new Godot.Collections.Dictionary<Vector2, string>
	{
		{ Vector2.Left, "_side" },
		{ Vector2.Right, "_side" },
		{ Vector2.Up, "_back" },
		{ Vector2.Down, "" }
	};
	
	private static readonly Godot.Collections.Dictionary<Vector2, bool> DirectionFlip = new Godot.Collections.Dictionary<Vector2, bool>
	{
		{ Vector2.Left, true },
		{ Vector2.Right, false },
		{ Vector2.Up, false },
		{ Vector2.Down, false }
	};
	
	public override void _Ready()
	{
		_shapeCast = GetNode<ShapeCast2D>("ShapeCast2D");
		_animatedSprite = GetNode<AnimatedSprite>("AnimatedSprite");
		_collider = GetNode<CollisionShape2D>("CollisionShape2D");
		
		_animatedSprite.SpeedScale = AnimationSpeed;
		
		_targetPosition = Position;
	}
	
	public void Teleport(Vector2 position)
	{
		Position = position;
		_targetPosition = position;
	}

	/// <summary>
	/// Applies a temporary speed boost to the character
	/// </summary>
	/// <param name="multiplier">Speed multiplier to apply</param>
	/// <param name="duration">Duration of the speed boost in seconds</param>
	public void ApplySpeedBoost(float multiplier, float duration)
	{
		_speedMultiplier = multiplier;
		_speedDurationRemaining = duration;
	}

	public override void _Process(float delta)
	{
		ProcessSpeedBoost(delta);
	}

	private void ProcessSpeedBoost(float delta)
	{
		if (_speedDurationRemaining <= 0)
		{
			_speedMultiplier = 1;
			return;
		}

		_speedDurationRemaining -= delta;
	}
	
	public override void _PhysicsProcess(float delta)
	{
		ProcessBuffer();
		ProcessMove(delta);
		UpdateAnimation();
		ProcessInput(delta);

		_animatedSprite.Animation = _currentAnimation + _currentDirection;
		_animatedSprite.SpeedScale = AnimationSpeed * _speedMultiplier * _shiftMultiplier;
		_animatedSprite.FlipH = _currentFlip;
	}

	private void ProcessMove(float delta)
	{
		var path = _targetPosition - Position;

		var step = delta * Speed * _speedMultiplier * _shiftMultiplier;
		var distance = path.Length();
		
		if (path == Vector2.Zero || step > distance)
		{
			Position = _targetPosition;
			_collider.Position = Vector2.Zero;
			return;
		}

		var direction = path.Normalized();
		Position += direction * step;
		_collider.Position -= direction * step;
	}
	
	private void UpdateAnimation()
	{
		if (_animationVector == Vector2.Zero)
		{
			return;
		}
		
		_currentDirection = DirectionAnimations[_animationVector];
		_currentAnimation = (Position == _targetPosition) ? Idle : Walk;
		_currentFlip = DirectionFlip[_animationVector];
	}

	private void ProcessBuffer()
	{
		if (Position != _targetPosition)
			return;

		if (_bufferedVector == Vector2.Zero)
			return;
		
		_animationVector = _bufferedVector;
		
		var targetVector = _bufferedVector * GridSize;
		var targetPosition = Position + targetVector;

		_shapeCast.TargetPosition = targetVector;
		_shapeCast.ForceShapecastUpdate();

		if (_shapeCast.IsColliding())
		{
			var c = _shapeCast.GetCollider(0);

			if (_shapeCast.GetCollider(0) is Bumper bumper)
			{
				bumper.Bump(this);
			}

			_bufferedVector = Vector2.Zero;
			return;
		}

		GetPositionInParent();

		_targetPosition = targetPosition;
		_collider.Position += targetVector;
		_bufferedVector = Vector2.Zero;
	}

	public Vector2 InputVector
	{
		set
		{
			_bufferedVector = value;
			_bufferTimeRemaining = BufferTimeMax;
		}
	}

	private void ProcessInput(float delta)
	{
		if (_bufferTimeRemaining <= 0)
			_bufferedVector = Vector2.Zero;
		else
			_bufferTimeRemaining -= delta;
	}
}

public interface Bumper
{
	public void Bump(Character bumper);
}
