/**
 * Performance Audit Script
 *
 * Analyzes frontend performance:
 * - Bundle size
 * - Lighthouse scores (if available)
 * - Dependencies size
 *
 * Usage: node scripts/performance-audit.js
 */

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const DIST_PATH = path.join(__dirname, '../dist');
const BUILD_PATH = path.join(__dirname, '../build');

console.log('🔍 Frontend Performance Audit\n');

// Check if build exists
const outputPath = fs.existsSync(DIST_PATH) ? DIST_PATH : BUILD_PATH;

if (!fs.existsSync(outputPath)) {
  console.error('❌ No build directory found. Run "npm run build" first.');
  process.exit(1);
}

// Analyze bundle size
function analyzeBundleSize() {
  console.log('📦 Bundle Size Analysis\n');

  const assets = [];

  function scanDirectory(dir, basePath = '') {
    const items = fs.readdirSync(dir);

    for (const item of items) {
      const fullPath = path.join(dir, item);
      const stat = fs.statSync(fullPath);

      if (stat.isDirectory()) {
        scanDirectory(fullPath, path.join(basePath, item));
      } else {
        const size = stat.size;
        const sizeKB = (size / 1024).toFixed(2);
        assets.push({
          file: path.join(basePath, item),
          size: parseFloat(sizeKB),
          path: fullPath,
        });
      }
    }
  }

  scanDirectory(outputPath);

  // Sort by size (largest first)
  assets.sort((a, b) => b.size - a.size);

  // Group by type
  const jsFiles = assets.filter((a) => a.file.endsWith('.js'));
  const cssFiles = assets.filter((a) => a.file.endsWith('.css'));
  const otherFiles = assets.filter((a) => !a.file.endsWith('.js') && !a.file.endsWith('.css'));

  const totalSize = assets.reduce((sum, a) => sum + a.size, 0);
  const jsSize = jsFiles.reduce((sum, a) => sum + a.size, 0);
  const cssSize = cssFiles.reduce((sum, a) => sum + a.size, 0);

  console.log(`Total Bundle Size: ${totalSize.toFixed(2)} KB`);
  console.log(`JavaScript: ${jsSize.toFixed(2)} KB (${((jsSize / totalSize) * 100).toFixed(1)}%)`);
  console.log(`CSS: ${cssSize.toFixed(2)} KB (${((cssSize / totalSize) * 100).toFixed(1)}%)\n`);

  console.log('Top 10 Largest Files:');
  console.log('-'.repeat(60));
  assets.slice(0, 10).forEach((asset, i) => {
    const warning = asset.size > 500 ? ' ⚠️' : asset.size > 244 ? ' 📄' : '';
    console.log(`${i + 1}. ${asset.file.padEnd(40)} ${asset.size.toFixed(2).padStart(8)} KB${warning}`);
  });

  // Performance budget check
  console.log('\n📊 Performance Budget Check:');
  console.log('-'.repeat(60));

  const budgets = {
    'Total Bundle': { limit: 500, actual: totalSize },
    'JavaScript': { limit: 300, actual: jsSize },
    'CSS': { limit: 50, actual: cssSize },
    'Largest JS Chunk': { limit: 244, actual: jsFiles[0]?.size || 0 },
  };

  for (const [name, { limit, actual }] of Object.entries(budgets)) {
    const status = actual > limit ? '❌ FAIL' : '✅ PASS';
    const color = actual > limit ? '\x1b[31m' : '\x1b[32m';
    const reset = '\x1b[0m';
    console.log(`${color}${status}${reset} ${name}: ${actual.toFixed(2)} KB / ${limit} KB`);
  }

  return { totalSize, jsSize, cssSize, assets };
}

// Analyze dependencies
function analyzeDependencies() {
  console.log('\n\n📚 Dependency Analysis\n');

  try {
    const packageJson = JSON.parse(fs.readFileSync(path.join(__dirname, '../package.json'), 'utf8'));

    const deps = Object.keys(packageJson.dependencies || {});
    const devDeps = Object.keys(packageJson.devDependencies || {});

    console.log(`Production Dependencies: ${deps.length}`);
    console.log(`Dev Dependencies: ${devDeps.length}`);

    // Check for known heavy dependencies
    const heavyDeps = [
      'recharts',
      '@auth0/auth0-react',
      'axios',
      'zustand',
      'react-router-dom',
    ];

    console.log('\nKey Dependencies:');
    heavyDeps.forEach((dep) => {
      if (deps.includes(dep) || devDeps.includes(dep)) {
        const version = packageJson.dependencies[dep] || packageJson.devDependencies[dep];
        console.log(`  • ${dep}@${version}`);
      }
    });

    return { deps, devDeps };
  } catch (error) {
    console.error('Error reading package.json:', error.message);
    return null;
  }
}

// Lighthouse recommendations
function lighthouseRecommendations() {
  console.log('\n\n💡 Lighthouse Recommendations\n');

  const recommendations = [
    {
      category: 'Performance',
      items: [
        'Enable gzip/brotli compression on server',
        'Use CDN for static assets',
        'Implement code splitting for routes',
        'Lazy load heavy components (Recharts)',
        'Optimize images with WebP format',
        'Add preconnect hints for API endpoints',
      ],
    },
    {
      category: 'Accessibility',
      items: [
        'Ensure all images have alt text',
        'Check color contrast ratios',
        'Add ARIA labels to interactive elements',
        'Test keyboard navigation',
      ],
    },
    {
      category: 'Best Practices',
      items: [
        'Use HTTPS in production',
        'Implement Content Security Policy',
        'Add service worker for offline support',
        'Monitor Core Web Vitals',
      ],
    },
  ];

  recommendations.forEach(({ category, items }) => {
    console.log(`${category}:`);
    items.forEach((item) => console.log(`  • ${item}`));
    console.log();
  });
}

// Main execution
console.log('=' .repeat(60));
const bundleStats = analyzeBundleSize();
analyzeDependencies();
lighthouseRecommendations();

console.log('=' .repeat(60));
console.log('\n✨ Audit Complete!\n');

// Exit with error if budget exceeded
const budgetsExceeded = [
  bundleStats.totalSize > 500,
  bundleStats.jsSize > 300,
  bundleStats.cssSize > 50,
].some(Boolean);

if (budgetsExceeded) {
  console.log('⚠️  Some performance budgets were exceeded.\n');
  process.exit(1);
} else {
  console.log('✅ All performance budgets met!\n');
  process.exit(0);
}
