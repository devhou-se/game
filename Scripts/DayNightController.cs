using Godot;
using System;

public class DayNightController : Node
{
    [Export] public float DayDuration = 86400.0f; // 24 hours in seconds (for real-time)
    [Export] public Color DayColor = new Color(1.0f, 1.0f, 1.0f, 1.0f);
    [Export] public Color NightColor = new Color(0.15f, 0.15f, 0.3f, 1.0f); // More visible blue night
    [Export] public Color DawnDuskColor = new Color(1.0f, 0.6f, 0.4f, 1.0f); // More orange dawn/dusk
    [Export] public bool UseTokyoRealTime = true; // Enabled to use Tokyo real time

    [Signal] public delegate void TimeChanged(GameController.TimeOfDay timeOfDay, float currentHour);
    [Signal] public delegate void WeatherChanged(string weather);

    private float time = 0.0f;
    private float currentHour = 0.0f;
    private string[] weatherEffects = { "Sunny", "Cloudy", "Rainy" };
    private string currentWeather = "Sunny";
    private float weatherTransitionTime = 0.0f;
    private float weatherDuration = 3600.0f; // 1 hour per weather state
    
    private CanvasModulate canvasModulate;
    private GameController gameController;
    
    // Light management
    private Node lightsParent;
    private bool lightsEnabled = false;
    
    // Weather particle systems
    private CPUParticles2D rainParticles;
    private CPUParticles2D cloudParticles;

    public override void _Ready()
    {
        gameController = GetNode<GameController>("/root/Main/GameController");
        
        // Create canvas modulate for lighting effects
        // CanvasModulate needs to be at the root of the viewport to affect everything
        canvasModulate = new CanvasModulate();
        canvasModulate.Name = "DayNightCanvasModulate";
        
        // Add to the root of the scene tree for global effect
        GetTree().Root.CallDeferred("add_child", canvasModulate);
        
        // Initialize time based on Tokyo real time if enabled
        if (UseTokyoRealTime)
        {
            InitializeTokyoTime();
        }
        else
        {
            time = (8.0f / 24.0f) * DayDuration; // Start at 8 AM
        }
        
        // Initialize weather
        ChangeWeather();
        
        // Setup lights parent node
        lightsParent = new Node2D();
        lightsParent.Name = "DayNightLights";
        CallDeferred("AddLightsParent");
        
        // Setup weather particles
        CallDeferred("SetupWeatherParticles");
    }

    public override void _Process(float delta)
    {
        if (UseTokyoRealTime)
        {
            UpdateTokyoTime();
        }
        else
        {
            time += delta;
            if (time >= DayDuration)
            {
                time = 0.0f;
            }
        }
        
        currentHour = (time / DayDuration) * 24.0f;
        UpdateLighting();
        UpdateWeather(delta);
        UpdateGameControllerTime();
    }

    private void InitializeTokyoTime()
    {
        var tokyoTime = GetTokyoTime();
        var hour = tokyoTime.Hour + (tokyoTime.Minute / 60.0f);
        time = (hour / 24.0f) * DayDuration;
    }

    private void UpdateTokyoTime()
    {
        var tokyoTime = GetTokyoTime();
        var hour = tokyoTime.Hour + (tokyoTime.Minute / 60.0f) + (tokyoTime.Second / 3600.0f);
        time = (hour / 24.0f) * DayDuration;
    }

    private DateTime GetTokyoTime()
    {
        // Tokyo is UTC+9
        return DateTime.UtcNow.AddHours(9);
    }

    private float lastDebugTime = 0.0f;
    
    private void UpdateLighting()
    {
        Color color = DayColor; // Initialize with default day color
        
        // Debug print every 60 seconds when using real time
        float debugInterval = UseTokyoRealTime ? 60.0f : 2.0f;
        if (time - lastDebugTime >= debugInterval)
        {
            lastDebugTime = time;
            GD.Print($"DayNight: Hour={currentHour:F1}, Weather={currentWeather}, Night={lightsEnabled}");
        }
        
        // Calculate smooth transitions throughout the day
        // Night: 9 PM - 5 AM (8 hours)
        // Dawn: 5 AM - 7 AM (2 hours)
        // Day: 7 AM - 5 PM (10 hours)
        // Dusk: 5 PM - 9 PM (4 hours)
        
        if (currentHour >= 21.0f || currentHour < 5.0f)
        {
            // Night (9 PM - 5 AM)
            color = NightColor;
            SetLightsEnabled(true);
        }
        else if (currentHour >= 5.0f && currentHour < 7.0f)
        {
            // Dawn (5 AM - 7 AM)
            float t = (currentHour - 5.0f) / 2.0f; // 0 to 1 over 2 hours
            color = NightColor.LinearInterpolate(DawnDuskColor, t * 0.7f); // First 70% of dawn
            if (t > 0.7f)
            {
                // Last 30% of dawn transitions to day
                float t2 = (t - 0.7f) / 0.3f;
                color = DawnDuskColor.LinearInterpolate(DayColor, t2);
            }
            SetLightsEnabled(t < 0.5f); // Lights off halfway through dawn
        }
        else if (currentHour >= 7.0f && currentHour < 17.0f)
        {
            // Day (7 AM - 5 PM)
            color = DayColor;
            SetLightsEnabled(false);
        }
        else if (currentHour >= 17.0f && currentHour < 21.0f)
        {
            // Dusk (5 PM - 9 PM)
            float t = (currentHour - 17.0f) / 4.0f; // 0 to 1 over 4 hours
            if (t < 0.5f)
            {
                // First half of dusk: day to golden hour
                float t1 = t / 0.5f;
                color = DayColor.LinearInterpolate(DawnDuskColor, t1);
            }
            else
            {
                // Second half of dusk: golden hour to night
                float t2 = (t - 0.5f) / 0.5f;
                color = DawnDuskColor.LinearInterpolate(NightColor, t2);
            }
            SetLightsEnabled(t > 0.7f); // Lights on in last 30% of dusk
        }
        
        // Apply weather effects to the color
        color = ApplyWeatherEffects(color);
        
        // Apply color to canvas
        if (canvasModulate != null && IsInstanceValid(canvasModulate))
        {
            canvasModulate.Color = color;
        }
        else
        {
            // Try to recreate if missing
            EnsureCanvasModulate();
            if (canvasModulate != null)
            {
                canvasModulate.Color = color;
            }
        }
    }

    private Color ApplyWeatherEffects(Color baseColor)
    {
        switch (currentWeather)
        {
            case "Cloudy":
                // Cloudy makes everything slightly darker and grayer
                baseColor.r *= 0.85f;
                baseColor.g *= 0.85f;
                baseColor.b *= 0.9f; // Slightly more blue/gray
                break;
                
            case "Rainy":
                // Rainy makes everything darker and more blue/gray
                baseColor.r *= 0.7f;
                baseColor.g *= 0.7f;
                baseColor.b *= 0.8f; // More blue tint
                break;
        }
        
        return baseColor;
    }
    
    private void UpdateWeather(float delta)
    {
        weatherTransitionTime += delta;
        if (weatherTransitionTime >= weatherDuration)
        {
            ChangeWeather();
            weatherTransitionTime = 0.0f;
        }
    }

    private void ChangeWeather()
    {
        var random = new Random();
        string newWeather;
        do
        {
            newWeather = weatherEffects[random.Next(weatherEffects.Length)];
        } while (newWeather == currentWeather);
        
        currentWeather = newWeather;
        UpdateWeatherParticles();
        EmitSignal(nameof(WeatherChanged), currentWeather);
    }
    
    private void SetupWeatherParticles()
    {
        // Create rain particles
        rainParticles = new CPUParticles2D();
        rainParticles.Name = "RainParticles";
        rainParticles.Amount = 200;
        rainParticles.Lifetime = 2.0f;
        rainParticles.Preprocess = 0.5f;
        rainParticles.SpeedScale = 2.0f;
        rainParticles.Emitting = false;
        
        // Configure rain appearance
        rainParticles.Direction = new Vector2(0.1f, 1); // Slightly angled rain
        rainParticles.Spread = 5.0f;
        rainParticles.InitialVelocity = 300.0f;
        rainParticles.InitialVelocityRandom = 0.1f;
        rainParticles.AngularVelocity = 0.0f;
        rainParticles.LinearAccel = 50.0f;
        
        // Rain drop appearance
        rainParticles.ScaleAmount = 2.0f;
        rainParticles.ScaleAmountRandom = 0.5f;
        rainParticles.Color = new Color(0.6f, 0.7f, 0.9f, 0.6f); // Light blue, semi-transparent
        
        // Make rain cover the screen
        var rect = GetViewport().GetVisibleRect();
        rainParticles.EmissionShape = CPUParticles2D.EmissionShapeEnum.Rectangle;
        rainParticles.EmissionRectExtents = new Vector2(rect.Size.x / 2, 10);
        rainParticles.Position = new Vector2(rect.Size.x / 2, -10);
        rainParticles.ZIndex = 100; // Render on top
        
        GetParent().CallDeferred("add_child", rainParticles);
        
        // Create cloud/fog particles for cloudy weather
        cloudParticles = new CPUParticles2D();
        cloudParticles.Name = "CloudParticles";
        cloudParticles.Amount = 30;
        cloudParticles.Lifetime = 20.0f;
        cloudParticles.Preprocess = 10.0f;
        cloudParticles.SpeedScale = 0.3f;
        cloudParticles.Emitting = false;
        
        // Configure cloud appearance
        cloudParticles.Direction = new Vector2(1, 0); // Horizontal movement
        cloudParticles.Spread = 20.0f;
        cloudParticles.InitialVelocity = 20.0f;
        cloudParticles.InitialVelocityRandom = 0.5f;
        
        // Cloud appearance
        cloudParticles.ScaleAmount = 50.0f;
        cloudParticles.ScaleAmountRandom = 0.3f;
        cloudParticles.Color = new Color(0.8f, 0.8f, 0.8f, 0.2f); // Gray, very transparent
        
        // Clouds across the top of screen
        cloudParticles.EmissionShape = CPUParticles2D.EmissionShapeEnum.Rectangle;
        cloudParticles.EmissionRectExtents = new Vector2(rect.Size.x, 100);
        cloudParticles.Position = new Vector2(rect.Size.x / 2, 100);
        cloudParticles.ZIndex = 90; // Render below rain but above scene
        
        GetParent().CallDeferred("add_child", cloudParticles);
    }
    
    private void UpdateWeatherParticles()
    {
        if (rainParticles != null)
        {
            rainParticles.Emitting = currentWeather == "Rainy";
        }
        
        if (cloudParticles != null)
        {
            cloudParticles.Emitting = currentWeather == "Cloudy";
        }
    }

    private void UpdateGameControllerTime()
    {
        if (gameController != null)
        {
            GameController.TimeOfDay timeOfDay;
            
            // Match the time periods defined above
            if (currentHour >= 21.0f || currentHour < 5.0f)
            {
                // Night (9 PM - 5 AM)
                timeOfDay = GameController.TimeOfDay.Night;
            }
            else if (currentHour >= 5.0f && currentHour < 7.0f)
            {
                // Dawn (5 AM - 7 AM) - Morning
                timeOfDay = GameController.TimeOfDay.Morning;
            }
            else if (currentHour >= 7.0f && currentHour < 17.0f)
            {
                // Day (7 AM - 5 PM)
                timeOfDay = GameController.TimeOfDay.Day;
            }
            else
            {
                // Dusk (5 PM - 9 PM) - Evening
                timeOfDay = GameController.TimeOfDay.Evening;
            }
            
            gameController.SetTime(timeOfDay);
            EmitSignal(nameof(TimeChanged), timeOfDay, currentHour);
        }
    }

    private void SetLightsEnabled(bool enabled)
    {
        if (lightsEnabled == enabled) return;
        
        lightsEnabled = enabled;
        
        // Enable/disable all light nodes
        if (lightsParent == null) return;
        
        // Adjust light intensity based on weather
        float weatherIntensity = 1.0f;
        if (currentWeather == "Rainy")
        {
            weatherIntensity = 1.3f; // Lights appear brighter in rain
        }
        else if (currentWeather == "Cloudy")
        {
            weatherIntensity = 1.1f; // Slightly brighter in cloudy weather
        }
        
        foreach (Node child in lightsParent.GetChildren())
        {
            if (child is Sprite sprite)
            {
                sprite.Visible = enabled;
                if (enabled)
                {
                    sprite.Modulate = new Color(weatherIntensity, weatherIntensity, weatherIntensity, 0.5f);
                }
            }
            else if (child is Light2D light)
            {
                light.Enabled = enabled;
                if (enabled)
                {
                    light.Energy = weatherIntensity;
                }
            }
        }
    }

    // Public methods for other systems to query time
    public float GetCurrentHour() => currentHour;
    public GameController.TimeOfDay GetTimeOfDay() => gameController?.GetTime() ?? GameController.TimeOfDay.Day;
    public string GetCurrentWeather() => currentWeather;
    public bool IsNightTime() => lightsEnabled;

    private void AddLightsParent()
    {
        if (GetParent() != null)
        {
            GetParent().AddChild(lightsParent);
        }
    }
    
    // Public method to ensure CanvasModulate is properly set up
    public void EnsureCanvasModulate()
    {
        // Check if we're in the tree first
        if (!IsInsideTree())
        {
            GD.PrintErr("DayNightController: Not in tree yet, cannot ensure CanvasModulate");
            return;
        }
        
        var tree = GetTree();
        if (tree == null || tree.Root == null)
        {
            GD.PrintErr("DayNightController: Tree or Root is null");
            return;
        }
        
        // Remove any existing CanvasModulate nodes first
        foreach (Node child in tree.Root.GetChildren())
        {
            if (child is CanvasModulate && child != canvasModulate)
            {
                child.QueueFree();
            }
        }
        
        // If our canvas modulate was freed, recreate it
        if (canvasModulate == null || !IsInstanceValid(canvasModulate))
        {
            canvasModulate = new CanvasModulate();
            canvasModulate.Name = "DayNightCanvasModulate";
            tree.Root.AddChild(canvasModulate);
            GD.Print("Recreated CanvasModulate");
        }
    }

    // Method to add lights to the system
    public void AddLight(Vector2 position, float energy = 1.0f, Color? color = null)
    {
        if (lightsParent == null)
        {
            GD.PrintErr("DayNightController: lightsParent is null, cannot add light");
            return;
        }
        
        // Create a simple sprite to represent the light
        var lightSprite = new Sprite();
        lightSprite.Position = position;
        
        // Create a simple circular texture for the light
        var image = new Image();
        image.Create(64, 64, false, Image.Format.Rgba8);
        image.Lock();
        
        var center = new Vector2(32, 32);
        for (int x = 0; x < 64; x++)
        {
            for (int y = 0; y < 64; y++)
            {
                var dist = center.DistanceTo(new Vector2(x, y));
                var alpha = Mathf.Clamp(1.0f - (dist / 32.0f), 0.0f, 1.0f);
                alpha = alpha * alpha; // Quadratic falloff
                
                var pixelColor = color ?? new Color(1.0f, 0.9f, 0.7f, 1.0f);
                pixelColor.a = alpha * energy;
                image.SetPixel(x, y, pixelColor);
            }
        }
        
        image.Unlock();
        
        var texture = new ImageTexture();
        texture.CreateFromImage(image);
        lightSprite.Texture = texture;
        lightSprite.Scale = new Vector2(3, 3); // Make lights larger
        lightSprite.Modulate = new Color(1, 1, 1, 0.5f); // Semi-transparent
        lightSprite.Visible = lightsEnabled;
        lightSprite.ZIndex = 10;
        
        lightsParent.AddChild(lightSprite);
    }

    // Method to add street lights automatically to outdoor scenes
    public void SetupStreetLights(Node2D scene)
    {
        // Add street lights in a grid pattern for testing
        // Create a nice pattern of lights around the scene
        
        // Add lights along main paths
        for (int x = -600; x <= 600; x += 200)
        {
            for (int y = -600; y <= 600; y += 200)
            {
                // Street light positions
                var pos = new Vector2(x, y);
                
                // Vary the light properties slightly for realism
                float energy = 0.7f + (float)(new Random(x * y).NextDouble() * 0.3f);
                
                // Warm street light color with slight variations
                var color = new Color(
                    1.0f,
                    0.9f + (float)(new Random(x + y).NextDouble() * 0.1f),
                    0.6f + (float)(new Random(x - y).NextDouble() * 0.2f),
                    1.0f
                );
                
                AddLight(pos, energy, color);
            }
        }
        
        // Add some extra lights at key locations for visual interest
        AddLight(new Vector2(0, -100), 1.2f, new Color(1.0f, 0.95f, 0.8f)); // Bright center light
        AddLight(new Vector2(-150, 50), 1.0f, new Color(1.0f, 0.9f, 0.7f)); // Near vending machine area
        AddLight(new Vector2(150, 50), 1.0f, new Color(1.0f, 0.9f, 0.7f)); // Opposite side
        
        GD.Print($"Added {lightsParent.GetChildCount()} street lights to the scene");
    }
}