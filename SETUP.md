# 🚀 Dynamic GitHub Profile README

A race-condition-free system that automatically generates and updates your GitHub profile README with real data from your repositories, activity, and contributions.

## ✨ Features

- 🔄 **Automatic Updates** - Updates every 6 hours via GitHub Actions
- 🎯 **3D Contribution Graph** - Beautiful 3D visualization of your coding activity
- 📊 **Dynamic Metrics** - Real-time GitHub statistics and achievements
- ⚡ **Zero Configuration** - Works out of the box with GitHub's built-in token
- 🔒 **Race-Condition-Free** - Atomic operations prevent conflicts
- 🎨 **Fully Customizable** - Easy theming and personalization

## 🚀 Quick Setup

### 1. **Fork or Use as Template**
- Fork this repository to your GitHub account
- Rename it to match your username (e.g., `your-username/your-username`)

### 2. **Customize Configuration**
Edit `config.js` with your details:
```javascript
module.exports = {
  user: {
    username: 'your-username', // CHANGE THIS!
    email: 'your@email.com'
  },
  
  social: {
    linkedin: 'your-linkedin-url',
    instagram: 'your-instagram-url',
    // Add your social links
  },
  
  theme: {
    primaryColor: '58A6FF', // Your signature color
    backgroundColor: '0D1117',
    textColor: 'C3D1D9'
  }
};
```

### 3. **Test Locally (Optional)**
```bash
npm run generate
```

### 4. **Deploy**
```bash
git add .
git commit -m "🚀 Setup dynamic README"
git push
```

That's it! Your README will automatically update every 6 hours.

## 🎯 What Gets Generated

### **Dynamic Content**
- **Profile Information** - Your real GitHub profile data
- **Repository Analysis** - Your most active projects and languages
- **Recent Activity** - Latest commits, PRs, and contributions
- **Starred Repositories** - Repos you've recently starred
- **Tech Stack** - Generated from your actual code languages

### **Visual Elements**
- **3D Contribution Graph** - Interactive coding activity visualization
- **GitHub Metrics** - Comprehensive stats and achievements
- **Language Charts** - Real language usage breakdown
- **Activity Timeline** - Recent contribution history

## 🛠️ Available Commands

| Command | Description |
|---------|-------------|
| `npm run generate` | Generate README locally |
| `npm run clean` | Clean cache and temporary files |
| `npm run test` | Test generation |
| `npm run dev` | Development mode |

## 🎨 Customization

### **Theme Colors**
Update colors in `config.js`:
```javascript
theme: {
  primaryColor: '58A6FF',    // Main accent color
  backgroundColor: '0D1117', // Dark background
  textColor: 'C3D1D9'       // Text color
}
```

### **Layout Changes**
Edit `README.gtpl` to modify the layout and add new sections.

### **Update Frequency**
Change the schedule in `.github/workflows/update-readme.yml`:
```yaml
schedule:
  - cron: '0 */6 * * *'  # Every 6 hours
```

## 🔄 How It Works

1. **GitHub Actions** triggers every 6 hours or on push
2. **Data Fetching** - Collects your GitHub data via public API
3. **3D Graph Generation** - Creates beautiful contribution visualization
4. **Template Processing** - Generates README from template with real data
5. **Atomic Update** - Safely commits changes to your repository

## 🚨 Troubleshooting

### **README not updating?**
- Check the Actions tab for workflow status
- Ensure GitHub Actions are enabled for your repository
- Verify the workflow file is in `.github/workflows/`

### **Missing data?**
- The system uses GitHub's public API with rate limiting
- Some data may be cached and update with a delay
- Private repository data requires authentication

### **Customization issues?**
- Ensure `config.js` has valid JavaScript syntax
- Check that all required fields are present
- Test locally with `npm run generate`

## 📚 File Structure

```
📦 your-username/
├── 📁 .github/workflows/
│   └── 📄 update-readme.yml    # GitHub Actions workflow
├── 📁 scripts/
│   └── 📄 readme-generator.js  # Main generator script
├── 📄 config.js                # Your configuration
├── 📄 README.gtpl              # README template
├── 📄 README.md                # Generated README (this file)
└── 📄 package.json             # Project configuration
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Make your changes
4. Test with `npm run generate`
5. Submit a pull request

---

<div align="center">

**🎉 Made with ❤️ for the GitHub community**

*Star this repository if you find it useful!*

</div>