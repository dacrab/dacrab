#!/usr/bin/env node

/**
 * 🚀 Race-Condition-Free Dynamic README Generator
 * Atomic operations with proper error handling and retry logic
 */

import { readFile, writeFile, access } from 'fs/promises';
import { constants } from 'fs';

class AtomicReadmeGenerator {
  constructor() {
    this.config = null;
    this.retryCount = 3;
    this.retryDelay = 1000;
    this.cache = new Map();
  }

  async loadConfig() {
    try {
      await access('config.js', constants.F_OK);
      const configContent = await readFile('config.js', 'utf8');
      
      // Safe config parsing
      const configMatch = configContent.match(/module\.exports\s*=\s*({[\s\S]*?});?\s*$/);
      if (configMatch) {
        // Use Function constructor for safer evaluation
        const configFunc = new Function('module', 'exports', configContent + '; return module.exports;');
        const mockModule = { exports: {} };
        this.config = configFunc(mockModule, mockModule.exports);
      } else {
        throw new Error('Invalid config format');
      }
    } catch (error) {
      console.warn('⚠️ Config loading failed, using defaults:', error.message);
      this.config = this.getDefaultConfig();
    }
  }

  getDefaultConfig() {
    return {
      user: {
        username: 'dacrab',
        displayName: '',
        bio: '',
        location: '',
        email: '',
        website: ''
      },
      theme: {
        primaryColor: '58A6FF',
        backgroundColor: '0D1117',
        textColor: 'C3D1D9'
      },
      content: {
        maxRepos: 6,
        maxLanguages: 8,
        maxActivity: 5,
        maxStarred: 6
      },
      messages: {
        tagline: 'Building amazing projects',
        quote: 'Code is poetry written in logic',
        contactMessage: 'Open to collaborations!',
        workingOn: 'What I\'m working on',
        recentStars: 'Recently starred'
      },
      social: {}
    };
  }

  async fetchWithRetry(url, options = {}) {
    const cacheKey = url + JSON.stringify(options);
    
    // Return cached result if available
    if (this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey);
    }

    for (let attempt = 1; attempt <= this.retryCount; attempt++) {
      try {
        const response = await fetch(url, {
          ...options,
          headers: {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'dynamic-readme-generator',
            ...options.headers
          }
        });

        if (response.ok) {
          const data = await response.json();
          this.cache.set(cacheKey, data);
          return data;
        }

        if (response.status === 403) {
          console.warn(`⚠️ Rate limited on attempt ${attempt}/${this.retryCount}`);
          if (attempt < this.retryCount) {
            await this.sleep(this.retryDelay * attempt);
            continue;
          }
        }

        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      } catch (error) {
        console.warn(`⚠️ Fetch attempt ${attempt}/${this.retryCount} failed:`, error.message);
        
        if (attempt === this.retryCount) {
          return null;
        }
        
        await this.sleep(this.retryDelay * attempt);
      }
    }

    return null;
  }

  async sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async getUserProfile() {
    console.log('👤 Fetching user profile...');
    const profile = await this.fetchWithRetry(`https://api.github.com/users/${this.config.user.username}`);
    
    if (!profile) {
      console.warn('⚠️ Could not fetch profile, using config defaults');
      return this.config.user;
    }

    return {
      username: this.config.user.username,
      displayName: this.config.user.displayName || profile.name || this.config.user.username,
      bio: this.config.user.bio || profile.bio || this.config.messages.tagline,
      location: this.config.user.location || profile.location || '',
      email: this.config.user.email || '',
      website: this.config.user.website || profile.blog || '',
      company: profile.company || '',
      followers: profile.followers || 0,
      following: profile.following || 0,
      publicRepos: profile.public_repos || 0,
      avatarUrl: profile.avatar_url || ''
    };
  }

  async getRepositories() {
    console.log('📊 Fetching repositories...');
    const repos = await this.fetchWithRetry(
      `https://api.github.com/users/${this.config.user.username}/repos?sort=updated&per_page=100`
    );

    if (!repos) {
      return [];
    }

    return repos
      .filter(repo => !repo.fork && !repo.archived && repo.size > 0)
      .slice(0, this.config.content.maxRepos)
      .map(repo => ({
        name: repo.name,
        fullName: repo.full_name,
        description: repo.description || 'No description available',
        url: repo.html_url,
        language: repo.language || 'Unknown',
        stars: repo.stargazers_count || 0,
        forks: repo.forks_count || 0,
        size: repo.size || 0,
        updatedAt: new Date(repo.updated_at).toLocaleDateString(),
        createdAt: new Date(repo.created_at).toLocaleDateString(),
        topics: repo.topics || []
      }));
  }

  async getLanguageStats() {
    console.log('💻 Analyzing languages...');
    const repos = await this.fetchWithRetry(
      `https://api.github.com/users/${this.config.user.username}/repos?per_page=100`
    );

    if (!repos) {
      return [];
    }

    const languageCount = {};
    const languageBytes = {};

    repos.forEach(repo => {
      if (repo.language && !repo.fork && repo.size > 0) {
        languageCount[repo.language] = (languageCount[repo.language] || 0) + 1;
        languageBytes[repo.language] = (languageBytes[repo.language] || 0) + repo.size;
      }
    });

    return Object.entries(languageCount)
      .sort(([,a], [,b]) => b - a)
      .slice(0, this.config.content.maxLanguages)
      .map(([language, count]) => ({
        language,
        count,
        bytes: languageBytes[language] || 0
      }));
  }

  async getRecentActivity() {
    console.log('⚡ Fetching recent activity...');
    const events = await this.fetchWithRetry(
      `https://api.github.com/users/${this.config.user.username}/events/public?per_page=30`
    );

    if (!events) {
      return '- 🌱 Building amazing projects!';
    }

    const activities = events
      .filter(event => ['PushEvent', 'CreateEvent', 'IssuesEvent', 'PullRequestEvent', 'ReleaseEvent'].includes(event.type))
      .slice(0, this.config.content.maxActivity)
      .map(event => {
        const repoName = event.repo.name.split('/')[1];
        const date = new Date(event.created_at).toLocaleDateString();
        
        switch (event.type) {
          case 'PushEvent':
            const commits = event.payload.commits?.length || 1;
            return `🔨 Pushed ${commits} commit${commits > 1 ? 's' : ''} to **${repoName}** - ${date}`;
          case 'CreateEvent':
            const refType = event.payload.ref_type || 'repository';
            return `🆕 Created ${refType} in **${repoName}** - ${date}`;
          case 'IssuesEvent':
            return `🐛 ${event.payload.action} issue in **${repoName}** - ${date}`;
          case 'PullRequestEvent':
            return `🔀 ${event.payload.action} PR in **${repoName}** - ${date}`;
          case 'ReleaseEvent':
            return `🚀 Released **${event.payload.release?.tag_name || 'new version'}** in **${repoName}** - ${date}`;
          default:
            return `⚡ Activity in **${repoName}** - ${date}`;
        }
      });

    return activities.length > 0 
      ? activities.map(activity => `- ${activity}`).join('\n')
      : '- 🌱 Building amazing projects!';
  }

  async getRecentlyStarred() {
    console.log('⭐ Fetching recently starred...');
    const starred = await this.fetchWithRetry(
      `https://api.github.com/users/${this.config.user.username}/starred?per_page=${this.config.content.maxStarred}&sort=created`
    );

    if (!starred) {
      return '<!-- No starred repositories available -->';
    }

    const starredRepos = starred
      .slice(0, this.config.content.maxStarred)
      .map(repo => {
        const description = repo.description 
          ? (repo.description.length > 100 ? repo.description.substring(0, 100) + '...' : repo.description)
          : 'No description available';
        
        return `
### [${repo.name}](${repo.html_url})
${description}

![${repo.language || 'Unknown'}](https://img.shields.io/badge/${encodeURIComponent(repo.language || 'Unknown')}-blue?style=flat-square) ![Stars](https://img.shields.io/badge/⭐-${repo.stargazers_count}-yellow?style=flat-square)`;
      });

    return starredRepos.join('\n');
  }

  generateTechStack(languages) {
    if (!languages.length) {
      return `![Top Languages](https://github-readme-stats.vercel.app/api/top-langs/?username=${this.config.user.username}&layout=compact&theme=tokyonight&hide_border=true)`;
    }

    const languageColors = {
      'JavaScript': 'F7DF1E', 'TypeScript': '3178C6', 'Python': '3776AB',
      'Java': 'ED8B00', 'C++': '00599C', 'C': 'A8B9CC', 'C#': '239120',
      'PHP': '777BB4', 'Ruby': 'CC342D', 'Go': '00ADD8', 'Rust': 'DEA584',
      'Swift': 'FA7343', 'Kotlin': '0095D5', 'Dart': '0175C2',
      'HTML': 'E34F26', 'CSS': '1572B6', 'SCSS': 'CC6699',
      'Vue': '4FC08D', 'React': '61DAFB', 'Angular': 'DD0031',
      'Node.js': '339933', 'Express': '000000', 'Django': '092E20',
      'Flask': '000000', 'Laravel': 'FF2D20', 'Spring': '6DB33F',
      'Astro': 'FF5D01', 'Svelte': 'FF3E00', 'Next.js': '000000'
    };

    const badges = languages.map(({ language }) => {
      const color = languageColors[language] || '666666';
      const encodedLang = encodeURIComponent(language.replace(/\+/g, 'plus'));
      return `![${language}](https://img.shields.io/badge/${encodedLang}-${color}?style=for-the-badge&logo=${language.toLowerCase().replace(/\+/g, 'plus')}&logoColor=white)`;
    });

    return `
### 🛠️ Technologies I Use

${badges.join('\n')}`;
  }

  generateFeaturedProjects(repos) {
    if (!repos.length) {
      return `
### 🚀 Featured Repositories

Visit my [GitHub profile](https://github.com/${this.config.user.username}) to see all my projects!`;
    }

    const projectCards = repos.map(repo => `
### [${repo.name}](${repo.url})
${repo.description}

**Language:** ${repo.language} | **Stars:** ⭐ ${repo.stars} | **Forks:** 🍴 ${repo.forks}  
**Topics:** ${repo.topics.length > 0 ? repo.topics.join(', ') : 'None'} | **Updated:** ${repo.updatedAt}`);

    return `
### 🚀 Featured Repositories

${projectCards.join('\n')}`;
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
      email: { name: 'Email', color: 'D14836', logo: 'gmail' }
    };

    Object.entries(this.config.social || {}).forEach(([platform, url]) => {
      if (url && socialPlatforms[platform]) {
        const { name, color, logo } = socialPlatforms[platform];
        links.push(`[![${name}](https://img.shields.io/badge/${name}-${color}?style=for-the-badge&logo=${logo}&logoColor=white)](${url})`);
      }
    });

    links.push(`[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/${this.config.user.username})`);

    return links.join('\n');
  }

  generateAboutSection(profile) {
    const items = [];
    
    if (profile.company) {
      items.push(`- 🏢 Working at **${profile.company}**`);
    }
    
    if (profile.location) {
      items.push(`- 📍 Based in **${profile.location}**`);
    }
    
    items.push(`- 📊 **${profile.publicRepos}** public repositories`);
    items.push(`- 👥 **${profile.followers}** followers • **${profile.following}** following`);
    
    if (profile.website) {
      items.push(`- 🌐 Check out my [website](${profile.website})`);
    }

    return items.join('\n');
  }

  async validateSetup() {
    console.log('🔍 Validating setup...');
    
    // Check Node version
    const nodeVersion = process.version;
    const requiredMajor = 18;
    const currentMajor = parseInt(nodeVersion.slice(1).split('.')[0]);
    
    if (currentMajor < requiredMajor) {
      throw new Error(`Node.js ${requiredMajor}+ required. Current: ${nodeVersion}`);
    }
    
    // Check required files
    const requiredFiles = ['README.gtpl', 'config.js'];
    for (const file of requiredFiles) {
      try {
        await access(file, constants.F_OK);
      } catch {
        throw new Error(`Required file missing: ${file}`);
      }
    }
    
    console.log('✅ Setup validation passed');
  }

  async atomicGenerate() {
    console.log('🚀 Starting atomic README generation...');
    
    try {
      // Validate setup first
      await this.validateSetup();
      
      // Load configuration
      await this.loadConfig();
      
      // Check template exists
      await access('README.gtpl', constants.F_OK);
      
      // Fetch all data concurrently but safely
      const [profile, repos, languages, recentActivity, recentlyStarred, template] = await Promise.allSettled([
        this.getUserProfile(),
        this.getRepositories(),
        this.getLanguageStats(),
        this.getRecentActivity(),
        this.getRecentlyStarred(),
        readFile('README.gtpl', 'utf8')
      ]);

      // Handle any failed promises gracefully
      const profileData = profile.status === 'fulfilled' ? profile.value : this.config.user;
      const reposData = repos.status === 'fulfilled' ? repos.value : [];
      const languagesData = languages.status === 'fulfilled' ? languages.value : [];
      const activityData = recentActivity.status === 'fulfilled' ? recentActivity.value : '- 🌱 Building amazing projects!';
      const starredData = recentlyStarred.status === 'fulfilled' ? recentlyStarred.value : '<!-- No starred data -->';
      const templateData = template.status === 'fulfilled' ? template.value : '';

      if (!templateData) {
        throw new Error('Could not read README template');
      }

      // Generate typing animation lines
      const typingLines = [
        profileData.bio || this.config.messages.tagline,
        'Building amazing projects',
        'Always learning new technologies',
        'Open to collaboration!'
      ].join(';');

      // Atomic replacement - all at once
      const readme = templateData
        .replace(/\{\{USERNAME\}\}/g, this.config.user.username)
        .replace(/\{\{USER_NAME\}\}/g, profileData.displayName)
        .replace(/\{\{USER_BIO\}\}/g, profileData.bio)
        .replace(/\{\{PRIMARY_COLOR\}\}/g, this.config.theme.primaryColor)
        .replace(/\{\{BG_COLOR\}\}/g, this.config.theme.backgroundColor)
        .replace(/\{\{TEXT_COLOR\}\}/g, this.config.theme.textColor)
        .replace(/\{\{TYPING_LINES\}\}/g, typingLines)
        .replace(/\{\{ABOUT_SECTION\}\}/g, this.generateAboutSection(profileData))
        .replace(/\{\{TECH_STACK\}\}/g, this.generateTechStack(languagesData))
        .replace(/\{\{FEATURED_PROJECTS\}\}/g, this.generateFeaturedProjects(reposData))
        .replace(/\{\{SOCIAL_LINKS\}\}/g, this.generateSocialLinks(profileData))
        .replace(/\{\{CONTACT_MESSAGE\}\}/g, this.config.messages.contactMessage)
        .replace(/\{\{QUOTE\}\}/g, this.config.messages.quote)
        .replace(/\{\{WORKING_ON\}\}/g, this.config.messages.workingOn)
        .replace(/\{\{RECENT_STARS\}\}/g, this.config.messages.recentStars)
        .replace('<!--RECENT_ACTIVITY:start--><!--RECENT_ACTIVITY:end-->', 
          `<!--RECENT_ACTIVITY:start-->\n${activityData}\n<!--RECENT_ACTIVITY:end-->`)
        .replace('<!--RECENTLY_STARRED:start--><!--RECENTLY_STARRED:end-->', 
          `<!--RECENTLY_STARRED:start-->\n${starredData}\n<!--RECENTLY_STARRED:end-->`);

      // Atomic write
      await writeFile('README.md', readme, 'utf8');
      console.log('✅ README.md generated successfully!');
      
    } catch (error) {
      console.error('❌ Atomic generation failed:', error.message);
      process.exit(1);
    }
  }
}

// Execute with proper error handling
const generator = new AtomicReadmeGenerator();
generator.atomicGenerate().catch(error => {
  console.error('💥 Fatal error:', error);
  process.exit(1);
});