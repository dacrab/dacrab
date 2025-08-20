/**
 * 🎯 GitHub Profile README Configuration
 * Redesigned based on ChrisTitusTech's functional approach
 */

export default {
  // 👤 Personal Information
  profile: {
    username: 'dacrab', // Your GitHub username
    name: '', // Leave empty to auto-fetch from GitHub
    bio: '', // Leave empty to auto-fetch from GitHub  
    location: '', // Leave empty to auto-fetch from GitHub
    company: '', // Leave empty to auto-fetch from GitHub
    website: '', // Leave empty to auto-fetch from GitHub
    email: 'vkavouras@proton.me',
  },

  // 🌐 Social Links
  social: {
    linkedin: 'https://www.linkedin.com/in/vkavouras/',
    instagram: 'https://www.instagram.com/killcrb/',
    twitter: '', // Leave empty if you don't have one
    youtube: '',
    discord: '',
    email: 'mailto:vkavouras@proton.me'
  },

  // 🎨 Visual Theme  
  theme: {
    primaryColor: '58A6FF',
    backgroundColor: '0D1117', 
    textColor: 'C3D1D9',
    accentColor: 'FF6B6B'
  },

  // 💬 Custom Messages
  messages: {
    tagline: 'Building amazing projects with modern technologies',
    quote: 'Code is poetry written in logic', 
    greeting: 'Hello, I\'m',
    aboutMe: 'doin my best',
    contactMessage: 'Open to collaborations and interesting conversations!'
  },

  // 📊 Content Settings (ChrisTitusTech Style)
  content: {
    showRecentRepos: true,
    maxRepos: 5,              // Repositories in "currently working on"
    showLanguages: true, 
    maxLanguages: 8,
    showActivity: true,
    maxActivity: 5,           // Recent pull requests 
    showStarredRepos: true,
    maxStarred: 4,            // Recently starred repositories
    showStats: true,
    showTrophies: true,
    show3DContribution: true
  },

  // 📰 Blog & Content (Optional - like ChrisTitusTech)
  blog: {
    enabled: false,           // Set to true if you have a blog
    rssUrl: '',              // Your RSS feed URL
    maxPosts: 5              // Number of recent blog posts to show
  },

  // 🔧 Advanced Options
  advanced: {
    includePrivateContributions: true,
    excludeForkedRepos: false,
    excludeArchivedRepos: true,
    sortReposBy: 'updated', // 'updated', 'stars', 'created'
    cacheResults: true,
    cacheDurationMinutes: 30
  }
};

/*
 * 🎯 ChrisTitusTech Style Features:
 * 
 * ✅ What I'm currently working on (repos with recent activity)
 * ✅ My latest projects (newest repositories)
 * ✅ Recent Pull Requests (across all repos)
 * ✅ Recent Stars (repositories you've starred)
 * ✅ Technologies & Tools (language badges)
 * ✅ Social Links (clean badge format)
 * ✅ GitHub Stats (comprehensive metrics)
 * ✅ 3D Contribution Graph
 * 
 * 💡 Quick Setup:
 * 1. Update 'username' above to match your GitHub username
 * 2. Add your social links and email  
 * 3. Customize your theme colors
 * 4. Run: npm run generate
 * 
 * 🚀 All sections now work like ChrisTitusTech's profile!
 */