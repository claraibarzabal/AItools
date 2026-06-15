# AItools

## Tools Installed

* Cursor IDE
* Claude Code extension
* Codex extension
* Git

## Steps Completed

### 1. Installed Cursor IDE

I downloaded Cursor from cursor.com and installed it on my Mac by dragging the application into the Applications folder.

### 2. Installed AI Coding Extensions

Using the Extensions panel in Cursor (Cmd + Shift + X), I searched for and installed the Claude Code and Codex extensions.

### 3. Created a Public GitHub Repository

I created a public GitHub repository named **AItools**.

### 4. Installed and Configured Git

I installed Apple's Developer Tools, which included Git, verified the installation, and configured my Git username and email.

### 5. Cloned the Repository

I cloned the repository locally by navigating to the Documents directory and running:

```bash
git clone https://github.com/claraibarzabal/AItools.git
```

### 6. Opened the Repository in Cursor

I opened the AItools repository in Cursor using **File → Open Folder**.

### 7. Created the README File

I created a README.md file documenting the tools installed, the setup process, and the issues encountered during the configuration.

### 8. Committed and Pushed Changes

After completing the setup, I committed my changes and pushed them to the GitHub repository.

## Issues Encountered and Solutions

### Cursor Installation

Initially, I expected the .dmg file to install Cursor automatically when opened. After troubleshooting, I realized that on macOS applications must be manually dragged into the Applications folder. Once I completed this step, Cursor installed successfully.

### Git Installation

When attempting to use Git, I discovered it was not installed on my machine. macOS prompted me to install Apple's Developer Tools. After completing the installation and configuring my Git credentials, I was able to clone the repository and continue the setup process.

### GitHub Synchronization Conflict

When I created the GitHub repository, it already contained a README file generated on GitHub. Later, I created and modified a local README file with different content. When I attempted to push my changes, Git detected that both the local and remote repositories contained changes to the same file and prevented the push.

To resolve the issue, I pulled the remote changes, reviewed the merge conflict in the README file, combined the content appropriately, and then committed and pushed the final version to GitHub.
