# 🚀 Dynamic GitHub README - No JavaScript!

**Zero dependencies, pure GitHub Actions approach!**

## ✨ What's Different

- 🚫 **No JavaScript** - No Node.js, no dependencies, no build steps
- 🚀 **Pure GitHub Actions** - Uses only marketplace actions and shell scripts  
- ⚡ **Super Fast** - Generates in under 2 minutes
- 🔧 **Fully Dynamic** - Auto-detects everything from GitHub context
- 🎛️ **Environment Configurable** - Customize via repository variables

## 🛠️ Quick Setup (2 Minutes)

### 1. **Use This Template**
```bash
# Option A: Use as template on GitHub (recommended)
# Option B: Fork this repository  
# Option C: Copy files to your username/username repository
```

### 2. **Rename Repository** 
Rename your repository to match your GitHub username:
- Repository name: `your-username` (same as your GitHub username)
- This will make it your GitHub profile README

### 3. **Configure (Optional)**
Go to **Settings → Secrets and variables → Actions → Variables** and add any of these:

| Variable | Example | Purpose |
|----------|---------|---------|
| `USER_EMAIL` | `your@email.com` | Contact email |
| `LINKEDIN_URL` | `https://linkedin.com/in/yourname` | LinkedIn profile |
| `TWITTER_URL` | `https://twitter.com/yourhandle` | Twitter profile |  
| `INSTAGRAM_URL` | `https://instagram.com/yourhandle` | Instagram profile |
| `YOUTUBE_URL` | `https://youtube.com/@yourchannel` | YouTube channel |
| `THEME_PRIMARY_COLOR` | `58A6FF` | Main accent color (hex) |
| `THEME_BG_COLOR` | `0D1117` | Background color (hex) |
| `USER_TAGLINE` | `Building the future` | Your tagline |
| `USER_QUOTE` | `Code is art` | Inspirational quote |

**Note:** All variables are optional! The system auto-detects everything it can from your GitHub profile.

### 4. **Push and Go!**
```bash
git add .
git commit -m "🚀 Setup dynamic README"
git push origin main
```

That's it! Your README will automatically:
- Update every 6 hours
- Show your latest repos, languages, and activity  
- Display beautiful 3D contribution graphs
- Include GitHub metrics and stats
- Work with any GitHub username - no hardcoding!

## 🎯 How It Works

### Pure GitHub Actions Magic:
1. **Auto-Detection** - Gets your username from repository context
2. **GitHub API Calls** - Uses GitHub CLI to fetch your profile data
3. **Template Processing** - Replaces variables in `README.gtpl` with real data
4. **Action Integrations** - Generates 3D graphs and metrics using marketplace actions
5. **Smart Updates** - Only commits when there are actual changes

### No JavaScript Required:
- ✅ Shell scripting for data processing
- ✅ GitHub CLI (`gh`) for API calls
- ✅ Marketplace actions for visualizations
- ✅ `sed`/`awk` for template processing
- ❌ No Node.js, npm, or dependencies

## 🎨 Customization

### Theme Colors
Set these repository variables:
- `THEME_PRIMARY_COLOR=FF6B6B` (red theme)
- `THEME_BG_COLOR=1A1A1A` (dark background)  
- `THEME_TEXT_COLOR=FFFFFF` (white text)

### Custom Messages
- `USER_TAGLINE=Your custom tagline here`
- `USER_QUOTE=Your inspirational quote`
- `CONTACT_MESSAGE=Your contact message`

### Content Limits
- `MAX_REPOS=8` (number of repos to show)
- `MAX_LANGUAGES=10` (number of languages to show)

## 🔄 Updates

### Automatic (Recommended)
- **Every 6 hours** via scheduled workflow
- **On template changes** when you push updates
- **Manual trigger** from Actions tab

### Manual Update
Go to **Actions** → **Dynamic README (No JavaScript!)** → **Run workflow**

## 🚨 Troubleshooting

### README not updating?
1. Check **Actions** tab for workflow status
2. Make sure repository name matches your username
3. Verify Actions are enabled in Settings

### Want to customize the template?
Edit `README.gtpl` and push - it will auto-update on the next run.

### Missing data?
The system auto-detects most things from your GitHub profile. Make sure your GitHub profile is public and complete.

## 📁 File Structure

```
your-username/           # Repository name = your GitHub username
├── README.gtpl         # Template file (edit this to customize)
├── README.md           # Generated file (don't edit directly)
├── .github/workflows/
│   └── update-readme.yml  # GitHub Actions workflow
├── package.json        # Minimal package info (no dependencies)
└── SETUP.md           # This setup guide
```

## 🎯 What Gets Generated

- **Profile Header** - Your name, bio, and avatar
- **Typing Animation** - Dynamic taglines based on your profile
- **Profile Stats** - Followers, repos, coding since date
- **3D Contribution Graph** - Beautiful 3D visualization
- **GitHub Metrics** - Comprehensive stats and achievements  
- **Top Languages** - Chart of your most used languages
- **Recent Activity** - Latest commits and contributions
- **Social Links** - Based on your profile and variables

## 🚀 Migration from Complex Setups

Moving from JavaScript-based generators?

1. **Backup** your current README.md
2. **Copy** this repository's files
3. **Move** any custom content to `README.gtpl`
4. **Set** repository variables for customization
5. **Push** and let GitHub Actions handle the rest!

---

<div align="center">

**🎉 No JavaScript, No Dependencies, No Problems!**

*⭐ Star this repository if you find it useful!*

</div>
