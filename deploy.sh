#!/bin/bash
# Quick deployment script for Render

echo "🚀 Deploying Pantry Pulse to Production"
echo ""

# Check if render CLI is installed
if ! command -v render &> /dev/null; then
    echo "⚠️  Render CLI not found. Installing..."
    npm install -g @render-cli/cli
fi

echo "📋 Deployment Checklist:"
echo "  [ ] Google AI Studio API key ready"
echo "  [ ] GitHub repo pushed to main"
echo "  [ ] CORS origins updated in backend/app/main.py"
echo ""

read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

echo ""
echo "🔧 Next steps:"
echo "1. Go to https://dashboard.render.com"
echo "2. Click 'New +' → 'Blueprint'"
echo "3. Connect this repo: https://github.com/Monal06/pantry-pulse-orchestrator"
echo "4. Render will auto-detect render.yaml and deploy both services"
echo "5. Add environment variables in the dashboard:"
echo "   - GEMINI_API_KEY"
echo "   - VITE_API_URL (for frontend)"
echo ""
echo "✅ Your app will be live at:"
echo "   Backend:  https://pantry-pulse-api.onrender.com"
echo "   Frontend: https://pantry-pulse-web.onrender.com"
echo ""

