using Godot;
using System;

public class DayNightController : Node
{
    [Export] public float DayDuration = 720.0f; // 12 minutes for a full day
    [Export] public Color DayColor = new Color(1.0f, 1.0f, 1.0f, 1.0f);
    [Export] public Color NightColor = new Color(0.07f, 0.07f, 0.15f, 1.0f);
    [Export] public Color DawnDuskColor = new Color(0.86f, 0.70f, 0.70f, 1.0f);
    [Export] public bool UseTokyoRealTime = true;

    [Signal] public delegate void TimeChanged(GameController.TimeOfDay timeOfDay, float currentHour);
    [Signal] public delegate void WeatherChanged(string weather);

    private float time = 0.0f;
    private float currentHour = 0.0f;
    private string[] weatherEffects = { "clear", "cloudy", "rain" };
    private string currentWeather = "clear";
    private float weatherTransitionTime = 0.0f;
    private float weatherDuration = 300.0f; // 5 minutes per weather state
    
    private CanvasModulate canvasModulate;
    private GameController gameController;
    
    // Light management
    private Node lightsParent;
    private bool lightsEnabled = false;

    public override void _Ready()
    {
        gameController = GetNode<GameController>("/root/Main/GameController");
        
        // Create canvas modulate for lighting effects
        canvasModulate = new CanvasModulate();
        AddChild(canvasModulate);
        
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
        GetParent().AddChild(lightsParent);
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

    private void UpdateLighting()
    {
        Color color;
        
        // Dawn (5-7 AM)
        if (currentHour >= 5.0f && currentHour < 7.0f)
        {
            float t = (currentHour - 5.0f) / 2.0f;
            color = DayColor.LinearInterpolate(DawnDuskColor, t);
            SetLightsEnabled(false);
        }
        // Day (7 AM - 7 PM)
        else if (currentHour >= 7.0f && currentHour < 19.0f)
        {
            color = DayColor;
            SetLightsEnabled(false);
        }
        // Dusk (7-9 PM)
        else if (currentHour >= 19.0f && currentHour < 21.0f)
        {
            float t = (currentHour - 19.0f) / 2.0f;
            color = DawnDuskColor.LinearInterpolate(NightColor, t);
            SetLightsEnabled(t > 0.5f); // Turn on lights halfway through dusk
        }
        // Night
        else
        {
            color = NightColor;
            SetLightsEnabled(true);
        }
        
        canvasModulate.Color = color;
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
        EmitSignal(nameof(WeatherChanged), currentWeather);
    }

    private void UpdateGameControllerTime()
    {
        if (gameController != null)
        {
            GameController.TimeOfDay timeOfDay;
            
            if (currentHour >= 5.0f && currentHour < 7.0f)
                timeOfDay = GameController.TimeOfDay.Morning; // Dawn
            else if (currentHour >= 7.0f && currentHour < 19.0f)
                timeOfDay = GameController.TimeOfDay.Day;
            else if (currentHour >= 19.0f && currentHour < 21.0f)
                timeOfDay = GameController.TimeOfDay.Evening; // Dusk
            else
                timeOfDay = GameController.TimeOfDay.Night;
            
            gameController.SetTime(timeOfDay);
            EmitSignal(nameof(TimeChanged), timeOfDay, currentHour);
        }
    }

    private void SetLightsEnabled(bool enabled)
    {
        if (lightsEnabled == enabled) return;
        
        lightsEnabled = enabled;
        
        // Enable/disable all light nodes
        foreach (Node child in lightsParent.GetChildren())
        {
            if (child is Light2D light)
            {
                light.Enabled = enabled;
            }
        }
    }

    // Public methods for other systems to query time
    public float GetCurrentHour() => currentHour;
    public GameController.TimeOfDay GetTimeOfDay() => gameController?.GetTime() ?? GameController.TimeOfDay.Day;
    public string GetCurrentWeather() => currentWeather;
    public bool IsNightTime() => lightsEnabled;

    // Method to add lights to the system
    public void AddLight(Vector2 position, float energy = 1.0f, Color? color = null)
    {
        var light = new Light2D();
        light.Position = position;
        light.Energy = energy;
        light.Color = color ?? new Color(1.0f, 0.9f, 0.7f, 1.0f); // Warm light color
        light.TextureScale = 2.0f;
        light.Enabled = lightsEnabled;
        lightsParent.AddChild(light);
    }

    // Method to add street lights automatically to outdoor scenes
    public void SetupStreetLights(Node2D scene)
    {
        // This would be called from GameController when loading outdoor scenes
        // For now, add some example lights - in a real implementation,
        // you'd parse the tilemap or scene to find appropriate positions
        
        var random = new Random(42); // Use seed for consistent placement
        for (int i = 0; i < 10; i++)
        {
            var pos = new Vector2(
                random.Next(-500, 500),
                random.Next(-500, 500)
            );
            AddLight(pos, 0.8f);
        }
    }
}