import os
import json
import requests
import re
from time import time, strftime, gmtime

GITHUB_USERNAME = 'GitPaulo'
GITHUB_API_TOKEN = os.getenv('GITHUB_TOKEN') 
HEADERS = {'Authorization': f'token {GITHUB_API_TOKEN}'}

# GitHub API URL to list all repos for a user
REPO_SEARCH_API_URL = f'https://api.github.com/users/{GITHUB_USERNAME}/repos'
REPO_JSON_URL = 'https://raw.githubusercontent.com/{}/{}/master/repo.json'
README_FILE = 'README.md'

def main():
    # Fetch all repos with "dalamud" tag
    dalamud_repos = get_dalamud_repos()
    # Process each repo and aggregate the plugin data
    master_manifest = [fetch_repo_json(repo) for repo in dalamud_repos if repo]
    master_manifest = [manifest for manifest in master_manifest if manifest]  # Filter out None entries

    # Write the consolidated repo JSON file
    write_master_json(master_manifest)
    
    # Generate and update the markdown table in README
    update_readme_with_table(master_manifest)

def get_dalamud_repos():
    response = requests.get(REPO_SEARCH_API_URL, headers=HEADERS)
    response.raise_for_status()
    repos = response.json()
    return [repo for repo in repos if 'dalamud' in repo.get('topics', [])]

def fetch_repo_json(repo):
    repo_name = repo['name']
    repo_json_url = REPO_JSON_URL.format(GITHUB_USERNAME, repo_name)
    
    response = requests.get(repo_json_url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Error fetching repo.json for {repo_name}: {response.status_code}")
        return None
    
    try:
        manifest = response.json()[0]  # Each repo.json is expected to be a list; take the first entry
    except (json.JSONDecodeError, IndexError) as e:
        print(f"Error parsing JSON for {repo_name}: {e}")
        return None
    
    # Add last update time (ISO format) - use _ to bypass manifest validation
    manifest['_LastUpdate'] = strftime("%Y-%m-%d", gmtime(time()))
    
    return manifest

def write_master_json(master):
    with open('pluginmaster.json', 'w') as f:
        json.dump(master, f, indent=4)

def update_readme_with_table(master_manifest):
    # Generate the markdown table for plugins
    table = "| Name | Description | Version | Last Updated |\n"
    table += "|------|-------------|---------|--------------|\n"
    for plugin in master_manifest:
        table += f"| {plugin['Name']} | {plugin['Description']} | {plugin['AssemblyVersion']} | {plugin['_LastUpdate']} |\n"

    # Load README file and update the ## Plugins section
    with open(README_FILE, 'r') as f:
        readme_content = f.read()

    # Regex to find the Plugins section and replace it with the new table
    new_content = re.sub(
        r"(## Plugins\s*\n)(.*?)(\n##|$)",
        rf"\1{table}\3",
        readme_content,
        flags=re.DOTALL
    )

    # Write updated content back to README file
    with open(README_FILE, 'w') as f:
        f.write(new_content)

if __name__ == '__main__':
    main()
