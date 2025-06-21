using System;
using System.Collections.Generic;
using Godot;

namespace DevHouse
{
    [Serializable]
    public class DialogueNode
    {
        public string Id { get; set; }
        public string Text { get; set; }
        public List<DialogueChoice> Choices { get; set; }
        public string NextNodeId { get; set; }
        public bool IsEndNode { get; set; }
        
        public DialogueNode()
        {
            Choices = new List<DialogueChoice>();
        }
    }
    
    [Serializable]
    public class DialogueChoice
    {
        public string Text { get; set; }
        public string NextNodeId { get; set; }
        public string RequiredFlag { get; set; }
        public string SetFlag { get; set; }
    }
    
    [Serializable]
    public class DialogueTree
    {
        public string StartNodeId { get; set; }
        public Dictionary<string, DialogueNode> Nodes { get; set; }
        
        public DialogueTree()
        {
            Nodes = new Dictionary<string, DialogueNode>();
        }
        
        public DialogueNode GetNode(string nodeId)
        {
            return Nodes.ContainsKey(nodeId) ? Nodes[nodeId] : null;
        }
        
        public static DialogueTree CreateSimpleTree(string[] dialogueLines)
        {
            var tree = new DialogueTree();
            
            for (int i = 0; i < dialogueLines.Length; i++)
            {
                var nodeId = $"node_{i}";
                var node = new DialogueNode
                {
                    Id = nodeId,
                    Text = dialogueLines[i],
                    IsEndNode = i == dialogueLines.Length - 1
                };
                
                if (i < dialogueLines.Length - 1)
                {
                    node.NextNodeId = $"node_{i + 1}";
                }
                
                tree.Nodes[nodeId] = node;
                
                if (i == 0)
                {
                    tree.StartNodeId = nodeId;
                }
            }
            
            return tree;
        }
    }
    
    public class DialogueManager
    {
        private DialogueTree currentTree;
        private DialogueNode currentNode;
        private HashSet<string> dialogueFlags;
        
        public DialogueManager()
        {
            dialogueFlags = new HashSet<string>();
        }
        
        public void StartDialogue(DialogueTree tree)
        {
            currentTree = tree;
            currentNode = tree.GetNode(tree.StartNodeId);
        }
        
        public DialogueNode GetCurrentNode()
        {
            return currentNode;
        }
        
        public List<DialogueChoice> GetAvailableChoices()
        {
            if (currentNode == null || currentNode.Choices == null)
                return new List<DialogueChoice>();
                
            var availableChoices = new List<DialogueChoice>();
            
            foreach (var choice in currentNode.Choices)
            {
                if (string.IsNullOrEmpty(choice.RequiredFlag) || dialogueFlags.Contains(choice.RequiredFlag))
                {
                    availableChoices.Add(choice);
                }
            }
            
            return availableChoices;
        }
        
        public bool AdvanceDialogue(int choiceIndex = -1)
        {
            if (currentNode == null || currentTree == null)
                return false;
                
            string nextNodeId = null;
            
            if (currentNode.Choices != null && currentNode.Choices.Count > 0 && choiceIndex >= 0)
            {
                var availableChoices = GetAvailableChoices();
                if (choiceIndex < availableChoices.Count)
                {
                    var selectedChoice = availableChoices[choiceIndex];
                    
                    if (!string.IsNullOrEmpty(selectedChoice.SetFlag))
                    {
                        dialogueFlags.Add(selectedChoice.SetFlag);
                    }
                    
                    nextNodeId = selectedChoice.NextNodeId;
                }
            }
            else if (!string.IsNullOrEmpty(currentNode.NextNodeId))
            {
                nextNodeId = currentNode.NextNodeId;
            }
            
            if (!string.IsNullOrEmpty(nextNodeId))
            {
                currentNode = currentTree.GetNode(nextNodeId);
                return currentNode != null;
            }
            
            return false;
        }
        
        public bool IsDialogueComplete()
        {
            return currentNode == null || currentNode.IsEndNode;
        }
        
        public void SetFlag(string flag)
        {
            dialogueFlags.Add(flag);
        }
        
        public bool HasFlag(string flag)
        {
            return dialogueFlags.Contains(flag);
        }
    }
}