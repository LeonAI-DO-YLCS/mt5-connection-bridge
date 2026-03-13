#!/usr/bin/env bash
# init-workspace.sh - Runs on container creation to setup the bare repo and worktree

WORKSPACE_DIR="/workspace"
BARE_REPO="main.git"
DEFAULT_BRANCH="main"
REMOTE_URL="https://github.com/LeonAI-DO-YLCS/mt5-connection-bridge.git"

cd "$WORKSPACE_DIR" || exit 1

# Check if bare repo already exists (e.g., container restart)
if [ -d "$BARE_REPO" ]; then
    echo "Bare repository already exists. Skipping initialization."
    exit 0
fi

echo "Checking SSH connectivity to GitHub..."
# Try to connect, but don't fail the script if it doesn't work.
if ssh -T git@github.com 2>&1 | grep -q 'successfully authenticated'; then
    echo "SSH connection successful."
else
    echo "⚠️ Warning: SSH connection failed or your key is not loaded."
    echo "If git clone fails, ensure your ssh-agent is running on the host and the key is added."
    echo "Host command: eval \$(ssh-agent) && ssh-add ~/.ssh/id_ed25519"
fi

echo "Cloning bare repository..."
git clone --bare "$REMOTE_URL" "$BARE_REPO" || {
    echo "❌ Git clone failed. Container will continue starting, but you must manually clone:"
    echo "cd $WORKSPACE_DIR && git clone --bare $REMOTE_URL $BARE_REPO"
    exit 0
}

cd "$BARE_REPO" || exit 1

# Configure Git Identity
git config user.name "LeonAI-DO"
git config user.email "yensileonel@gmail.com"

echo "Setting up default worktree for $DEFAULT_BRANCH..."
git worktree add "$WORKSPACE_DIR/$DEFAULT_BRANCH" "$DEFAULT_BRANCH"

echo "✅ Workspace initialization complete."
echo "VS Code should automatically open $WORKSPACE_DIR/$DEFAULT_BRANCH"
