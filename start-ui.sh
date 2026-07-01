#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# Load nvm if available
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
if [ -s "$NVM_DIR/nvm.sh" ]; then
    source "$NVM_DIR/nvm.sh"
    nvm use 20 2>/dev/null || nvm install 20
fi

# Check Node version >= 20
NODE_MAJOR=$(node -e "process.stdout.write(process.versions.node.split('.')[0])" 2>/dev/null || echo "0")
if [ "$NODE_MAJOR" -lt 20 ]; then
    echo "[error] Node.js >= 20 is required (found: $(node --version 2>/dev/null || echo 'none'))"
    echo "  Install nvm: curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash"
    echo "  Then: nvm install 20"
    exit 1
fi

cd "$FRONTEND_DIR"

# Install dependencies if node_modules is missing
if [ ! -d "node_modules" ]; then
    echo "[setup] Installing frontend dependencies..."
    npm install
fi

# Kill anything already on port 3001
echo "[setup] Freeing port 3001..."
fuser -k 3001/tcp 2>/dev/null || true
# fallback: lsof-based kill if fuser is unavailable
if lsof -ti :3001 &>/dev/null 2>&1; then
    lsof -ti :3001 | xargs kill -9 2>/dev/null || true
fi
sleep 1

echo ""
echo "  HireX UI starting..."
echo "  App:  http://localhost:3001"
echo ""

exec npm run dev
