#!/bin/bash
set -euo pipefail

OUTPUT_FILE=$1

OWNER="OpenNeuroDerivatives"

# Return every repository name excluding .github and OpenNeuroDerivatives
nRepos=$(gh api graphql -f query='{
    organization(login: "'"${OWNER}"'" ) {
        repositories {
            totalCount
        }
    }
}' | jq -r '.data.organization.repositories.totalCount')
gh repo list "$OWNER" --limit ${nRepos} --json name --jq '.[].name' | grep -v -E '^(\.github|OpenNeuroDerivatives)$' > "$OUTPUT_FILE"
