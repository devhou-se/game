using Godot;
using System;

public class TimeWeatherHUD : Control
{
    private Label timeLabel;
    private Label weatherLabel;
    private DayNightController dayNightController;
    
    public override void _Ready()
    {
        // Create the UI elements
        SetAnchorsAndMargins(MARGIN_LEFT, 0.0f);
        SetAnchorsAndMargins(MARGIN_TOP, 0.0f);
        SetAnchorsAndMargins(MARGIN_RIGHT, 0.0f);
        SetAnchorsAndMargins(MARGIN_BOTTOM, 0.0f);
        
        var vbox = new VBoxContainer();
        vbox.AnchorRight = 1.0f;
        vbox.MarginLeft = 10;
        vbox.MarginTop = 10;
        AddChild(vbox);
        
        // Time label
        timeLabel = new Label();
        timeLabel.Text = "Time: Loading...";
        timeLabel.AddStyleboxOverride("normal", CreatePanelBackground());
        vbox.AddChild(timeLabel);
        
        // Weather label
        weatherLabel = new Label();
        weatherLabel.Text = "Weather: Loading...";
        weatherLabel.AddStyleboxOverride("normal", CreatePanelBackground());
        vbox.AddChild(weatherLabel);
        
        // Find day/night controller
        dayNightController = GetNodeOrNull<DayNightController>("/root/Main/DayNightController");
        
        if (dayNightController != null)
        {
            dayNightController.Connect(nameof(DayNightController.TimeChanged), this, nameof(OnTimeChanged));
            dayNightController.Connect(nameof(DayNightController.WeatherChanged), this, nameof(OnWeatherChanged));
        }
    }
    
    private StyleBox CreatePanelBackground()
    {
        var styleBox = new StyleBoxFlat();
        styleBox.BgColor = new Color(0.0f, 0.0f, 0.0f, 0.7f);
        styleBox.BorderColor = new Color(1.0f, 1.0f, 1.0f, 0.3f);
        styleBox.BorderWidthBottom = 1;
        styleBox.BorderWidthTop = 1;
        styleBox.BorderWidthLeft = 1;
        styleBox.BorderWidthRight = 1;
        styleBox.CornerRadiusTopLeft = 5;
        styleBox.CornerRadiusTopRight = 5;
        styleBox.CornerRadiusBottomLeft = 5;
        styleBox.CornerRadiusBottomRight = 5;
        styleBox.ContentMarginLeft = 10;
        styleBox.ContentMarginRight = 10;
        styleBox.ContentMarginTop = 5;
        styleBox.ContentMarginBottom = 5;
        return styleBox;
    }
    
    public void OnTimeChanged(GameController.TimeOfDay timeOfDay, float currentHour)
    {
        string timeString = GetTimeString(currentHour);
        string periodString = GetPeriodString(timeOfDay);
        timeLabel.Text = $"Time: {timeString} ({periodString})";
    }
    
    public void OnWeatherChanged(string weather)
    {
        weatherLabel.Text = $"Weather: {weather.Capitalize()}";
    }
    
    private string GetTimeString(float hour)
    {
        int hours = (int)hour;
        int minutes = (int)((hour - hours) * 60);
        
        // Convert to 12-hour format
        int displayHour = hours;
        string ampm = "AM";
        
        if (hours == 0)
        {
            displayHour = 12;
        }
        else if (hours > 12)
        {
            displayHour = hours - 12;
            ampm = "PM";
        }
        else if (hours == 12)
        {
            ampm = "PM";
        }
        
        return $"{displayHour:D2}:{minutes:D2} {ampm}";
    }
    
    private string GetPeriodString(GameController.TimeOfDay timeOfDay)
    {
        switch (timeOfDay)
        {
            case GameController.TimeOfDay.Morning:
                return "Dawn";
            case GameController.TimeOfDay.Day:
                return "Day";
            case GameController.TimeOfDay.Evening:
                return "Dusk";
            case GameController.TimeOfDay.Night:
                return "Night";
            default:
                return "Unknown";
        }
    }
}