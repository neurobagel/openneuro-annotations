#!/bin/bash
set -euo pipefail

DS_ID=$1
DS_URL="https://github.com/OpenNeuroDatasets/${DS_ID}.git"

# NOTE: Double check paths in context of wf runner
SCRIPT_DIR="$(dirname "$(realpath "$0")")"
DERIVATIVES_REPO_MAP="${SCRIPT_DIR}/../dataset_derivatives_mapping.json"
SOURCE_WORKDIR="derivatives/source"
NIPOPPY_WORKDIR="derivatives/nipoppy"
TEMPLATE_CONFIGS_DIR="derivatives/template_pipeline_configs"
NIPOPPY_DATASET_DIR="${NIPOPPY_WORKDIR}/${DS_ID}"

mkdir -p ${SOURCE_WORKDIR}
mkdir -p ${NIPOPPY_WORKDIR}

git clone -q ${DS_URL} ${SOURCE_WORKDIR}/${DS_ID}
echo "${DS_ID}: Initializing Nipoppy dataset"
# NOTE: The BIDS dataset is symlinked by default
nipoppy init --dataset ${NIPOPPY_DATASET_DIR} --bids-source ${SOURCE_WORKDIR}/${DS_ID}

# This creates a multi-line string variable
derivative_datasets="$(jq -r --arg ds "$DS_ID" '.[ $ds ] | keys[]' "$DERIVATIVES_REPO_MAP")"

has_no_ses=0
if ! python ${SCRIPT_DIR}/does_dataset_have_sessions.py "$DS_ID" "$NIPOPPY_DATASET_DIR/bids"; then
    has_no_ses=1
    echo "${DS_ID}: No sessions found."
fi

while IFS= read -r derivative_ds; do
    pipeline_info="$(jq -c --arg ds "$DS_ID" --arg repo "$derivative_ds" '.[ $ds ][ $repo ]' "$DERIVATIVES_REPO_MAP")"

    # Check that the derivative dataset has pipeline info
    if [ "$pipeline_info" != "{}" ]; then
        echo "${DS_ID}: Cloning derivative dataset ${derivative_ds}"
        derivative_ds_url="https://github.com/OpenNeuroDerivatives/${derivative_ds}.git"
        pipeline_name=$(jq -r '.name | ascii_downcase' <<< "$pipeline_info")
        pipeline_version=$(jq -r '.version' <<< "$pipeline_info")
        derivative_dir="${NIPOPPY_DATASET_DIR}/derivatives/${pipeline_name}/${pipeline_version}/output"
        mkdir -p "${derivative_dir}"
        git clone -q "${derivative_ds_url}" "${derivative_dir}"

        pipeline_config_dir="${NIPOPPY_DATASET_DIR}/pipelines/processing/${pipeline_name}-${pipeline_version}"
        mkdir -p "${pipeline_config_dir}"

        args=(
            "${TEMPLATE_CONFIGS_DIR}/${pipeline_name}/config.json"
            "${TEMPLATE_CONFIGS_DIR}/${pipeline_name}/tracker.json"
            "${pipeline_version}"
            "${pipeline_config_dir}"
        )
        if [ $has_no_ses -eq 1 ]; then
            args+=("--no-sessions")
        fi
        echo "${DS_ID}: Customizing config.json and tracker.json files for ${derivative_ds}"
        python ${SCRIPT_DIR}/customize_configs_for_pipeline.py "${args[@]}"
    else
        echo "${DS_ID}: WARNING No pipeline info found for ${derivative_ds} in ${DERIVATIVES_REPO_MAP}, skipping."
    fi

done <<< "$derivative_datasets"

echo "${DS_ID}: Done."
