#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
printf '%s\n' 'Read DEPLOYMENT.md and configure Preview environment variables first.'
npx vercel link
npx vercel
