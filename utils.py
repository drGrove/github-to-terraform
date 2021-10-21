import base64
import json
import os
import re
import sys

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.exceptions import TransportQueryError

BEARER_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_GQL_ENDPOINT = os.environ.get("GITHUB_GQL_ENDPOINT", "https://api.github.com/graphql")
LOGIN = os.environ.get('GITHUB_LOGIN')

headers = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Content-Type": "application/json",
}

transport = RequestsHTTPTransport(
    url=GITHUB_GQL_ENDPOINT,
    headers=headers,
    use_json=True,
    retries=3,
)
client = Client(
    transport=transport,
    fetch_schema_from_transport=False,
)

class ForbiddenAccessError(Exception):
    pass


def run_query(query):
    try:
        query = gql(query)
        return client.execute(query)
    except TransportQueryError as e:
        raise ForbiddenAccessError()


def simplify(name):
    name = name.lower()
    result = ""
    for idx, char in enumerate(name):
        if idx == 0:
            if ord(char) >= 48 and ord(char) <= 57:
                continue
        if ord(char) >= 97 and ord(char) <= 122:
            result += f"{char}"
        if ord(char) >= 48 and ord(char) <= 57:
            result += f"{char}"
        if char == "_" or char == " " or char == "-" or char == "/":
            result += "_"
        if char == "*":
            result += "wildcard"


    return re.sub(r'_+', '_', result)

def unique(in_data):
    data = set()
    for row in in_data:
        data.add(base64.b64encode(json.dumps(row).encode('utf-8')))
    return [json.loads(base64.b64decode(row)) for row in data]

def get_all_teams(teams_filter = "first: 100"):
    query = f"""
    {{
        organization(login: "{LOGIN}") {{
            id
            name,
            teams({teams_filter}) {{
                pageInfo {{
                    endCursor,
                }},
                totalCount,
                nodes {{
                    id
                    databaseId,
                    name,
                    description,
                    privacy,
                    parentTeam {{
                        id,
                        name,
                    }},
                    members(membership:IMMEDIATE) {{
                        edges {{
                            role,
                            node {{
                                login,
                            }},
                        }},
                    }},
                }},
            }},
        }},
    }}
    """
    data = run_query(query)
    teams = data['organization']['teams']
    hasNextPage = teams.get('hasNextPage')
    output = teams.get('nodes')
    endCursor = teams.get('pageInfo').get('endCursor')
    if hasNextPage:
        teams_filter = f"first: 100, after: '{endCursor}'"
        output += get_all_teams(teams_filter)
    return sorted(unique(output), key = lambda t: simplify(t['name']))

def get_team_repositories(team_name, repository_filter = "first: 100"):
    query = f"""
    {{
        organization(login: "{LOGIN}") {{
            teams(query: "{team_name}", first: 1) {{
                nodes {{
                    id
                    repositories({repository_filter}) {{
                        edges {{
                            permission,
                            node {{
                                name
                            }}
                        }}
                        pageInfo {{
                            endCursor
                            hasNextPage
                        }}
                    }}
                }}
            }}
        }}
    }}
    """
    data = run_query(query)
    team = data.get('organization').get('teams').get('nodes')[0]
    repos = team.get('repositories').get('edges')
    hasNextPage = team.get('repositories').get('pageInfo').get('hasNextPage')
    endCursor = team.get('repositories').get('pageInfo').get('endCursor')
    if hasNextPage:
        repos += get_team_repositories(team_name, repository_filter=f'first: 100, after: "{endCursor}"')
    return sorted(unique(repos), key = lambda t: simplify(t['node']['name']))


def get_private_repositories(query):
    data = run_query(query)
    repos = data.get('organization').get('repositories')
    count = len(repos.get('edges'))
    total_count = repos.get('totalCount')
    output = repos.get('edges')
    while True:
        repo_filters = f"isFork: false, first: 100, after: '{repos.get('pageInfo').get('endCursor')}'"
        repos = run_query(query).get('organization').get('repositories')
        count += len(repos.get('edges'))
        output += repos.get('edges')
        if count > total_count:
            break
    return sorted(unique(output), key = lambda t: simplify(t['node']['name']))

def get_branch_protection_rules(
        owner,
        repository_name,
        branch_protection_filter = "first: 100"
):
    review_dismissal_allowances_filter = "first: 100"
    push_allowances_filter = "first: 100"
    query = f"""
    {{
        repository(owner: "{owner}", name: "{repository_name}") {{
            branchProtectionRules({branch_protection_filter}) {{
                nodes {{
                    allowsDeletions,
                    allowsForcePushes,
                    pattern,
                    isAdminEnforced,
                    requiredApprovingReviewCount,
                    requiredStatusCheckContexts,
                    requiresApprovingReviews,
                    requiresCodeOwnerReviews,
                    requiresCommitSignatures,
                    requiresConversationResolution,
                    requiresLinearHistory,
                    requiresStatusChecks,
                    requiresStatusChecks,
                    requiresStrictStatusChecks,
                    restrictsPushes,
                    restrictsReviewDismissals,
                    dismissesStaleReviews,
                    pushAllowances({push_allowances_filter}) {{
                        nodes {{
                            actor {{
                                ... on App {{
                                    __typename
                                    name
                                }}
                                ... on Team {{
                                    __typename
                                    name
                                }}
                                ... on User {{
                                    __typename
                                    login
                                }}
                            }}
                        }}
                        pageInfo {{
                            endCursor,
                            hasNextPage,
                        }},
                        totalCount,
                    }},
                    reviewDismissalAllowances({review_dismissal_allowances_filter}) {{
                        nodes {{
                            actor {{
                                ... on Team {{
                                    __typename
                                    name
                                }}
                                ... on User {{
                                    __typename
                                    name
                                }}
                            }}
                        }}
                        pageInfo {{
                            endCursor,
                            hasNextPage
                        }},
                        totalCount
                    }},
                }},
                pageInfo {{
                    endCursor
                    hasNextPage
                }},
                totalCount
            }}
        }}
    }}
    """
    data = run_query(query)
    repo = data.get('repository')
    output = repo.get('branchProtectionRules').get('nodes')
    hasNextPage = repo.get('branchProtectionRules').get('hasNextPage')
    if hasNextPage:
        end_cursor = repo.get('branchProtectionRules').get('pageInfo').get('endCursor')
        fltr = f"first: 100, after: {end_cursor}"
        output += get_branch_protection_rules(owner, repository_name, fltr)
    return output

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
                    isArchived,
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
    repos = data.get('organization').get('repositories')
    output = repos.get('nodes')
    hasNextPage = repos.get('pageInfo').get('hasNextPage')
    if hasNextPage:
        end_cursor = repos.get('pageInfo').get('endCursor')
        repository_filter = f'first: 100, after: "{end_cursor}"'
        output += get_repositories(repository_filter)
    return sorted(output, key = lambda t: simplify(t['name']))


def  get_collaborators_for_repository(repo_name, affiliation="ALL",
        collaborators_filter="first: 100", owner=LOGIN):
    collaborators_filter += f", affiliation: {affiliation}"
    query = f"""
    {{
      repository(owner: "{owner}", name: "{repo_name}") {{
        collaborators({collaborators_filter}) {{
          pageInfo {{
            endCursor
            hasNextPage
          }}
          edges {{
            permission,
            node {{
              login
            }}
          }}
        }}
      }}
    }}
    """
    data = run_query(query)
    collaborators = data['repository']['collaborators']
    hasNextPage = collaborators.get('pageInfo').get('hasNextPage')
    end_cursor = collaborators.get('pageInfo').get('endCursor')
    output = collaborators.get('edges')
    if hasNextPage:
        collaborators_filter = f"first: 100, after: {end_cursor}"
        output += get_collaborators_for_repository(
            repo_name,
            affiliation=affiliation,
            collaborators_filter=collaborators_filter,
            owner=owner
        )
    return output

def get_all_users(query):
    data = run_query(query)
    users = data.get('organization').get('membersWithRole')
    count = len(users.get('edges'))
    total_count = users.get('totalCount')
    output = users.get('edges')
    while True:
        users_filters = f"first: 100, after: '{users.get('pageInfo').get('endCursor')}'"
        users = run_query(query).get('organization').get('membersWithRole')
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

def tf_context_for_contexts(contexts):
    output = []
    count = len(contexts)
    for idx, context in enumerate(contexts):
        ctx = f'"{context}"'
        if idx < count - 1:
            ctx += ","
        output.append(ctx)
    return output

def tf_resource_for_actor(actor):
    typename = actor.get('__typename')
    output = ""
    if typename == "User":
        output = f"github_user.{simplify(actor.get('login'))}.node_id"
    elif typename == "Team" or typename == "App":
        output = f"github_team.{simplify(actor.get('name'))}.node_id"
    return output

def tf_resources_for_actors(actors):
    output = []
    count = len(actors)
    for idx, actor in enumerate(actors):
        resource = tf_resource_for_actor(actor)
        if idx < count - 1:
            resource += ","
        output.append(resource)
    return output
