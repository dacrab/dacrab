/**
 * 🔧 Dynamic README Configuration
 * Centralized configuration for README generation
 */

module.exports = {
  // User Configuration
  user: {
    username: 'dacrab',
    name: 'Vaggelis Kavouras',
    location: 'Greece 🇬🇷',
    timezone: 'Europe/Athens',
    email: 'hello@dacrab.dev',
    website: 'https://dacrab.github.io',
    bio: 'Solo developer passionate about crafting modern, type-safe web applications',
  },

  // Social Links
  social: {
    github: 'https://github.com/dacrab',
    linkedin: 'https://www.linkedin.com/in/vkavouras/',
    instagram: 'https://www.instagram.com/killcrb/',
    email: 'mailto:hello@dacrab.dev',
  },

  // Featured Projects
  featuredProjects: [
    {
      name: 'clubOS',
      description: 'Sports Facility Management System',
      url: 'https://clubos.vercel.app',
      repo: 'https://github.com/dacrab/clubos',
      tech: 'Next.js 14 + Supabase + TypeScript',
      features: 'Real-time POS, RBAC, Analytics',
      status: '🚧 Active Development',
      emoji: '🧑‍💼'
    },
    {
      name: 'Portfolio',
      description: 'Personal Developer Website',
      url: 'https://dacrab.github.io',
      repo: 'https://github.com/dacrab/dacrab.github.io',
      tech: 'Astro + TypeScript + TailwindCSS',
      features: 'Fast, SEO Optimized, Modern UI',
      status: '✅ Production',
      emoji: '🌐'
    },
    {
      name: 'Argicon',
      description: 'Architecture Studio Website',
      url: 'https://argicon.gr',
      repo: null,
      tech: 'Next.js + Framer Motion + i18n',
      features: 'Multilingual, Smooth Animations',
      status: '✅ Production',
      emoji: '🎯'
    },
    {
      name: 'DesignDash',
      description: 'Architecture Portfolio',
      url: 'https://designdash.gr',
      repo: null,
      tech: 'Next.js + TailwindCSS + Dark Mode',
      features: 'Portfolio Gallery, Responsive',
      status: '✅ Production',
      emoji: '🧱'
    }
  ],

  // API Configuration
  api: {
    github: 'https://api.github.com',
    wakatime: 'https://wakatime.com/api/v1',
    devto: 'https://dev.to/api',
  },

  // Content Configuration
  content: {
    maxRepos: 6,
    maxActivities: 8,
    maxBlogPosts: 5,
    maxStars: 5,
    maxPullRequests: 4,
  },

  // GitHub Actions Configuration
  actions: {
    updateInterval: '0 */6 * * *', // Every 6 hours
    timeoutMinutes: 10,
    retryAttempts: 3,
  },

  // Theme Configuration  
  theme: {
    primaryColor: '58A6FF',
    backgroundColor: '0D1117',
    textColor: 'C3D1D9',
    accentColor: 'FF6B6B',
  },

  // Skills & Technologies
  skills: {
    frontend: [
      'TypeScript', 'React', 'Next.js', 'Tailwind CSS', 'Vite', 'Astro'
    ],
    backend: [
      'Node.js', 'Supabase', 'PostgreSQL', 'Prisma'
    ],
    tools: [
      'Git', 'VS Code', 'Vercel', 'Figma', 'Docker'
    ],
    learning: [
      'Advanced TypeScript Patterns', 'System Architecture', 'GraphQL'
    ]
  }
};
