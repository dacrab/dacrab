#!/usr/bin/env node

/**
 * 🛠️ Setup Script for Dynamic README
 * Helps configure secrets and validate setup
 */

const fs = require('fs');
const path = require('path');

console.log('🚀 Setting up Dynamic README Generator...\n');

// Check Node.js version
const nodeVersion = process.version;
const requiredVersion = '16.0.0';

if (parseInt(nodeVersion.slice(1)) < parseInt(requiredVersion)) {
  console.error(`❌ Node.js ${requiredVersion} or higher is required. Current: ${nodeVersion}`);
  process.exit(1);
}

console.log(`✅ Node.js version: ${nodeVersion}`);

// Check if running in GitHub repository
const isGitRepo = fs.existsSync('.git');
console.log(`${isGitRepo ? '✅' : '⚠️'} Git repository: ${isGitRepo ? 'Detected' : 'Not detected'}`);

// Check for required files
const requiredFiles = [
  'config.js',
  'README.template.md',
  '.github/workflows/update-readme.yml',
  'scripts/readme-generator.js'
];

console.log('\n📁 Checking required files:');
let allFilesExist = true;

requiredFiles.forEach(file => {
  const exists = fs.existsSync(file);
  console.log(`${exists ? '✅' : '❌'} ${file}`);
  if (!exists) allFilesExist = false;
});

if (!allFilesExist) {
  console.error('\n❌ Some required files are missing. Please ensure all files are in place.');
  process.exit(1);
}

// Check environment variables
console.log('\n🔐 Environment variables needed:');

const requiredSecrets = [
  { name: 'GITHUB_TOKEN', description: 'GitHub Personal Access Token (for API requests)', required: true },
  { name: 'METRICS_TOKEN', description: 'GitHub token for metrics generation', required: true },
  { name: 'WAKATIME_API_KEY', description: 'WakaTime API key for coding stats', required: false }
];

let secretsConfigured = 0;

requiredSecrets.forEach(secret => {
  const isSet = process.env[secret.name];
  const status = isSet ? '✅ Set' : (secret.required ? '❌ Missing' : '⚠️ Optional');
  console.log(`${status} ${secret.name} - ${secret.description}`);
  if (isSet) secretsConfigured++;
});

// Create .env.example file
const envExample = requiredSecrets
  .map(s => `${s.name}=your_${s.name.toLowerCase()}_here`)
  .join('\n');

fs.writeFileSync('.env.example', envExample);
console.log('\n📄 Created .env.example file for reference');

// Check GitHub Actions workflow
const workflowFile = '.github/workflows/update-readme.yml';
if (fs.existsSync(workflowFile)) {
  console.log('✅ GitHub Actions workflow is configured');
} else {
  console.log('❌ GitHub Actions workflow not found');
}

// Summary
console.log('\n📋 Setup Summary:');
console.log(`✅ Required files: ${allFilesExist ? 'All present' : 'Some missing'}`);
console.log(`🔐 Secrets configured: ${secretsConfigured}/${requiredSecrets.filter(s => s.required).length} required`);

if (allFilesExist && secretsConfigured >= requiredSecrets.filter(s => s.required).length) {
  console.log('\n🎉 Setup complete! You can now run:');
  console.log('   npm run generate  - Generate README locally');
  console.log('   git push          - Trigger GitHub Actions workflow');
} else {
  console.log('\n⚠️ Setup incomplete. Please:');
  if (!allFilesExist) {
    console.log('   - Ensure all required files are present');
  }
  if (secretsConfigured < requiredSecrets.filter(s => s.required).length) {
    console.log('   - Configure required GitHub secrets');
    console.log('   - Go to: Repository Settings → Secrets and variables → Actions');
  }
}

console.log('\n📚 Documentation: https://github.com/dacrab/dacrab#readme');
console.log('🐛 Issues: https://github.com/dacrab/dacrab/issues');
