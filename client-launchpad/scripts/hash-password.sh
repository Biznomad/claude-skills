#!/bin/bash
# Generate SHA-256 hash for dashboard password
# Usage: hash-password.sh <password>
if [ -z "$1" ]; then echo "Usage: hash-password.sh <password>"; exit 1; fi
echo -n "$1" | shasum -a 256 | cut -d ' ' -f1
