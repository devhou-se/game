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
    private SpriteFrames npcSpriteFrames;
    
    public override void _Ready()
    {
        dialogueText = GetNode<RichTextLabel>("DialogueBox/DialogueText");
        nameLabel = GetNode<Label>("CharacterDisplay/NameLabel");
        characterSprite = GetNode<AnimatedSprite>("CharacterDisplay/AnimatedSprite");
        continueButton = GetNode<Button>("DialogueBox/ContinueButton");
        clickIndicator = GetNode<Label>("DialogueBox/ClickIndicator");
        
        continueButton.Connect("pressed", this, nameof(OnContinuePressed));
        
        // Hide by default
        Visible = false;
    }
    
    public override void _Input(InputEvent @event)
    {
        if (!Visible) return;
        
        // Allow clicking anywhere or pressing space/enter to continue
        if (@event is InputEventMouseButton mouseEvent && mouseEvent.Pressed && mouseEvent.ButtonIndex == 1)
        {
            OnContinuePressed();
        }
        else if (@event is InputEventKey keyEvent && keyEvent.Pressed)
        {
            if (keyEvent.Scancode == (uint)KeyList.Space || keyEvent.Scancode == (uint)KeyList.Enter)
            {
                OnContinuePressed();
            }
        }
    }
    
    public void ShowInteraction(string npcName, List<string> dialogue, SpriteFrames spriteFrames = null)
    {
        this.npcName = npcName;
        this.dialogueLines = new List<string>(dialogue);
        this.npcSpriteFrames = spriteFrames;
        currentLineIndex = 0;
        
        // Set up the display
        nameLabel.Text = npcName;
        
        if (spriteFrames != null)
        {
            characterSprite.Frames = spriteFrames;
        }
        
        // Show first line
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
        Visible = false;
        GetTree().Paused = false;
        
        // Emit signal that interaction is complete
        EmitSignal("interaction_completed", npcName);
    }
    
    [Signal]
    public delegate void interaction_completed(string npcName);
}