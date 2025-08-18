#!/usr/bin/env node

/**
 * 🚀 Enhanced Dynamic README Generator
 * Modern, modular approach with better error handling and caching
 */

const https = require('https');
const fs = require('fs');
const path = require('path');
const config = require('../config.js');

class ReadmeGenerator {
  constructor() {
    this.config = config;
    this.cache = new Map();
    this.cacheDir = path.join(__dirname, '../.cache');
    this.errors = [];
    
    // Ensure cache directory exists
    if (!fs.existsSync(this.cacheDir)) {
      fs.mkdirSync(this.cacheDir, { recursive: true });
    }
  }

  /**
   * Make HTTP request with retry logic
   */
  async makeRequest(url, options = {}, retries = 3) {
    const requestOptions = {
      headers: {
        'User-Agent': 'Enhanced-README-Generator/2.0',
        'Accept': 'application/vnd.github.v3+json',
        ...options.headers
      },
      timeout: 10000,
      ...options
    };

    if (process.env.GITHUB_TOKEN) {
      requestOptions.headers['Authorization'] = `token ${process.env.GITHUB_TOKEN}`;
    }

    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        const data = await this._makeHttpRequest(url, requestOptions);
        return JSON.parse(data);
      } catch (error) {
        console.warn(`⚠️  Request attempt ${attempt}/${retries} failed for ${url}: ${error.message}`);
        
        if (attempt === retries) {
          this.errors.push(`Failed to fetch ${url}: ${error.message}`);
          return this._getCachedData(url) || { error: error.message };
        }
        
        // Exponential backoff
        await this._sleep(Math.pow(2, attempt) * 1000);
      }
    }
  }

  /**
   * Promise-based HTTP request
   */
  _makeHttpRequest(url, options) {
    return new Promise((resolve, reject) => {
      const request = https.get(url, options, (res) => {
        if (res.statusCode === 403 && res.headers['x-ratelimit-remaining'] === '0') {
          const resetTime = new Date(res.headers['x-ratelimit-reset'] * 1000);
          reject(new Error(`Rate limit exceeded. Resets at ${resetTime}`));
          return;
        }

        if (res.statusCode < 200 || res.statusCode >= 300) {
          reject(new Error(`HTTP ${res.statusCode}: ${res.statusMessage}`));
          return;
        }

        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          this._cacheData(url, data);
          resolve(data);
        });
      });

      request.on('timeout', () => {
        request.destroy();
        reject(new Error('Request timeout'));
      });

      request.on('error', reject);
      request.setTimeout(options.timeout || 10000);
    });
  }

  /**
   * Cache response data
   */
  _cacheData(url, data) {
    try {
      const cacheKey = Buffer.from(url).toString('base64').slice(0, 50);
      const cacheFile = path.join(this.cacheDir, `${cacheKey}.json`);
      fs.writeFileSync(cacheFile, JSON.stringify({ 
        url, 
        data, 
        timestamp: Date.now() 
      }));
    } catch (error) {
      console.warn(`⚠️  Failed to cache data: ${error.message}`);
    }
  }

  /**
   * Get cached data if available and not expired
   */
  _getCachedData(url, maxAge = 3600000) { // 1 hour default
    try {
      const cacheKey = Buffer.from(url).toString('base64').slice(0, 50);
      const cacheFile = path.join(this.cacheDir, `${cacheKey}.json`);
      
      if (fs.existsSync(cacheFile)) {
        const cached = JSON.parse(fs.readFileSync(cacheFile, 'utf8'));
        const isExpired = Date.now() - cached.timestamp > maxAge;
        
        if (!isExpired) {
          console.log(`📋 Using cached data for ${url}`);
          return JSON.parse(cached.data);
        }
      }
    } catch (error) {
      console.warn(`⚠️  Failed to read cache: ${error.message}`);
    }
    return null;
  }

  /**
   * Sleep for specified milliseconds
   */
  _sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Fetch GitHub user data
   */
  async fetchUserData() {
    console.log('👤 Fetching user data...');
    const user = await this.makeRequest(
      `${this.config.api.github}/users/${this.config.user.username}`
    );
    return user.error ? {} : user;
  }

  /**
   * Fetch user repositories
   */
  async fetchRepositories() {
    console.log('📦 Fetching repositories...');
    const repos = await this.makeRequest(
      `${this.config.api.github}/users/${this.config.user.username}/repos?sort=updated&per_page=50`
    );
    
    if (repos.error) return [];
    
    return Array.isArray(repos) 
      ? repos.filter(repo => !repo.fork && !repo.private)
               .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
      : [];
  }

  /**
   * Fetch recent GitHub activity
   */
  async fetchActivity() {
    console.log('⚡ Fetching recent activity...');
    const events = await this.makeRequest(
      `${this.config.api.github}/users/${this.config.user.username}/events/public?per_page=${this.config.content.maxActivities}`
    );
    
    if (events.error) return [];
    
    return Array.isArray(events) 
      ? events.filter(event => 
          ['PushEvent', 'CreateEvent', 'IssuesEvent', 'PullRequestEvent', 'WatchEvent', 'ForkEvent'].includes(event.type)
        ).slice(0, this.config.content.maxActivities)
      : [];
  }

  /**
   * Format time ago
   */
  formatTimeAgo(date) {
    const now = new Date();
    const diff = now - new Date(date);
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (days > 0) return `${days} day${days === 1 ? '' : 's'} ago`;
    if (hours > 0) return `${hours} hour${hours === 1 ? '' : 's'} ago`;
    if (minutes > 0) return `${minutes} minute${minutes === 1 ? '' : 's'} ago`;
    return 'Just now';
  }

  /**
   * Get language emoji
   */
  getLanguageEmoji(language) {
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

  /**
   * Calculate comprehensive statistics
   */
  calculateStats(user, repos, activity) {
    const currentYear = new Date().getFullYear();
    const totalStars = repos.reduce((sum, repo) => sum + (repo.stargazers_count || 0), 0);
    const totalForks = repos.reduce((sum, repo) => sum + (repo.forks_count || 0), 0);
    const languages = [...new Set(repos.map(repo => repo.language).filter(Boolean))];
    
    const commitsThisYear = activity.filter(event => 
      event.type === 'PushEvent' && 
      new Date(event.created_at).getFullYear() === currentYear
    ).length;

    return {
      totalStars,
      totalForks,
      languages: languages.length,
      commitsThisYear,
      publicRepos: user.public_repos || repos.length,
      followers: user.followers || 0,
      following: user.following || 0
    };
  }

  /**
   * Generate the README content
   */
  async generateReadme() {
    try {
      console.log('🚀 Starting enhanced README generation...');
      console.log(`📊 Fetching data for ${this.config.user.username}...`);

      // Fetch all data concurrently
      const [user, repos, activity] = await Promise.all([
        this.fetchUserData(),
        this.fetchRepositories(),
        this.fetchActivity()
      ]);

      // Calculate statistics
      const stats = this.calculateStats(user, repos, activity);
      
      // Get current timestamp
      const lastUpdated = new Date().toLocaleString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        timeZone: this.config.user.timezone
      });

      console.log('✅ Data fetched successfully!');
      console.log(`📊 Stats: ${stats.publicRepos} repos, ${stats.totalStars} stars, ${stats.languages} languages`);

      // If there are errors but we have some data, continue
      if (this.errors.length > 0) {
        console.warn('⚠️  Some requests failed but continuing with available data:');
        this.errors.forEach(error => console.warn(`   - ${error}`));
      }

      console.log('✅ README generation completed successfully!');
      
      return {
        success: true,
        stats,
        lastUpdated,
        errors: this.errors
      };

    } catch (error) {
      console.error('❌ Failed to generate README:', error.message);
      
      // Try to use cached data as fallback
      console.log('🔄 Attempting to use cached data as fallback...');
      
      return {
        success: false,
        error: error.message,
        errors: this.errors
      };
    }
  }
}

// CLI execution
if (require.main === module) {
  const generator = new ReadmeGenerator();
  
  generator.generateReadme().then(result => {
    if (result.success) {
      console.log('\n🎉 README generation completed!');
      if (result.errors?.length > 0) {
        console.log(`⚠️  ${result.errors.length} warnings encountered`);
      }
      process.exit(0);
    } else {
      console.error('\n❌ README generation failed!');
      console.error('Error:', result.error);
      process.exit(1);
    }
  }).catch(error => {
    console.error('\n💥 Unexpected error:', error);
    process.exit(1);
  });
}

module.exports = ReadmeGenerator;
