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
  'README.template.md',
  '.github/workflows/update-readme.yml',
  'package.json'
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
console.log('\n🎉 No secrets or environment variables needed!');
console.log('✅ GitHub Actions uses built-in GITHUB_TOKEN automatically');

let secretsConfigured = 1; // Always configured since GITHUB_TOKEN is built-in

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
console.log(`🔐 Secrets: ✅ No setup required (uses built-in GITHUB_TOKEN)`);

if (allFilesExist) {
  console.log('\n🎉 Setup complete! Your repository is ready to go:');
  console.log('   git push          - Trigger GitHub Actions workflow');
  console.log('   Manual trigger    - Go to Actions tab → Run workflow');
  console.log('   Automatic updates - Every 6 hours via scheduled workflow');
} else {
  console.log('\n⚠️ Setup incomplete. Please ensure all required files are present.');
}

console.log('\n📚 Documentation: https://github.com/dacrab/dacrab#readme');
console.log('🐛 Issues: https://github.com/dacrab/dacrab/issues');
