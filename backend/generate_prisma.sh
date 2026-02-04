#!/usr/bin/env bash
# Generate Prisma Client Python. Requires venv bin on PATH so the Node Prisma CLI
# can find the prisma-client-py generator.
set -e
cd "$(dirname "$0")"
PATH="$(pwd)/.venv/bin:$PATH" .venv/bin/prisma generate
