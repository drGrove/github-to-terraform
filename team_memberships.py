#!/usr/bin/env python3
import os

from utils import simplify
from utils import get_all_teams


login = os.environ.get('GITHUB_LOGIN')
teams_filter = f"first: 100"
query = f"""
{{
    organization(login: "{login}") {{
        name,
        teams({teams_filter}) {{
            pageInfo {{
                endCursor,
            }},
            totalCount,
            edges {{
                node {{
                    name,
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
    }},
}}
"""


teams = get_all_teams(query)

for team in teams:
    team_name = team.get('node').get('name')
    users = team.get('node').get('members').get('edges')
    users = sorted(users, key=lambda u: u['node']['login'])
    for user in users:
        username = user['node']['login']
        role = user['role']
        output = f"""
        resource "github_team_membership" "{simplify(team_name)}_{simplify(username)}" {{
            team_id  = github_team.{simplify(team_name)}.id
            username = github_membership.{simplify(username)}.id
            role     = "{role.lower()}"
        }}"""
        print(output)
