using Godot;
using System;

public class EnvironmentController : Node2D
{
    private CPUParticles2D fireflies;
    private CPUParticles2D butterflies;
    private CPUParticles2D waterReflections;
    private CPUParticles2D leafParticles;
    
    private float time = 0.0f;
    private Vector2 windInfluence = Vector2.Zero;
    
    private DayNightController dayNightController;

    public override void _Ready()
    {
        // Try to find particle systems
        fireflies = GetNodeOrNull<CPUParticles2D>("Fireflies");
        butterflies = GetNodeOrNull<CPUParticles2D>("Butterflies");
        waterReflections = GetNodeOrNull<CPUParticles2D>("WaterReflections");
        leafParticles = GetNodeOrNull<CPUParticles2D>("LeafParticles");
        
        // Find day/night controller - it's added as a sibling to Main
        var main = GetNodeOrNull("/root/Main");
        if (main != null)
        {
            dayNightController = main.GetParent()?.GetNodeOrNull<DayNightController>("DayNightController");
        }
        
        // Connect to wind controller if it exists
        var windController = GetNodeOrNull("/root/Main/WindController");
        if (windController != null && windController.HasSignal("wind_changed"))
        {
            windController.Connect("wind_changed", this, nameof(OnWindChanged));
        }
        
        // Connect to day/night controller
        if (dayNightController != null)
        {
            dayNightController.Connect(nameof(DayNightController.TimeChanged), this, nameof(OnTimeChanged));
            dayNightController.Connect(nameof(DayNightController.WeatherChanged), this, nameof(OnWeatherChanged));
        }
        
        SetupInitialStates();
    }

    public override void _Process(float delta)
    {
        time += delta;
        UpdateParticleEffects();
    }

    private void SetupInitialStates()
    {
        // Set default states for particle systems
        if (fireflies != null)
        {
            fireflies.Emitting = false;
        }
        
        if (butterflies != null)
        {
            butterflies.Emitting = true;
        }
        
        if (waterReflections != null)
        {
            waterReflections.Emitting = true;
        }
        
        if (leafParticles != null)
        {
            leafParticles.Emitting = false;
        }
    }

    private void UpdateParticleEffects()
    {
        if (dayNightController == null) return;
        
        bool isNight = dayNightController.IsNightTime();
        string weather = dayNightController.GetCurrentWeather();
        
        // Handle fireflies with pulsing glow and wind influence
        if (fireflies != null)
        {
            fireflies.Emitting = isNight && (weather == "Sunny" || weather == "Cloudy");
            if (fireflies.Emitting)
            {
                float pulse = (Mathf.Sin(time * 2) + 1) * 0.5f;
                fireflies.ScaleAmount = 2 + pulse;
                var color = fireflies.Color;
                color.a = 0.7f + pulse * 0.3f;
                fireflies.Color = color;
                fireflies.Direction = windInfluence;
            }
        }
        
        // Make butterflies react to wind
        if (butterflies != null)
        {
            butterflies.Emitting = !isNight && (weather == "Sunny" || weather == "Cloudy");
            if (butterflies.Emitting)
            {
                butterflies.Direction = windInfluence;
                butterflies.InitialVelocity = 30 + windInfluence.Length() * 20;
            }
        }
        
        // Enhance leaf particles with wind
        if (leafParticles != null)
        {
            leafParticles.Emitting = weather == "Rainy" || windInfluence.Length() > 0.3f;
            if (leafParticles.Emitting)
            {
                leafParticles.Direction = windInfluence;
                leafParticles.InitialVelocity = 40 + windInfluence.Length() * 50;
            }
        }
        
        // Make water reflections respond to wind
        if (waterReflections != null)
        {
            waterReflections.Amount = weather == "Sunny" ? 50 : 30;
            waterReflections.InitialVelocity = 5 + windInfluence.Length() * 10;
            waterReflections.Direction = windInfluence;
        }
    }

    public void OnWindChanged(float strength, Vector2 direction)
    {
        windInfluence = direction * strength;
    }

    public void OnTimeChanged(GameController.TimeOfDay timeOfDay, float currentHour)
    {
        // React to time changes if needed
        // This method can be used for time-specific environment changes
    }

    public void OnWeatherChanged(string weather)
    {
        // React to weather changes
        GD.Print($"Weather changed to: {weather}");
    }
}