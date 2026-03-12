#!/bin/bash

# Team Risk Analysis Dashboard - Demo Startup Script

echo "🚀 Starting Team Risk Analysis Dashboard Demo..."
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    echo ""
fi

echo "✅ Starting development server..."
echo "📊 Dashboard will be available at: http://localhost:3000"
echo "🎭 Demo mode is enabled by default (using mock data)"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

npm run dev
