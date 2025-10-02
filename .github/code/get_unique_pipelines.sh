#!/bin/bash

ALL_OPENNEURODERIVATIVES_REPOS=$1
N_REPOS=$(wc -l < "$ALL_OPENNEURODERIVATIVES_REPOS")

OWNER="OpenNeuroDerivatives"
METADATA_FILE="dataset_description.json"
OUTPUT_FILE="openneuroderivatives_pipelines.txt"
PROBLEM_REPOS_TRACKER_FILE="dataset_description_problem_repos.tmp"

# Clear existing output file
> "$OUTPUT_FILE"

touch "$PROBLEM_REPOS_TRACKER_FILE"
counter=1
while IFS= read -r repo; do
    echo "($counter/$N_REPOS) Checking $repo"
    file_url="https://raw.githubusercontent.com/$OWNER/$repo/refs/heads/main/$METADATA_FILE"
    if content=$(curl -sfL "$file_url"); then
        n_generating_pipelines=$(jq -r '.GeneratedBy | length' <<< "$content")
        # Sanity check since GeneratedBy is a list for some reason
        if [ "$n_generating_pipelines" -ne 1 ]; then
            echo "WARNING: Dataset $repo has $n_generating_pipelines generating pipelines."
        fi

        pipeline_versions=$(jq -r '.GeneratedBy[] | "\(.Name | ascii_downcase) \(.Version)"' <<< "$content")

        if [ $? -eq 0 ]; then
            while IFS= read -r pipeline_version; do
                echo "$pipeline_version" >> "$OUTPUT_FILE"
            done <<< "$pipeline_versions"
        else
            echo "$repo" >> "$PROBLEM_REPOS_TRACKER_FILE"
        fi
    else
        echo "WARNING: $repo is missing $METADATA_FILE. Skipping."
        echo "$repo" >> "$PROBLEM_REPOS_TRACKER_FILE"
    fi
    ((counter++))
done < "$ALL_OPENNEURODERIVATIVES_REPOS"

# Sort and remove duplicates
sort -u "$OUTPUT_FILE" -o "$OUTPUT_FILE"

echo -e "\n$(wc -l < $OUTPUT_FILE) unique pipeline-version combos found."
echo -e "dataset_description.json missing or unreadable for $(wc -l < $PROBLEM_REPOS_TRACKER_FILE)/$N_REPOS repos:"
cat "$PROBLEM_REPOS_TRACKER_FILE"
echo -e "Done."

# Cleanup temp files
rm "$PROBLEM_REPOS_TRACKER_FILE"
