# Git Guide for Non-Technical Team Members

## Initial Setup (One Time Only)

1. **Install Git**
   - Windows: Download from https://git-scm.com
   - Mac: Install via Homebrew or download from git-scm.com
   - Linux: `sudo apt-get install git`

2. **Configure Your Identity**
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

3. **Clone the Repository**
   ```bash
   git clone https://github.com/devhou-se/game.git
   cd game
   ```

## Daily Workflow

### Starting Your Work Day

1. **Always start by getting latest changes:**
   ```bash
   git pull
   ```

2. **Check what branch you're on:**
   ```bash
   git branch
   ```
   You should see `* master`

### While Working

Work in your team folder:
- Artists → `TeamFolders/Art/`
- Musicians → `TeamFolders/Audio/`
- Designers → `TeamFolders/Design/`

### Saving Your Work

1. **See what files you've changed:**
   ```bash
   git status
   ```

2. **Add your changes:**
   ```bash
   # Add everything
   git add .
   
   # Or add specific files
   git add TeamFolders/Art/my_sprite.png
   ```

3. **Commit with a message:**
   ```bash
   git commit -m "Added new player walk animation"
   ```

4. **Push to GitHub:**
   ```bash
   git push
   ```

## Common Scenarios

### "It says I have conflicts!"

Don't panic! This means someone else changed the same file.

1. **Get help from tech team**, or:
2. **If it's your file in your team folder:**
   ```bash
   # Save your version somewhere safe first!
   cp your_file.png your_file_backup.png
   
   # Get their version
   git pull
   
   # Now manually merge or choose which version to keep
   ```

### "I messed up and want to start over"

```bash
# Discard all local changes (CAREFUL - this deletes your work!)
git reset --hard HEAD

# Get latest from GitHub
git pull
```

### "I accidentally deleted a file"

```bash
# Restore a deleted file
git checkout -- path/to/deleted/file.png
```

### "I want to see what changed"

```bash
# See all recent commits
git log --oneline -10

# See what files changed
git diff --name-only
```

## Visual Git Tools (Easier!)

Instead of command line, you can use:

- **GitHub Desktop** (Recommended for beginners)
  - Download: https://desktop.github.com
  - Visual interface for all git operations
  
- **SourceTree**
  - Download: https://www.sourcetreeapp.com
  - More advanced but still visual

- **VS Code** 
  - Has built-in git support
  - Great for text files and code

## Git Best Practices

### DO:
- ✅ Pull before starting work
- ✅ Commit often with clear messages
- ✅ Work in your team folder
- ✅ Ask for help if confused
- ✅ Keep files organized

### DON'T:
- ❌ Commit huge files (>100MB)
- ❌ Delete other people's work
- ❌ Work directly in Assets/ folder
- ❌ Force push (unless you know what you're doing)
- ❌ Panic - everything can be fixed!

## Quick Command Reference

| What you want | Command |
|--------------|---------|
| Get latest changes | `git pull` |
| See what you changed | `git status` |
| Save your work | `git add .` then `git commit -m "message"` |
| Send to GitHub | `git push` |
| See history | `git log --oneline` |
| Undo changes | `git checkout -- filename` |
| See current branch | `git branch` |

## Getting Help

1. **In-team help:**
   - Post in #help channel
   - Tag @tech-team
   - Share your `git status` output

2. **Error messages:**
   - Copy the full error
   - Don't try random commands
   - Ask before using `--force`

## Common Error Messages Explained

**"Your branch is behind"**
- Meaning: GitHub has new changes
- Fix: `git pull`

**"Please commit your changes or stash them"**
- Meaning: You have unsaved changes
- Fix: Either `git commit` or `git stash`

**"Permission denied"**
- Meaning: You don't have access
- Fix: Check you're logged in to GitHub

**"Merge conflict"**
- Meaning: Two people changed the same file
- Fix: Get help or manually resolve

Remember: Version control means we can always recover from mistakes. Don't be afraid to ask for help!