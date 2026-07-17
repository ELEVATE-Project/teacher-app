#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "==================================================="
echo "  Chanakya Frontend Setup Assistant (Unix/macOS)  "
echo "==================================================="
echo

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js is not installed or not in your PATH."
    echo "Please install Node.js (v18 or higher) from https://nodejs.org/"
    exit 1
fi

NODE_VER=$(node -v)
echo "[*] Found Node.js: $NODE_VER"

# Check for npm
if ! command -v npm &> /dev/null; then
    echo "[ERROR] npm is not installed or not in your PATH."
    exit 1
fi

NPM_VER=$(npm -v)
echo "[*] Found npm: $NPM_VER"
echo

# Check for root .env
echo "[*] Checking environment configuration..."
ROOT_ENV="../../.env"
ROOT_ENV_EXAMPLE="../../.env.example"

if [ ! -f "$ROOT_ENV" ]; then
    if [ -f "$ROOT_ENV_EXAMPLE" ]; then
        echo "[!] .env file not found at workspace root."
        echo "[*] Copying .env.example to .env at workspace root..."
        cp "$ROOT_ENV_EXAMPLE" "$ROOT_ENV"
        echo "[SUCCESS] Created .env file from template. Please update the API keys in the root .env file."
    else
        echo "[!] Neither .env nor .env.example found at workspace root."
        echo "[*] Creating a basic .env file at workspace root..."
        cat <<EOT > "$ROOT_ENV"
# Frontend API Configurations
VITE_API_URL=http://localhost:3000
VITE_FEEDBACK_BACKEND_URL=http://localhost:3000
VITE_SARVAM_API_KEY=your_sarvam_api_key_here
EOT
        echo "[SUCCESS] Created a default .env file."
    fi
else
    echo "[*] .env file found at workspace root."
fi
echo

# Install dependencies
echo "[*] Installing frontend dependencies (npm install)..."
echo
npm install

echo
echo "==================================================="
echo "[SUCCESS] Frontend setup completed successfully!"
echo "==================================================="
echo
echo "To start the development server, run:"
echo "  npm run dev"
echo
echo "The frontend will be available at:"
echo "  http://localhost:5173"
echo
