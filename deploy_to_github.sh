#!/bin/bash

# 🚀 Script to deploy the app to GitHub for Streamlit Cloud deployment

echo "🚀 Preparing to deploy Job Description Card System to GitHub (form-filter repository)..."

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📁 Initializing git repository..."
    git init
fi

# Check if remote origin exists
if ! git remote get-url origin > /dev/null 2>&1; then
    echo "🔗 Please add your GitHub repository as remote origin:"
    echo "   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git"
    echo ""
    echo "   Replace YOUR_USERNAME and YOUR_REPO_NAME with your actual GitHub details"
    echo ""
    read -p "Press Enter after you've added the remote origin..."
fi

# Add all files
echo "📦 Adding all files to git..."
git add .

# Commit changes
echo "💾 Committing changes..."
git commit -m "Deploy Job Description Card System for Streamlit Cloud"

# Push to GitHub
echo "🚀 Pushing to GitHub..."
git push -u origin main

echo ""
echo "✅ Successfully pushed to GitHub!"
echo ""
echo "🌐 Next steps for Streamlit Cloud deployment:"
echo "1. Go to https://share.streamlit.io/deploy"
echo "2. Sign in with your GitHub account"
echo "3. Select your repository"
echo "4. Set Main file path to: app.py"
echo "5. Click Deploy!"
echo ""
echo "🔐 After deployment, add your OpenAI API key in Streamlit Cloud:"
echo "   - Go to your app settings"
echo "   - Click on 'Secrets'"
echo "   - Add: OPENAI_API_KEY = 'your-actual-api-key'"
echo ""
echo "🎉 Your app will be available online!"
