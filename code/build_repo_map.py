import os
from pathlib import Path
import json
from collections import defaultdict
import base64
import argparse

import tqdm
import pandas as pd
import requests
import configparser
import logging


# Set up logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('build_repo_map.log', mode='w'),
    ]
)
logger = logging.getLogger("processing")


def get_file(owner, repo, file_path, token, branch='main'):
    headers = {}
    if token:
        headers['Authorization'] = f'token {token}'
    
    # Fetch .gitmodules file from GitHub
    url = f'https://api.github.com/repos/{owner}/{repo}/contents/{file_path}'
    params = {'ref': branch}
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 404:
        return None
    
    response.raise_for_status()
    return response


def get_submodule_url(content, submodule_path):
    # .gitmodule is INI format, which configparser handles
    # Some repos have duplicate entires in .gitmodule, so we need strict=False
    config = configparser.ConfigParser(strict=False)
    config.read_string(content)
    
    for section in config.sections():
        if config.has_option(section, 'path'):
            if config.get(section, 'path') == submodule_path:
                return config.get(section, 'url')
    return None


def get_name_from_url(url: str) -> str:
    return url.split('/')[-1].strip('.git')


def get_pipeline_info(repo_name, token) -> dict:
    owner = 'OpenNeuroDerivatives'
    response = get_file(owner, repo_name, file_path='dataset_description.json', token=token)
    if response is None:
        logger.debug(f"{repo_name} has no dataset_description.json")
        return {}

    content  = get_content(response)
    dataset_description = json.loads(content)
    pipeline_info = dataset_description.get('GeneratedBy')
    
    if pipeline_info:
        return {
            'name': pipeline_info[0].get('Name'),
            'version': pipeline_info[0].get('Version')
        }
    return {}


def get_parent(repo_name, token):
    owner = 'OpenNeuroDerivatives'
    submodule_path = 'sourcedata/raw'
    # Get the file
    response = get_file(owner, repo_name, file_path='.gitmodules', token=token)
    # Process the response
    content  = get_content(response)
    # Parse the file
    parent_url = get_submodule_url(content, submodule_path)
    # Parse the name of the parent
    if parent_url:
        parent_name = get_name_from_url(parent_url)
        return (parent_url, parent_name)
    
    logger.info(f"    {repo_name} does not have a parent: {repo_name}")
    return (None, None)


def get_content(response):
    return base64.b64decode(response.json()['content']).decode('utf-8')


def main(repo_table: Path, token: str):
    
    repo_rows = pd.read_csv(repo_table, sep='\t', header=None).to_records()
    map_dict = defaultdict(dict)
    
    
    for (_, repo_name, repo_url) in tqdm.tqdm(repo_rows, desc="Processing repos"):
        try:
            parent_url, parent_name = get_parent(repo_name=repo_name, token=token)
            if parent_url:
                pipeline_info = get_pipeline_info(repo_name=repo_name, token=token)
                map_dict[parent_name][repo_name] = pipeline_info
        except Exception as e:
            logger.error(f"Error while processing {repo_name}: {e}")
        
    with open("outfile.json", "w") as f:
        json.dump(map_dict, f, indent=2)


# Example usage
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Build repo map from a TSV of derivative repos")
    parser.add_argument('input', type=str, help='Path to input TSV (repo_name <tab> repo_url)')
    args = parser.parse_args()

    table_path = Path(args.input)
    token = os.environ.get('NB_TOKEN', '')
    main(table_path, token)