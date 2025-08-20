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
    const prs = await this.fetchFromGitHub(`/search/issues?q=${encodeURIComponent(searchQuery)}&sort=created&order=desc&per_page=${this.config.content.maxPullRequests || 5}`);
    
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
    
    // ChrisTitusTech style social links using danielcranney icons
    const socialPlatforms = {
      github: 'github',
      linkedin: 'linkedin', 
      instagram: 'instagram',
      website: null, // Website uses different handling
      email: null // Email uses different handling
    };

    Object.entries(this.config.social).forEach(([platform, url]) => {
      if (!url) return;
      
      if (platform === 'website') {
        // Handle website separately
        return;
      }
      
      if (platform === 'email') {
        // Handle email separately  
        return;
      }
      
      if (socialPlatforms[platform]) {
        const iconName = socialPlatforms[platform];
        links.push(`<a href="${url}" target="_blank" rel="noreferrer"> <picture> <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/danielcranney/readme-generator/main/public/icons/socials/${iconName}-dark.svg" /> <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/danielcranney/readme-generator/main/public/icons/socials/${iconName}.svg" /> <img src="https://raw.githubusercontent.com/danielcranney/readme-generator/main/public/icons/socials/${iconName}.svg" width="32" height="32" /> </picture> </a>`);
      }
    });

    return `<p align="left"> ${links.join(' ')} </p>`;
  }

  generateContactInfo() {
    const contacts = [];
    
    if (this.config.social.website) {
      contacts.push(`  - Website  : <${this.config.social.website}>`);
    }
    
    if (this.config.social.linkedin) {
      contacts.push(`  - LinkedIn : <${this.config.social.linkedin}>`);
    }
    
    if (this.config.social.email) {
      contacts.push(`  - Email    : <${this.config.social.email}>`);
    }
    
    if (this.config.social.github) {
      contacts.push(`  - GitHub   : <${this.config.social.github}>`);
    }

    return contacts.join('\n');
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

    // Generate content sections (ChrisTitusTech style)
    const workingOn = this.generateCurrentlyWorkingOn(currentWork);
    const latestProjectsContent = this.generateLatestProjects(latestProjects);
    const recentPRsContent = this.generateRecentPullRequests(recentPRs);
    const recentStarsContent = this.generateRecentStars(recentStars);
    const techStack = this.generateTechStack(languages);
    const socialLinks = this.generateSocialLinks(profile);
    const contactInfo = this.generateContactInfo();

    // Read template
    console.log('📄 Processing README template...');
    const template = await readFile('README.gtpl', 'utf8');

    // Generate final README (ChrisTitusTech style with beautiful header)
    const readme = template
      .replace(/\{\{USERNAME\}\}/g, this.config.profile.username)
      .replace(/\{\{USER_NAME\}\}/g, profile.name)
      .replace(/\{\{USER_BIO\}\}/g, profile.bio || 'Passionate developer building amazing projects')
      .replace(/\{\{REPO_COUNT\}\}/g, profile.public_repos)
      .replace(/\{\{FOLLOWERS_COUNT\}\}/g, profile.followers)
      .replace(/\{\{AVATAR_URL\}\}/g, profile.avatar_url)
      .replace(/\{\{SOCIAL_LINKS\}\}/g, socialLinks)
      .replace(/\{\{WORKING_ON\}\}/g, workingOn)
      .replace(/\{\{LATEST_PROJECTS\}\}/g, latestProjectsContent)
      .replace(/\{\{RECENT_PRS\}\}/g, recentPRsContent)
      .replace(/\{\{RECENT_STARS\}\}/g, recentStarsContent)
      .replace(/\{\{TECH_STACK\}\}/g, techStack)
      .replace(/\{\{CONTACT_INFO\}\}/g, contactInfo);

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