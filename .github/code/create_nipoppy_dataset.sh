#!/bin/bash
set -euo pipefail

DS_ID=ds000001
DS_URL="https://github.com/OpenNeuroDatasets/${DS_ID}.git"

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
# NOTE: Double check paths in context of wf runner
DERIVATIVES_REPO_MAP="${SCRIPT_DIR}/../dataset_derivatives_mapping.json"
echo "Dataset derivatives mapping file: ${DERIVATIVES_REPO_MAP}"

# NOTE: Double check paths in context of wf runner
SOURCE_WORKDIR="derivatives/source"
NIPOPPY_WORKDIR="derivatives/nipoppy"
NIPOPPY_DATASET_DIR="${NIPOPPY_WORKDIR}/${DS_ID}"
mkdir -p ${SOURCE_WORKDIR}
mkdir -p ${NIPOPPY_WORKDIR}

git clone -q ${DS_URL} ${SOURCE_WORKDIR}/${DS_ID}
echo "${DS_ID}: Initializing Nipoppy dataset"
# NOTE: The BIDS dataset is symlinked by default
nipoppy init --dataset ${NIPOPPY_DATASET_DIR} --bids-source ${SOURCE_WORKDIR}/${DS_ID}

# This creates a multi-line string variable
derivative_datasets="$(jq -r --arg ds "$DS_ID" '.[ $ds ] | keys[]' "$DERIVATIVES_REPO_MAP")"

# TODO: Decide what happens if no name or version are available (e.g., no dataset_description.json)
while IFS= read -r derivative_ds; do
    echo "${DS_ID}: Cloning derivative dataset ${derivative_ds}"
    derivative_ds_url="https://github.com/OpenNeuroDerivatives/${derivative_ds}.git"
    pipeline_name=$(jq -r --arg ds "$DS_ID" --arg repo "$derivative_ds" '.[ $ds ][ $repo ].name | ascii_downcase' "$DERIVATIVES_REPO_MAP")
    pipeline_version=$(jq -r --arg ds "$DS_ID" --arg repo "$derivative_ds" '.[ $ds ][ $repo ].version' "$DERIVATIVES_REPO_MAP")
    derivative_dir="${NIPOPPY_DATASET_DIR}/derivatives/${pipeline_name}/${pipeline_version}/output"
    mkdir -p "${derivative_dir}"
    git clone -q "${derivative_ds_url}" "${derivative_dir}"
done <<< "$derivative_datasets"

echo "${DS_ID}: Done."
