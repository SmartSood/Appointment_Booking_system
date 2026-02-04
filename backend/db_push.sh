#!/usr/bin/env bash
# Push backend Prisma schema to the database.
# Uses only backend/.env to avoid conflict with root .env (Prisma errors if both define DATABASE_URL).
set -e
cd "$(dirname "$0")"
ROOT_ENV="../.env"
if [ -f "$ROOT_ENV" ]; then
  mv "$ROOT_ENV" "../.env.bak"
  trap 'mv "../.env.bak" "../.env"' EXIT
fi
npx prisma db push --schema=prisma/schema.prisma --skip-generate
echo "Database is in sync with backend/prisma/schema.prisma"
