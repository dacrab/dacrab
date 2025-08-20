#!/usr/bin/env node

/**
 * 🚀 GitHub Profile README Generator
 * Redesigned based on ChrisTitusTech's functional approach
 */

import { readFile, writeFile } from 'fs/promises';
import fetch from 'node-fetch';

class ProfileReadmeGenerator {
  constructor() {
    this.config = null;
    this.cache = new Map();
    this.githubToken = process.env.GITHUB_TOKEN || '';
  }

  async loadConfig() {
    console.log('📋 Loading configuration...');
    try {
      const configModule = await import('../config.js');
      this.config = configModule.default;
      console.log(`✅ Configuration loaded for ${this.config.profile.username}`);
    } catch (error) {
      console.error('❌ Failed to load config.js:', error.message);
      process.exit(1);
    }
  }

  async fetchFromGitHub(endpoint) {
    const url = `https://api.github.com${endpoint}`;
    const headers = {
      'Accept': 'application/vnd.github.v3+json',
      'User-Agent': 'profile-readme-generator'
    };
    
    if (this.githubToken) {
      headers['Authorization'] = `token ${this.githubToken}`;
    }

    try {
      const response = await fetch(url, { headers });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.warn(`⚠️ GitHub API error for ${endpoint}:`, error.message);
      return null;
    }
  }

  async getUserProfile() {
    console.log('👤 Fetching profile information...');
    const profile = await this.fetchFromGitHub(`/users/${this.config.profile.username}`);
    
    if (!profile) {
      console.warn('⚠️ Using config values for profile');
      return this.config.profile;
    }

    return {
      username: this.config.profile.username,
      name: this.config.profile.name || profile.name || this.config.profile.username,
      bio: this.config.profile.bio || profile.bio || this.config.messages.aboutMe,
      location: this.config.profile.location || profile.location || '',
      company: this.config.profile.company || profile.company || '',
      website: this.config.profile.website || profile.blog || '',
      email: this.config.profile.email || '',
      avatar_url: profile.avatar_url || '',
      followers: profile.followers || 0,
      following: profile.following || 0,
      public_repos: profile.public_repos || 0,
      created_at: profile.created_at || new Date().toISOString(),
      twitter_username: profile.twitter_username || ''
    };
  }

  async getCurrentlyWorkingOn() {
    console.log('🔨 Fetching what you\'re currently working on...');
    
    // Get recent events to find actively worked repositories
    const events = await this.fetchFromGitHub(
      `/users/${this.config.profile.username}/events?per_page=100`
    );
    
    if (!events) return [];

    // Find repos with recent activity (pushes, PRs, issues)
    const recentRepos = new Map();
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - 30); // Last 30 days

    events.forEach(event => {
      if (new Date(event.created_at) < cutoffDate) return;
      
      if (['PushEvent', 'PullRequestEvent', 'IssuesEvent', 'CreateEvent'].includes(event.type)) {
        const repoName = event.repo.name;
        if (!recentRepos.has(repoName)) {
          recentRepos.set(repoName, {
            name: repoName,
            lastActivity: event.created_at,
            activityType: event.type
          });
        }
      }
    });

    // Get detailed repo info for the most active ones
    const activeRepos = Array.from(recentRepos.values())
      .sort((a, b) => new Date(b.lastActivity) - new Date(a.lastActivity))
      .slice(0, this.config.content.maxRepos || 5);

    const repoDetails = await Promise.all(
      activeRepos.map(async (repo) => {
        const repoData = await this.fetchFromGitHub(`/repos/${repo.name}`);
        if (!repoData) return null;
        
        return {
          name: repoData.name,
          full_name: repoData.full_name,
          description: repoData.description || 'No description available',
          html_url: repoData.html_url,
          language: repoData.language,
          stargazers_count: repoData.stargazers_count,
          lastActivity: repo.lastActivity
        };
      })
    );

    return repoDetails.filter(repo => repo !== null);
  }

  async getLatestProjects() {
    console.log('🌱 Fetching your latest projects...');
    const repos = await this.fetchFromGitHub(
      `/users/${this.config.profile.username}/repos?sort=created&direction=desc&per_page=${this.config.content.maxRepos || 5}`
    );
    
    if (!repos) return [];

    return repos
      .filter(repo => !repo.fork && repo.size > 0 && !repo.archived)
      .map(repo => ({
        name: repo.name,
        full_name: repo.full_name,
        description: repo.description || 'No description available',
        html_url: repo.html_url,
        language: repo.language,
        stargazers_count: repo.stargazers_count,
        created_at: repo.created_at
      }));
  }

  async getRecentPullRequests() {
    console.log('🔀 Fetching recent pull requests...');
    
    // Search for recent PRs by the user
    const searchQuery = `author:${this.config.profile.username} is:pr created:>=${new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]}`;
    const prs = await this.fetchFromGitHub(`/search/issues?q=${encodeURIComponent(searchQuery)}&sort=created&order=desc&per_page=5`);
    
    if (!prs || !prs.items) return [];

    return prs.items.map(pr => ({
      title: pr.title,
      html_url: pr.html_url,
      repository: pr.repository_url.split('/').slice(-2).join('/'),
      state: pr.state,
      created_at: pr.created_at
    }));
  }

  async getRecentStars() {
    console.log('⭐ Fetching recently starred repositories...');
    const starred = await this.fetchFromGitHub(
      `/users/${this.config.profile.username}/starred?per_page=${this.config.content.maxStarred || 5}&sort=created&direction=desc`
    );
    
    if (!starred || starred.length === 0) return [];

    return starred.map(repo => ({
      name: repo.name,
      full_name: repo.full_name,
      description: repo.description || 'No description available',
      html_url: repo.html_url,
      owner: repo.owner.login,
      language: repo.language,
      stargazers_count: repo.stargazers_count
    }));
  }

  async getLanguageStats() {
    console.log('💻 Analyzing languages...');
    const repos = await this.fetchFromGitHub(`/users/${this.config.profile.username}/repos?per_page=100`);
    
    if (!repos) return [];

    const langCount = {};
    repos.forEach(repo => {
      if (repo.language && !repo.fork && repo.size > 0) {
        langCount[repo.language] = (langCount[repo.language] || 0) + 1;
      }
    });

    return Object.entries(langCount)
      .sort(([,a], [,b]) => b - a)
      .slice(0, this.config.content.maxLanguages || 8)
      .map(([language, count]) => ({ language, count }));
  }

  generateCurrentlyWorkingOn(repos) {
    if (!repos.length) {
      return `* Working on exciting new projects! 🚀`;
    }

    return repos.map(repo => {
      const description = repo.description.length > 100 
        ? repo.description.substring(0, 100) + '...' 
        : repo.description;
      return `* [${repo.name}](${repo.html_url}) - ${description}`;
    }).join('\n');
  }

  generateLatestProjects(repos) {
    if (!repos.length) {
      return `* Check out my [GitHub profile](https://github.com/${this.config.profile.username}) for all projects!`;
    }

    return repos.map(repo => {
      const description = repo.description.length > 100 
        ? repo.description.substring(0, 100) + '...' 
        : repo.description;
      return `* [${repo.name}](${repo.html_url}) - ${description}`;
    }).join('\n');
  }

  generateRecentPullRequests(prs) {
    if (!prs.length) {
      return `* No recent pull requests - time to contribute! 🔀`;
    }

    return prs.map(pr => {
      const title = pr.title.length > 80 ? pr.title.substring(0, 80) + '...' : pr.title;
      const repo = pr.repository.split('/')[1];
      return `* [${title}](${pr.html_url}) on [${repo}](https://github.com/${pr.repository})`;
    }).join('\n');
  }

  generateRecentStars(stars) {
    if (!stars.length) {
      return `* No recent stars - discover some awesome repos! ⭐`;
    }

    return stars.map(repo => {
      const description = repo.description.length > 80 
        ? repo.description.substring(0, 80) + '...' 
        : repo.description;
      return `* [${repo.owner}/${repo.name}](${repo.html_url}) - ${description}`;
    }).join('\n');
  }

  generateTechStack(languages) {
    if (!languages.length) {
      return `![Top Languages](https://github-readme-stats.vercel.app/api/top-langs/?username=${this.config.profile.username}&layout=compact&theme=tokyonight&hide_border=true)`;
    }

    const languageColors = {
      'JavaScript': 'F7DF1E', 'TypeScript': '3178C6', 'Python': '3776AB',
      'Java': 'ED8B00', 'C++': '00599C', 'C': 'A8B9CC', 'C#': '239120',
      'PHP': '777BB4', 'Ruby': 'CC342D', 'Go': '00ADD8', 'Rust': 'DEA584',
      'Swift': 'FA7343', 'Kotlin': '0095D5', 'Dart': '0175C2',
      'HTML': 'E34F26', 'CSS': '1572B6', 'Astro': 'FF5D01', 'Shell': '89e051',
      'Vue': '4FC08D', 'React': '61DAFB', 'Svelte': 'FF3E00', 'Angular': 'DD0031'
    };

    const badges = languages.map(({ language }) => {
      const color = languageColors[language] || '666666';
      const encodedLang = encodeURIComponent(language);
      return `![${language}](https://img.shields.io/badge/${encodedLang}-${color}?style=for-the-badge&logoColor=white)`;
    });

    return `${badges.join('\n')}`;
  }

  generateSocialLinks(profile) {
    const links = [];
    
    if (profile.website) {
      links.push(`[![Website](https://img.shields.io/badge/Website-FF5722?style=for-the-badge&logo=google-chrome&logoColor=white)](${profile.website})`);
    }
    
    const socialPlatforms = {
      linkedin: { name: 'LinkedIn', color: '0077B5', logo: 'linkedin' },
      twitter: { name: 'Twitter', color: '1DA1F2', logo: 'twitter' },
      instagram: { name: 'Instagram', color: 'E4405F', logo: 'instagram' },
      youtube: { name: 'YouTube', color: 'FF0000', logo: 'youtube' },
      discord: { name: 'Discord', color: '7289DA', logo: 'discord' },
      email: { name: 'Email', color: 'D14836', logo: 'gmail' }
    };

    Object.entries(this.config.social).forEach(([platform, url]) => {
      if (url && socialPlatforms[platform]) {
        const { name, color, logo } = socialPlatforms[platform];
        links.push(`[![${name}](https://img.shields.io/badge/${name}-${color}?style=for-the-badge&logo=${logo}&logoColor=white)](${url})`);
      }
    });

    if (profile.twitter_username && !this.config.social.twitter) {
      links.push(`[![Twitter](https://img.shields.io/badge/Twitter-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white)](https://twitter.com/${profile.twitter_username})`);
    }

    links.push(`[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/${this.config.profile.username})`);

    return links.join('\n');
  }

  generateProfileStats(profile) {
    const stats = [];
    
    if (profile.company) stats.push(`🏢 **${profile.company}**`);
    if (profile.location) stats.push(`📍 **${profile.location}**`);
    
    const year = new Date(profile.created_at).getFullYear();
    stats.push(`📅 **Coding since ${year}**`);
    stats.push(`📊 **${profile.public_repos}** repositories`);
    stats.push(`👥 **${profile.followers}** followers • **${profile.following}** following`);
    
    if (profile.website) stats.push(`🌐 [**Website**](${profile.website})`);

    return stats.join(' • ');
  }

  generateTypingLines(profile) {
    const lines = [
      profile.bio,
      'Building amazing projects',
      'Always learning new technologies'
    ];
    
    if (profile.company) lines.push(`Working at ${profile.company}`);
    lines.push('Open to collaboration!');
    
    return lines
      .filter(line => line && line.trim())
      .map(line => encodeURIComponent(line))
      .join(';');
  }

  async generateReadme() {
    console.log('\n🚀 Starting profile README generation...\n');
    
    await this.loadConfig();
    
    // Fetch all data in parallel for better performance
    const [profile, currentWork, latestProjects, recentPRs, recentStars, languages] = await Promise.all([
      this.getUserProfile(),
      this.getCurrentlyWorkingOn(),
      this.getLatestProjects(),
      this.getRecentPullRequests(),
      this.getRecentStars(),
      this.getLanguageStats()
    ]);

    // Generate content sections
    const typingLines = this.generateTypingLines(profile);
    const profileStats = this.generateProfileStats(profile);
    const workingOn = this.generateCurrentlyWorkingOn(currentWork);
    const latestProjectsContent = this.generateLatestProjects(latestProjects);
    const recentPRsContent = this.generateRecentPullRequests(recentPRs);
    const recentStarsContent = this.generateRecentStars(recentStars);
    const techStack = this.generateTechStack(languages);
    const socialLinks = this.generateSocialLinks(profile);

    // Read template
    console.log('📄 Processing README template...');
    const template = await readFile('README.gtpl', 'utf8');

    // Generate final README
    const readme = template
      .replace(/\{\{USERNAME\}\}/g, this.config.profile.username)
      .replace(/\{\{USER_NAME\}\}/g, profile.name)
      .replace(/\{\{USER_BIO\}\}/g, profile.bio)
      .replace(/\{\{PRIMARY_COLOR\}\}/g, this.config.theme.primaryColor)
      .replace(/\{\{BG_COLOR\}\}/g, this.config.theme.backgroundColor)
      .replace(/\{\{TEXT_COLOR\}\}/g, this.config.theme.textColor)
      .replace(/\{\{TYPING_LINES\}\}/g, typingLines)
      .replace(/\{\{AVATAR_URL\}\}/g, profile.avatar_url)
      .replace(/\{\{PROFILE_STATS\}\}/g, profileStats)
      .replace(/\{\{TECH_STACK\}\}/g, techStack)
      .replace(/\{\{FEATURED_PROJECTS\}\}/g, latestProjectsContent)
      .replace(/\{\{SOCIAL_LINKS\}\}/g, socialLinks)
      .replace(/\{\{CONTACT_MESSAGE\}\}/g, this.config.messages.contactMessage)
      .replace(/\{\{QUOTE\}\}/g, this.config.messages.quote)
      .replace(/\{\{WORKING_ON\}\}/g, workingOn)
      .replace(/\{\{LATEST_PROJECTS\}\}/g, latestProjectsContent)
      .replace(/\{\{RECENT_PRS\}\}/g, recentPRsContent)
      .replace(/\{\{RECENT_STARS\}\}/g, recentStarsContent);

    // Write README
    await writeFile('README.md', readme, 'utf8');
    
    console.log('\n✅ README.md generated successfully!');
    console.log(`📊 Profile: ${profile.name} (@${this.config.profile.username})`);
    console.log(`🔨 Currently working on: ${currentWork.length} repos`);
    console.log(`🌱 Latest projects: ${latestProjects.length} repos`);
    console.log(`🔀 Recent PRs: ${recentPRs.length} pull requests`);
    console.log(`⭐ Recent stars: ${recentStars.length} repositories`);
    console.log(`💻 Languages: ${languages.length} detected`);
    console.log('\n🎯 Next steps:');
    console.log('   • Review your README.md');
    console.log('   • Commit and push to GitHub');  
    console.log('   • Set up the workflow to auto-update every 6 hours\n');
  }
}

// Run the generator
const generator = new ProfileReadmeGenerator();
generator.generateReadme().catch(error => {
  console.error('\n💥 Generation failed:', error.message);
  console.log('🔍 Debug info:', error.stack);
  process.exit(1);
});