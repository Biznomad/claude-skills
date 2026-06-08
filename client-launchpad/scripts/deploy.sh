#!/bin/bash
# Deploy a directory to Netlify
# Usage: deploy.sh <site-name> <directory>
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: deploy.sh <site-name> <directory>"
    exit 1
fi
cd "$2" && npx netlify-cli deploy --create-site "$1" --dir . --prod
echo "Done: https://${1}.netlify.app"
