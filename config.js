/**
 * 🎛️ Dynamic README Configuration
 * Race-condition-free configuration system
 */

module.exports = {
  // Core user settings - CONFIGURED ✅
  user: {
    username: 'dacrab', // ✅ Your GitHub username
    displayName: '', // Leave empty to auto-fetch from GitHub
    bio: '', // Leave empty to auto-fetch from GitHub
    location: '', // Leave empty to auto-fetch from GitHub
    email: 'vkavouras@proton.me',
    website: '', // Leave empty to auto-fetch from GitHub
  },

  // Social links (optional)
  social: {
    linkedin: 'https://www.linkedin.com/in/vkavouras/',
    instagram: 'https://www.instagram.com/killcrb/',
    twitter: '',
    email: 'mailto:vkavouras@proton.me'
  },

  // Visual theme - CONFIGURED ✅
  theme: {
    primaryColor: '58A6FF', // ✅ Your signature color
    backgroundColor: '0D1117',
    textColor: 'C3D1D9',
    accentColor: 'FF6B6B'
  },

  // Content settings
  content: {
    maxRepos: 6,
    maxLanguages: 8,
    maxActivity: 5,
    maxStarred: 6,
    showPrivateContributions: true
  },

  // Custom messages
  messages: {
    tagline: 'Building amazing projects with modern technologies',
    quote: 'Code is poetry written in logic',
    contactMessage: 'Open to collaborations and interesting conversations!',
    workingOn: 'What I\'m currently working on',
    recentStars: 'Recently starred repositories'
  }
};