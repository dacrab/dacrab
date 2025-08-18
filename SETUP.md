# 🚀 Dynamic README Setup Guide

This repository uses a modern, automated system to keep your GitHub profile README fresh and up-to-date!

## ✨ What's New

### 🔄 **Automated Updates**
- Updates every 6 hours automatically via GitHub Actions
- No more manual script running required!

### 🎨 **Modern Design**  
- Clean, organized layout with proper sections
- Beautiful badges and dynamic visual elements
- Mobile-responsive design

### 🛠️ **Modular Architecture**
- Centralized configuration in `config.js`
- Improved error handling and caching
- Fallback mechanisms for API failures

### 📊 **Rich Dynamic Content**
- Real-time GitHub statistics and activity
- WakaTime coding time tracking
- Recent blog posts from dev.to
- Automatic metrics generation

## 🛠️ Quick Setup

### 1. **Zero Configuration Required!**

The workflow uses GitHub's built-in `GITHUB_TOKEN` automatically - **no secrets or setup needed!**

🎉 **Ready to use out of the box!**

### 2. **Run Setup Script**

```bash
npm run setup
```

This will validate your configuration and check all requirements.

### 3. **Customize Your Profile**

Edit `config.js` to personalize:
- Your information and social links
- Featured projects
- Skills and technologies
- Theme colors

### 4. **Deploy**

Simply push to your repository:

```bash
git add .
git commit -m "🚀 Setup dynamic README system"
git push
```

The GitHub Actions workflow will automatically run and update your README!

## 📁 Project Structure

```
📦 dacrab/
├── 📁 .github/workflows/
│   └── 📄 update-readme.yml          # GitHub Actions workflow
├── 📁 scripts/
│   ├── 📄 readme-generator.js        # Main generation script
│   └── 📄 setup.js                   # Setup validation script
├── 📄 config.js                      # Centralized configuration
├── 📄 README.template.md             # README template
├── 📄 package.json                   # Project configuration
└── 📄 SETUP.md                       # This file
```

## 🎛️ Configuration Options

### **Personal Information**
```javascript
user: {
  username: 'dacrab',
  name: 'Vaggelis Kavouras',
  location: 'Greece 🇬🇷',
  // ... more options
}
```

### **Featured Projects**  
```javascript
featuredProjects: [
  {
    name: 'clubOS',
    description: 'Sports Facility Management System',
    url: 'https://clubos.vercel.app',
    // ... project details
  }
]
```

### **Theme Customization**
```javascript
theme: {
  primaryColor: '58A6FF',
  backgroundColor: '0D1117',
  textColor: 'C3D1D9',
  // ... color scheme
}
```

## 🔄 How It Works

1. **GitHub Actions Trigger**: Every 6 hours or on push to main branch
2. **Data Fetching**: Collects fresh data from GitHub API, WakaTime, etc.
3. **Template Processing**: Populates `README.template.md` with dynamic content
4. **Metrics Generation**: Creates beautiful SVG metrics using lowlighter/metrics
5. **Auto-Commit**: Updates the repository with fresh content

## 🎨 Dynamic Elements

- **📊 GitHub Statistics**: Real-time stats, language breakdown, contribution graphs
- **⚡ Recent Activity**: Latest commits, PRs, and repository activity


- **🏆 Achievements**: GitHub achievements and milestones

## 🛠️ Available Commands

| Command | Description |
|---------|-------------|
| `npm run setup` | Validate configuration and setup |
| `npm run clean` | Clean cache and temporary files |
| `npm test` | Show workflow status information |

## 🔧 Troubleshooting

### **README not updating?**
- Check GitHub Actions tab for workflow status
- Verify all secrets are properly configured
- Check API rate limits

### **Missing data?**
- The system uses caching and fallbacks
- Some APIs may be temporarily unavailable
- Check the Actions logs for specific errors

### **Customization help?**
- Edit `config.js` for basic changes
- Modify `README.template.md` for layout changes
- Update `.github/workflows/update-readme.yml` for workflow changes

## 📚 Additional Resources

- **GitHub Actions Documentation**: [docs.github.com/actions](https://docs.github.com/en/actions)
- **GitHub API Reference**: [docs.github.com/rest](https://docs.github.com/en/rest)
- **WakaTime API**: [wakatime.com/api](https://wakatime.com/developers)

## 💬 Support

Having issues? 
- 🐛 [Create an issue](https://github.com/dacrab/dacrab/issues)
- 💬 [Start a discussion](https://github.com/dacrab/dacrab/discussions)
- 📧 [Email me](mailto:vkavouras@proton.me)

---

<div align="center">

**🎉 Happy coding! Your profile will now stay fresh automatically! 🎉**

</div>
