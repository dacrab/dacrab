const https = require('https');
const fs = require('fs');

const GITHUB_USERNAME = 'dacrab';
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;

function makeRequest(url) {
  return new Promise((resolve, reject) => {
    const options = {
      headers: {
        'User-Agent': 'Enhanced-README-Generator',
        'Authorization': `token ${GITHUB_TOKEN}`,
        'Accept': 'application/vnd.github.v3+json'
      }
    };
    
    https.get(url, options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          console.warn(`Parse error for ${url}:`, e.message);
          resolve({ error: e.message });
        }
      });
    }).on('error', reject);
  });
}

function formatTimeAgo(date) {
  const now = new Date();
  const diff = now - new Date(date);
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  const hours = Math.floor(diff / (1000 * 60 * 60));
  const minutes = Math.floor(diff / (1000 * 60));
  
  if (days > 365) return `${Math.floor(days/365)} year${Math.floor(days/365) === 1 ? '' : 's'} ago`;
  if (days > 30) return `${Math.floor(days/30)} month${Math.floor(days/30) === 1 ? '' : 's'} ago`;
  if (days > 0) return `${days} day${days === 1 ? '' : 's'} ago`;
  if (hours > 0) return `${hours} hour${hours === 1 ? '' : 's'} ago`;
  if (minutes > 0) return `${minutes} minute${minutes === 1 ? '' : 's'} ago`;
  return 'Just now';
}

function getLanguageEmoji(language) {
  const langEmojis = {
    'JavaScript': '🟨', 'TypeScript': '🔷', 'Python': '🐍', 'Java': '☕',
    'React': '⚛️', 'Vue': '💚', 'Angular': '🅰️', 'Node.js': '💚',
    'HTML': '🌐', 'CSS': '🎨', 'SCSS': '💜', 'PHP': '🐘',
    'Go': '🔵', 'Rust': '🦀', 'C++': '⚡', 'C#': '💜', 'C': '⚙️',
    'Shell': '🐚', 'Dockerfile': '🐳', 'Markdown': '📝', 'Astro': '🚀',
    'Svelte': '🧡', 'Dart': '🎯', 'Swift': '🍎', 'Kotlin': '💎'
  };
  return langEmojis[language] || '📁';
}

function getActivityEmoji(type) {
  const activityEmojis = {
    'PushEvent': '📝', 'CreateEvent': '🆕', 'IssuesEvent': '🐛',
    'PullRequestEvent': '🔀', 'WatchEvent': '⭐', 'ForkEvent': '🍴',
    'ReleaseEvent': '🎉', 'PublicEvent': '🌍'
  };
  return activityEmojis[type] || '💼';
}

async function generateReadme() {
  try {
    console.log('🚀 Fetching comprehensive GitHub data...');
    
    // Fetch multiple data sources concurrently
    const [user, repos, events, starred, pullRequests] = await Promise.all([
      makeRequest(`https://api.github.com/users/${GITHUB_USERNAME}`),
      makeRequest(`https://api.github.com/users/${GITHUB_USERNAME}/repos?sort=updated&per_page=30`),
      makeRequest(`https://api.github.com/users/${GITHUB_USERNAME}/events/public?per_page=20`),
      makeRequest(`https://api.github.com/users/${GITHUB_USERNAME}/starred?per_page=6`),
      makeRequest(`https://api.github.com/search/issues?q=author:${GITHUB_USERNAME}+type:pr&sort=updated&per_page=5`)
    ]);
    
    // Process repos data
    const activeRepos = Array.isArray(repos) 
      ? repos.filter(repo => !repo.fork && !repo.private)
          .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
      : [];
    
    const contributingRepos = Array.isArray(events)
      ? events.filter(event => event.type === 'PushEvent' && event.repo)
          .map(event => event.repo.name)
          .filter((name, index, arr) => arr.indexOf(name) === index)
          .slice(0, 5)
      : [];
    
    const recentlyUpdated = activeRepos.slice(0, 6);
    
    // Process recent activity with more detail
    const recentActivity = Array.isArray(events) 
      ? events.filter(event => ['PushEvent', 'CreateEvent', 'IssuesEvent', 'PullRequestEvent', 'WatchEvent'].includes(event.type))
          .slice(0, 6)
      : [];
    
    // Process starred repos
    const recentStars = Array.isArray(starred) ? starred.slice(0, 5) : [];
    
    // Process pull requests
    const recentPRs = Array.isArray(pullRequests.items) ? pullRequests.items.slice(0, 4) : [];
    
    // Calculate comprehensive stats
    const totalStars = activeRepos.reduce((sum, repo) => sum + (repo.stargazers_count || 0), 0);
    const totalForks = activeRepos.reduce((sum, repo) => sum + (repo.forks_count || 0), 0);
    const languages = [...new Set(activeRepos.map(repo => repo.language).filter(Boolean))];
    const totalCommitsThisYear = events.filter(event => 
      event.type === 'PushEvent' && 
      new Date(event.created_at).getFullYear() === new Date().getFullYear()
    ).length;
    
    // Generate current time
    const now = new Date();
    const timeString = now.toLocaleString('en-US', { 
      weekday: 'long',
      year: 'numeric', 
      month: 'long', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'Europe/Athens'
    });
    
    // Build README content
    let readme = `<div align="center">

# Hello World! 👋 I'm Vaggelis Kavouras

[![Typing SVG](https://readme-typing-svg.herokuapp.com?font=Fira+Code&size=22&duration=3000&pause=1000&color=58A6FF&center=true&vCenter=true&width=700&lines=Full+Stack+Developer+from+Greece+🇬🇷;Building+Modern+Web+Applications;Always+Learning+%26+Shipping!;TypeScript+%7C+React+%7C+Next.js+Enthusiast;${totalCommitsThisYear}+Commits+in+${new Date().getFullYear()}!)](https://github.com/dacrab)

<img src="https://user-images.githubusercontent.com/74038190/212284100-561aa473-3905-4a80-b561-0d28506553ee.gif" width="900">

</div>

## 🚀 About Me

I'm a **solo developer** from 🇬🇷 **Greece** passionate about crafting modern, type-safe web applications. My journey started with **C** and static websites, and now I build full-stack, real-time applications using cutting-edge technologies.

- 🔭 Currently working on **${recentlyUpdated[0]?.name || 'exciting projects'}**
- 🌱 Learning advanced **TypeScript patterns** and **system design**
- 💡 Love **clean code**, **scalable architecture**, and **developer experience**
- 🎯 Always shipping **production-ready** applications
- 📍 Based in **Greece** 🇬🇷

<img src="https://user-images.githubusercontent.com/74038190/212284087-bbe7e430-757e-4901-90bf-4cd2ce3e1852.gif" width="100%">

## 🛠️ Tech Stack & Tools

<div align="center">

![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-06B6D4?style=for-the-badge&logo=tailwind-css&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![shadcn/ui](https://img.shields.io/badge/shadcn/ui-000000?style=for-the-badge&logo=shadcn&logoColor=white)

</div>

<img src="https://user-images.githubusercontent.com/74038190/212284087-bbe7e430-757e-4901-90bf-4cd2ce3e1852.gif" width="100%">

## 📊 GitHub Analytics

<div align="center">

![GitHub Metrics](https://raw.githubusercontent.com/dacrab/dacrab/main/github-metrics.svg)

</div>

<div align="center">

| 📈 **GitHub Stats** | 🔥 **Streak Stats** | 🌐 **Languages** |
|:---:|:---:|:---:|
| [![GitHub stats](https://github-readme-stats.vercel.app/api?username=dacrab&show_icons=true&theme=tokyonight&hide_border=true&bg_color=0D1117&title_color=58A6FF&text_color=C3D1D9&icon_color=58A6FF)](https://github.com/dacrab) | [![GitHub Streak](https://github-readme-streak-stats.herokuapp.com/?user=dacrab&theme=tokyonight&hide_border=true&background=0D1117&stroke=58A6FF&ring=58A6FF&fire=FF6B6B&currStreakLabel=58A6FF)](https://github.com/dacrab) | [![Top Languages](https://github-readme-stats.vercel.app/api/top-langs/?username=dacrab&layout=compact&theme=tokyonight&hide_border=true&bg_color=0D1117&title_color=58A6FF&text_color=C3D1D9)](https://github.com/dacrab) |

</div>

<img src="https://user-images.githubusercontent.com/74038190/212284087-bbe7e430-757e-4901-90bf-4cd2ce3e1852.gif" width="100%">

## 🏗️ Featured Projects

<table>
<tr>
<td width="50%">

### 🎯 [Argicon](https://argicon.gr)
**Architecture Studio Website**

\`\`\`typescript
Tech: Next.js + Framer Motion + i18n
Features: Multilingual, Animations, Modern UI
\`\`\`

</td>
<td width="50%">

### 🧱 [DesignDash](https://designdash.gr)
**Architecture Portfolio**

\`\`\`typescript
Tech: Next.js + Tailwind CSS + Dark Mode
Features: Responsive, Portfolio Gallery
\`\`\`

</td>
</tr>
<tr>
<td width="50%">

### 🧑‍💼 [clubOS](https://clubos.vercel.app)
**Sports Facility Management**

\`\`\`typescript
Tech: Real-time + RBAC + Analytics
Features: POS System, Booking, Dashboard
\`\`\`
[![Repo](https://img.shields.io/badge/View_Code-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/dacrab/clubos)

</td>
<td width="50%">

### 🌐 [Portfolio](https://dacrab.github.io/)
**Personal Developer Site**

\`\`\`typescript
Tech: Next.js + TypeScript + TailwindCSS
Features: Responsive, Modern, Fast
\`\`\`
[![Repo](https://img.shields.io/badge/View_Code-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/dacrab/portfolio)

</td>
</tr>
</table>

<img src="https://user-images.githubusercontent.com/74038190/212284087-bbe7e430-757e-4901-90bf-4cd2ce3e1852.gif" width="100%">

## 👷 Check out what I'm currently working on

`;
    
    // Add contributing repos
    contributingRepos.forEach((repoName, i) => {
      const shortName = repoName.split('/')[1] || repoName;
      readme += `**${i + 1}.** [${shortName}](https://github.com/${repoName}) - Active development\n`;
    });
    
    readme += `\n## 🌱 My latest projects\n\n`;
    
    // Add recent projects
    recentlyUpdated.slice(0, 5).forEach((repo, i) => {
      readme += `**${i + 1}.** [${repo.name}](${repo.html_url}) ${getLanguageEmoji(repo.language)} \`${repo.language || 'Misc'}\`  \n${repo.description || 'No description provided'}  \n⭐ ${repo.stargazers_count} · 🍴 ${repo.forks_count} · Updated ${formatTimeAgo(repo.updated_at)}\n\n`;
    });
    
    readme += `## 🔨 My recent Pull Requests\n\n`;
    
    // Add recent PRs
    recentPRs.forEach(pr => {
      const repoName = pr.repository_url.split('/').slice(-2).join('/');
      readme += `- [${pr.title}](${pr.html_url}) on [${repoName}](${pr.repository_url})\n`;
    });
    
    readme += `\n## ⭐ Recent Stars\n\n`;
    
    // Add recent stars
    recentStars.forEach(repo => {
      readme += `- [**${repo.name}**](${repo.html_url}) by [${repo.owner.login}](${repo.owner.html_url}) ${getLanguageEmoji(repo.language)}  \n  ${repo.description || 'No description available'}\n`;
    });
    
    readme += `
<img src="https://user-images.githubusercontent.com/74038190/212284087-bbe7e430-757e-4901-90bf-4cd2ce3e1852.gif" width="100%">

## 📊 Profile Stats

<div align="center">

| Metric | Value | Metric | Value |
|:---:|:---:|:---:|:---:|
| 📚 **Public Repositories** | **${user.public_repos || 0}** | 👥 **Followers** | **${user.followers || 0}** |
| ➡️ **Following** | **${user.following || 0}** | ⭐ **Total Stars Earned** | **${totalStars}** |
| 🍴 **Total Forks** | **${totalForks}** | 💻 **Languages Used** | **${languages.length}** |
| 🔥 **Commits This Year** | **${totalCommitsThisYear}** | 📈 **Profile Views** | ![Profile Views](https://komarev.com/ghpvc/?username=dacrab&style=flat-square&color=58A6FF) |

</div>

<img src="https://user-images.githubusercontent.com/74038190/212284087-bbe7e430-757e-4901-90bf-4cd2ce3e1852.gif" width="100%">

## 🤝 Let's Connect & Collaborate!

<div align="center">

[![Instagram](https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white)](https://www.instagram.com/killcrb/)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/dacrab)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/vkavouras/)

**💬 Open to collaborations and interesting projects!**

</div>

<img src="https://user-images.githubusercontent.com/74038190/212284087-bbe7e430-757e-4901-90bf-4cd2ce3e1852.gif" width="100%">

<div align="center">

[![Activity Graph](https://github-readme-activity-graph.vercel.app/graph?username=dacrab&custom_title=Vaggelis's%20Activity%20Graph&bg_color=0D1117&color=58A6FF&line=58A6FF&point=FFFFFF&area=true&hide_border=true)](https://github.com/dacrab)

</div>

<img src="https://user-images.githubusercontent.com/74038190/212284087-bbe7e430-757e-4901-90bf-4cd2ce3e1852.gif" width="100%">

<div align="center">

### ✨ **"Code is poetry written in logic"** ✨

<img src="https://user-images.githubusercontent.com/74038190/212284158-e840e285-664b-44d7-b79b-e264b5e54825.gif" width="400">

*🕒 Last updated: ${timeString} (Europe/Athens)*

</div>`;
    
    fs.writeFileSync('README.md', readme);
    console.log('✅ Enhanced Dynamic README generated successfully!');
    console.log(`📊 Processed ${activeRepos.length} repos, ${recentActivity.length} activities, ${recentStars.length} stars, ${recentPRs.length} PRs`);
    
  } catch (error) {
    console.error('❌ Error generating README:', error);
    process.exit(1);
  }
}

generateReadme();
