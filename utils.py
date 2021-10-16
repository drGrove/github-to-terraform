import base64
import json
import os
import re

import requests

BEARER_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_GQL_ENDPOINT = os.environ.get("GITHUB_GQL_ENDPOINT", "https://api.github.com/graphql")
LOGIN = os.environ.get('GITHUB_LOGIN')

headers = {
    "Authorization": f"bearer {BEARER_TOKEN}"
}


def run_query(query):
    request = requests.post(
        f"{GITHUB_GQL_ENDPOINT}",
        json={'query': query},
        headers=headers
    )

    if request.status_code == 200:
        data = request.json()
    else:
        raise Exception(f"Query failed to run by returning code of {request.status_code}. {query}")

    if data.get('errors'):
        raise Exception(f"Query failed to run by returning code of {request.status_code} and Error: {data.get('errors')}. {query}")

    return data


def simplify(name):
    name = name.lower()
    result = ""
    for _, char in enumerate(name):
        if ord(char) >= 97 and ord(char) <= 122:
            result += f"{char}"
        if ord(char) >= 48 and ord(char) <= 57:
            result += f"{char}"
        if char == "_" or char == " " or char == "-":
            result += "_"


    return re.sub(r'_+', '_', result)

def unique(in_data):
    data = set()
    for row in in_data:
        data.add(base64.b64encode(json.dumps(row).encode('utf-8')))
    return [json.loads(base64.b64decode(row)) for row in data]

def get_all_teams(query):
    data = run_query(query)
    teams = data.get('data').get('organization').get('teams')
    output = teams.get('edges')
    count = len(teams.get('edges'))
    total_count = teams.get('totalCount')
    while True:
        teams_filter = f"first: 100, after: '{teams.get('pageInfo').get('endCursor')}'"
        teams = run_query(query).get('data').get('organization').get('teams')
        count += len(teams.get('edges'))
        output += teams.get('edges')
        if count > total_count:
            break
    return sorted(unique(output), key = lambda t: simplify(t['node']['name']))


def get_private_repositories(query):
    data = run_query(query)
    repos = data.get('data').get('organization').get('repositories')
    count = len(repos.get('edges'))
    total_count = repos.get('totalCount')
    output = repos.get('edges')
    while True:
        repo_filters = f"isFork: false, first: 100, after: '{repos.get('pageInfo').get('endCursor')}'"
        repos = run_query(query).get('data').get('organization').get('repositories')
        count += len(repos.get('edges'))
        output += repos.get('edges')
        if count > total_count:
            break
    return sorted(unique(output), key = lambda t: simplify(t['node']['name']))

def get_repositories(repository_filter="first: 100"):
    query = f"""
    {{
        organization(login: "{LOGIN}") {{
            repositories({repository_filter}) {{
                totalCount,
                nodes {{
                    name,
                    description,
                    homepageUrl,
                    isPrivate,
                    visibility,
                    hasIssuesEnabled,
                    hasProjectsEnabled,
                    hasWikiEnabled,
                    mergeCommitAllowed,
                    squashMergeAllowed,
                    rebaseMergeAllowed,
                    deleteBranchOnMerge,
                }}
                pageInfo {{
                  endCursor
                  hasNextPage
                }}
            }}
        }}
    }}
    """
    data = run_query(query)
    repos = data.get('data').get('organization').get('repositories')
    output = repos.get('nodes')
    hasNextPage = repos.get('pageInfo').get('hasNextPage')
    if hasNextPage:
        end_cursor = repos.get('pageInfo').get('endCursor')
        repository_filter = f'first: 100, after: "{end_cursor}"'
        output += get_repositories(repository_filter)
    return sorted(output, key = lambda t: simplify(t['name']))


def get_all_users(query):
    data = run_query(query)
    users = data.get('data').get('organization').get('membersWithRole')
    count = len(users.get('edges'))
    total_count = users.get('totalCount')
    output = users.get('edges')
    while True:
        users_filters = f"first: 100, after: '{users.get('pageInfo').get('endCursor')}'"
        users = run_query(query).get('data').get('organization').get('membersWithRole')
        count += len(users.get('edges'))
        output += users.get('edges')
        if count > total_count:
            break
    return sorted(unique(output), key = lambda t: simplify(t['node']['login']))

def bool_to_str(boolean):
    if boolean:
        return "true"
    else:
        return "false"
