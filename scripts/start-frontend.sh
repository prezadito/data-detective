#!/bin/bash
# Start frontend development server

echo "🚀 Starting Data Detective Frontend..."
echo ""

cd "$(dirname "$0")/../frontend" || exit 1

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📥 Installing dependencies..."
    pnpm install
fi

# Start the server
echo "✅ Starting dev server at http://localhost:3000"
echo ""
pnpm dev
