/* eslint-env node */
/* eslint-disable @typescript-eslint/no-var-requires */
// Post-build verification to ensure production readiness
// - Fails if any built asset contains hardcoded localhost references
// - Verifies dist folder exists and has an index.html

/* eslint-env node */

const fs = require('fs');
const path = require('path');

const DIST_DIR = path.join(__dirname, '..', 'dist');

function fail(msg) {
  console.error(`[verify-build] ${msg}`);
  process.exit(1);
}

function checkDistExists() {
  if (!fs.existsSync(DIST_DIR)) {
    fail(`Build output not found: ${DIST_DIR}`);
  }
  const indexHtml = path.join(DIST_DIR, 'index.html');
  if (!fs.existsSync(indexHtml)) {
    fail('index.html not found in dist');
  }
}

function walk(dir) {
  const res = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) res.push(...walk(full));
    else res.push(full);
  }
  return res;
}

function checkForLocalhost() {
  const files = walk(DIST_DIR);
  const textLike = files.filter(f => /\.(html|js|css|map|json|txt)$/i.test(f));
  const offenders = [];
  const re = /\b(?:https?:\/\/|wss?:\/\/)?(?:localhost|127\.0\.0\.1)(?::\d+)?\b/i;

  for (const f of textLike) {
    try {
      const content = fs.readFileSync(f, 'utf8');
      if (re.test(content)) {
        offenders.push(path.relative(DIST_DIR, f));
      }
    } catch {
      // ignore binary or read issues
    }
  }

  if (offenders.length) {
    fail(`Found localhost references in built assets: ${offenders.join(', ')}`);
  }
}

function main() {
  checkDistExists();
  checkForLocalhost();
  console.log('[verify-build] Build verified OK. No localhost references detected.');
}

main();