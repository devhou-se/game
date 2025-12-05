using Godot;

public partial class DrinkCan : Area2D
{
	[Export]
	public float SpeedBoostMultiplier { get; set; } = 2.0f;

	[Export]
	public float SpeedBoostDuration { get; set; } = 5.0f;

	private Tween _tween;
	private Sprite _sprite;
	private Node2D _light;
	private string _currentWeather = "Sunny";
	private GameController.TimeOfDay _currentTimeOfDay = GameController.TimeOfDay.Day;

	public override void _Ready()
	{
		Connect("body_entered", this, nameof(OnBodyEntered));
		_tween = GetNode<Tween>("Tween");
		_sprite = GetNode<Sprite>("Sprite");

		// Get the light if it exists
		if (HasNode("Light2D"))
		{
			_light = GetNode<Node2D>("Light2D");

			// Create a radial gradient texture for the light
			if (_light is Light2D light2D)
			{
				var lightTexture = CreateRadialGradientTexture(128);
				light2D.Texture = lightTexture;
			}

			_light.Visible = false; // Start with light off
		}

		// Connect to DayNightController weather and time changes
		CallDeferred(nameof(ConnectToWeatherSystem));
	}

	private void ConnectToWeatherSystem()
	{
		// Find the DayNightController
		var dayNightController = GetNodeOrNull<DayNightController>("/root/Main/DayNightController");
		if (dayNightController == null)
		{
			// Try parent path
			dayNightController = GetTree().Root.GetNodeOrNull<DayNightController>("Main/DayNightController");
		}

		if (dayNightController != null)
		{
			dayNightController.Connect("WeatherChanged", this, nameof(OnWeatherChanged));
			dayNightController.Connect("TimeChanged", this, nameof(OnTimeChanged));
			// Get initial state
			_currentWeather = dayNightController.GetCurrentWeather();
			_currentTimeOfDay = dayNightController.GetTimeOfDay();
			UpdateLight();
		}
	}

	private void OnWeatherChanged(string weather)
	{
		_currentWeather = weather;
		UpdateLight();
	}

	private void OnTimeChanged(GameController.TimeOfDay timeOfDay, float currentHour)
	{
		_currentTimeOfDay = timeOfDay;
		UpdateLight();
	}

	private void UpdateLight()
	{
		if (_light == null) return;

		// Turn on light when: cloudy, rainy, evening, or night
		bool shouldGlow = (_currentWeather == "Cloudy" || _currentWeather == "Rainy" ||
						   _currentTimeOfDay == GameController.TimeOfDay.Evening ||
						   _currentTimeOfDay == GameController.TimeOfDay.Night);

		_light.Visible = shouldGlow;

		// Increase saturation of vending machine sprite when glowing
		if (_sprite != null)
		{
			if (shouldGlow)
			{
				// Boost colors to make it more saturated/vibrant
				_sprite.Modulate = new Color(1.3f, 1.3f, 1.3f, 1.0f);
			}
			else
			{
				// Normal colors
				_sprite.Modulate = new Color(1.0f, 1.0f, 1.0f, 1.0f);
			}
		}
	}

	private void OnBodyEntered(Node body)
	{
		GD.Print("OnBodyEntered called");
		if (body is Character player)
		{
			GD.Print("Character entered");
			player.ApplySpeedBoost(SpeedBoostMultiplier, SpeedBoostDuration);
			FlashAndJiggle();
		}
	}

	private void FlashAndJiggle()
	{
		GD.Print("FlashAndJiggle called");
		// Flash animation
		_tween.InterpolateProperty(_sprite, "modulate:a", 1.0f, 0.0f, 0.1f, Tween.TransitionType.Sine, Tween.EaseType.InOut, 0.0f);
		_tween.InterpolateProperty(_sprite, "modulate:a", 0.0f, 1.0f, 0.1f, Tween.TransitionType.Sine, Tween.EaseType.InOut, 0.1f);

		// Jiggle animation
		_tween.InterpolateProperty(_sprite, "scale", new Vector2(1, 1), new Vector2(1.2f, 0.8f), 0.1f, Tween.TransitionType.Sine, Tween.EaseType.InOut, 0.0f);
		_tween.InterpolateProperty(_sprite, "scale", new Vector2(1.2f, 0.8f), new Vector2(0.8f, 1.2f), 0.1f, Tween.TransitionType.Sine, Tween.EaseType.InOut, 0.1f);
		_tween.InterpolateProperty(_sprite, "scale", new Vector2(0.8f, 1.2f), new Vector2(1, 1), 0.1f, Tween.TransitionType.Sine, Tween.EaseType.InOut, 0.2f);

		_tween.Start();
	}

	private ImageTexture CreateRadialGradientTexture(int size)
	{
		var image = new Image();
		image.Create(size, size, false, Image.Format.Rgba8);
		image.Lock();

		float center = size / 2.0f;
		float maxRadius = center;

		for (int y = 0; y < size; y++)
		{
			for (int x = 0; x < size; x++)
			{
				float dx = x - center;
				float dy = y - center;
				float distance = Mathf.Sqrt(dx * dx + dy * dy);
				float normalized = Mathf.Clamp(distance / maxRadius, 0, 1);
				float alpha = 1.0f - normalized;

				image.SetPixel(x, y, new Color(1, 1, 1, alpha));
			}
		}

		image.Unlock();

		var texture = new ImageTexture();
		texture.CreateFromImage(image, 0);
		return texture;
	}
}
