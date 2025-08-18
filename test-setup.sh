#!/bin/bash

# 🧪 Test GitHub Actions Setup
echo "🚀 Testing GitHub Actions setup..."
echo ""

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not in a git repository"
    exit 1
else
    echo "✅ Git repository detected"
fi

# Check for required files
echo ""
echo "📁 Checking required files:"

files=(
    ".github/workflows/update-readme.yml"
    "README.template.md"
    "config.js"
    "package.json"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (missing)"
    fi
done

echo ""
echo "🔐 GitHub Secrets needed:"
echo "   1. Go to: Repository Settings → Secrets and variables → Actions"
echo "   2. Add secret: GITHUB_TOKEN (required)"
echo "   3. Add secret: WAKATIME_API_KEY (optional)"
echo ""

echo "🧪 To test the workflow:"
echo "   1. Push these changes to GitHub"
echo "   2. Go to Actions tab in your repository" 
echo "   3. Manually trigger 'Update Dynamic README' workflow"
echo "   4. Check if it runs successfully"
echo ""

echo "📚 Full setup guide: SETUP.md"
