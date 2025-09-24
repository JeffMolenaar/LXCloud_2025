#!/usr/bin/env bash
# Convenience script to build and start LXCloud from the project folder
set -e
cd "$(dirname "$0")"
if [ ! -f docker-compose.yml ]; then
  echo "docker-compose.yml not found in project/. Run scripts/bootstrap_project.ps1 to create project/ or copy files."
  exit 1
fi

echo "Building and starting LXCloud (docker-compose)"
docker-compose up --build -d

echo "Services started. Use: docker-compose ps" 
