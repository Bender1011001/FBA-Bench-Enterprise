/* eslint-env node */
/* eslint-disable @typescript-eslint/no-var-requires, global-require */
// Production build-time environment validation for the frontend
// - Ensures no hardcoded localhost URLs are used for production-like modes
// - Supports both CRA-style (REACT_APP_*) and Vite-style (VITE_*) env vars
// - Reads .env files minimally to validate when run outside Vite's context

const fs = require('fs');
const path = require('path');

const ROOT = __dirname ? path.join(__dirname, '..') : path.resolve('..');

// Minimal .env parser (key=value, ignores comments and quotes)
function parseDotEnv(filePath) {
  if (!fs.existsSync(filePath)) return {};
  const lines = fs.readFileSync(filePath, 'utf8').split(/\r?\n/);
  const out = {};
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const idx = trimmed.indexOf('=');
    if (idx === -1) continue;
    const key = trimmed.slice(0, idx).trim();
    let val = trimmed.slice(idx + 1).trim();
    if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
      val = val.slice(1, -1);
    }
    out[key] = val;
  }
  return out;
}

// Merge envs from files into process.env for validation only (do not override existing)
function loadEnvForMode(mode) {
  const filesToLoad = [
    path.join(ROOT, '.env'),
    path.join(ROOT, `.env.${mode}`),
  ];
  for (const f of filesToLoad) {
    const parsed = parseDotEnv(f);
    for (const [k, v] of Object.entries(parsed)) {
      if (process.env[k] === undefined) process.env[k] = v;
    }
  }
}

function isLocalhostUrl(url) {
  return /^(https?:\/\/|wss?:\/\/)?(localhost|127\.0\.0\.1)(?::\d+)?/i.test(url);
}

function main() {
  const mode = process.env.MODE || process.env.NODE_ENV || 'production';
  loadEnvForMode(mode);

  const apiUrl = (process.env.VITE_API_URL || process.env.REACT_APP_API_URL || '').trim();
  const wsUrl = (process.env.VITE_WS_URL || process.env.REACT_APP_WS_URL || '').trim();
  const allowLocalhost = String(process.env.ALLOW_LOCALHOST || '').toLowerCase() === 'true';

  const isProdLike = /prod/i.test(mode) || mode === 'production';

  if (isProdLike && !allowLocalhost) {
    const offenders = [];
    if (apiUrl && isLocalhostUrl(apiUrl)) offenders.push(`API_URL=${apiUrl}`);
    if (wsUrl && isLocalhostUrl(wsUrl)) offenders.push(`WS_URL=${wsUrl}`);

    if (offenders.length) {
      console.error('[validate-env] Refusing to build with localhost URLs in production-like mode.');
      console.error('Offending values:', offenders.join(', '));
      console.error('Either set proper URLs, omit them to use same-origin, or set ALLOW_LOCALHOST=true (not recommended).');
      process.exit(1);
    }
  }

  // Success
  console.log(`[validate-env] Mode=${mode} OK. API_URL=${apiUrl || '(same-origin)'} WS_URL=${wsUrl || '(derived)'}`);
}

main();