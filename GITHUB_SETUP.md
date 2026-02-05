# GitHub Repository Setup

## Quick Start

1. **Create a new repository on GitHub:**
   - Go to https://github.com/new
   - Repository name: `dnd-vtt` (or your preferred name)
   - Description: "D&D 5e Virtual Tabletop - Real-time web app for remote D&D sessions"
   - Set to Public or Private as desired
   - **Do NOT** initialize with README, .gitignore, or license (we already have these)
   - Click "Create repository"

2. **Link your local repository to GitHub:**
   ```bash
   # Add the remote (replace YOUR_USERNAME with your GitHub username)
   git remote add origin https://github.com/YOUR_USERNAME/dnd-vtt.git

   # Verify the remote was added
   git remote -v

   # Push your code to GitHub
   git push -u origin master
   ```

3. **Verify the push:**
   - Go to your repository URL on GitHub
   - You should see all your code, README, and commit history

## Alternative: Using GitHub CLI (gh)

If you have the GitHub CLI installed:

```bash
# Create repo and push in one command
gh repo create dnd-vtt --public --source=. --remote=origin --push
```

## Future Commits

After the initial setup, you can push changes with:

```bash
git add .
git commit -m "Your commit message"
git push
```

## Collaboration

To collaborate with others:

1. Add collaborators in repository Settings > Collaborators
2. Team members can clone with: `git clone https://github.com/YOUR_USERNAME/dnd-vtt.git`
3. They can make changes and push to the repository
