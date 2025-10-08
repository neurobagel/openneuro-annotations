import argparse
import base64
import configparser
import json
import logging
import os
import sys
from collections import defaultdict
from pathlib import Path

import requests


ORG_OWNER = 'OpenNeuroDerivatives'


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('build_repo_map.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("processing")


def get_file(repo, file_path, token, branch='main'):
    headers = {}
    if token:
        headers['Authorization'] = f'token {token}'
    
    url = f'https://api.github.com/repos/{ORG_OWNER}/{repo}/contents/{file_path}'
    params = {'ref': branch}
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 404:
        return None
    
    response.raise_for_status()
    return response


def get_submodule_url(content, submodule_path) -> str:
    # .gitmodule is INI format, which configparser handles
    # Some repos have duplicate keys in a section in .gitmodules, so we need strict=False
    # to allow this (NOTE: last occurrence takes precedence)
    config = configparser.ConfigParser(strict=False)
    config.read_string(content)
    
    for section in config.sections():
        if config.has_option(section, 'path'):
            if config.get(section, 'path') == submodule_path:
                return config.get(section, 'url')
    return None


def get_name_from_url(url: str) -> str:
    return url.split('/')[-1].removesuffix('.git')


def get_pipeline_info(repo_name, token) -> dict:
    response = get_file(repo_name, file_path='dataset_description.json', token=token)
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


def get_parent(repo_name, token) -> tuple[str, str]:
    submodule_path = 'sourcedata/raw'
    # Get the file
    response = get_file(repo_name, file_path='.gitmodules', token=token)
    # Process the response
    content = get_content(response)
    # Parse the file
    parent_url = get_submodule_url(content, submodule_path)
    # Parse the name of the parent
    if parent_url:
        parent_name = get_name_from_url(parent_url)
        if parent_name:
            return (parent_url, parent_name)
        else:
            logger.warning(f"    {repo_name} has a parent, but we cannot identify the parent name from the .gitmodules file")

    else:
        logger.info(f"    {repo_name} does not have a parent: {repo_name}")

    return ('', '')


def get_content(response):
    return base64.b64decode(response.json()['content']).decode('utf-8')


def main(repo_name: str, map_file_path: Path, token: str):
    
    if map_file_path.exists():
        with open(map_file_path, "r") as f:
            loaded_dict = json.load(f)
    else:
        loaded_dict = {}
   # start with the contents of loaded_dict, but ensure that any new (non-existent) key
   # accessed later will default to having a value of empty dict `{}`,
   # allowing nested updates without needing to check for key existence.
    map_dict = defaultdict(dict, loaded_dict)
    
    try:
        parent_url, parent_name = get_parent(repo_name=repo_name, token=token)
        if parent_url:
            pipeline_info = get_pipeline_info(repo_name=repo_name, token=token)
            map_dict[parent_name][repo_name] = pipeline_info
    except Exception as e:
        logger.error(f"Error while processing {repo_name}: {e}")
        
    with open(map_file_path, "w") as f:
        json.dump(map_dict, f, indent=2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Map an OpenNeuroDerivative repo to its parent OpenNeuroDataset repo and store its pipeline information")
    parser.add_argument('repo_name', type=str, help='Name of the derivative repo to run on')
    parser.add_argument('map_file', type=str, help='Path to the .json repo map file')
    args = parser.parse_args()

    token = os.environ.get('NB_TOKEN', 'nix')
    main(args.repo_name, Path(args.map_file), token)