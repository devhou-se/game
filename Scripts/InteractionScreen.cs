using Godot;
using System.Collections.Generic;

public class InteractionScreen : Control
{
    private RichTextLabel dialogueText;
    private Label nameLabel;
    private AnimatedSprite characterSprite;
    private Button continueButton;
    private Label clickIndicator;
    
    private List<string> dialogueLines = new List<string>();
    private int currentLineIndex = 0;
    private string npcName = "";
    
    public override void _Ready()
    {
        dialogueText = GetNode<RichTextLabel>("DialogueBox/DialogueText");
        nameLabel = GetNode<Label>("CharacterDisplay/NameLabel");
        characterSprite = GetNode<AnimatedSprite>("CharacterDisplay/AnimatedSprite");
        continueButton = GetNode<Button>("DialogueBox/ContinueButton");
        clickIndicator = GetNode<Label>("DialogueBox/ClickIndicator");
        
        continueButton.Connect("pressed", this, nameof(OnContinuePressed));
        
        // Ensure this control can receive input
        SetProcessInput(true);
        
        // Allow processing when paused
        PauseMode = PauseModeEnum.Process;
        
        // Hide by default
        Visible = false;
    }
    
    public override void _Input(InputEvent @event)
    {
        if (!Visible) return;
        
        // Only handle keyboard input here, mouse clicks are handled by the button
        if (@event is InputEventKey keyEvent && keyEvent.Pressed)
        {
            if (keyEvent.Scancode == (uint)KeyList.Space || keyEvent.Scancode == (uint)KeyList.Enter)
            {
                OnContinuePressed();
            }
        }
    }
    
    public void ShowInteraction(NPC npc, string lastScene = "")
    {
        this.npcName = npc.NPCName;
        this.dialogueLines = new List<string>(npc.DialogueLines);
        this.characterSprite = npc.GetNode<AnimatedSprite>("CharacterDisplay/AnimatedSprite");
        
        currentLineIndex = 0;
        
        // Set up the display
        nameLabel.Text = npcName;
        
        ShowCurrentLine();
        
        // Show the screen
        Visible = true;
        
        // Pause the game
        GetTree().Paused = true;
    }
    
    private void ShowCurrentLine()
    {
        if (currentLineIndex < dialogueLines.Count)
        {
            dialogueText.BbcodeText = dialogueLines[currentLineIndex];
            
            // Update click indicator
            if (currentLineIndex < dialogueLines.Count - 1)
            {
                clickIndicator.Text = "Click to continue...";
                continueButton.Text = "Continue";
            }
            else
            {
                clickIndicator.Text = "Click to close";
                continueButton.Text = "Close";
            }
        }
    }
    
    private void OnContinuePressed()
    {
        currentLineIndex++;
        
        if (currentLineIndex < dialogueLines.Count)
        {
            ShowCurrentLine();
        }
        else
        {
            // End interaction
            CloseInteraction();
        }
    }
    
    private void CloseInteraction()
    {
        this.QueueFree();
        
        GetTree().Paused = false;
    }
    
    [Signal]
    public delegate void interaction_completed(string npcName);
}