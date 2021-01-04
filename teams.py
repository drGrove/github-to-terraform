#!/usr/bin/env python3
import os

from utils import get_all_teams
from utils import simplify


login = os.environ.get('GITHUB_LOGIN')
teams_filter = "first: 100"
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
                    description,
                    privacy,
                    parentTeam {{
                        id,
                        name,
                    }},
                }},
            }},
        }},
    }},
}}
"""

teams = get_all_teams(query)

for team in teams:
    normalized_team_name = simplify(team.get('node').get('name'))
    privacy = "closed" if team.get('privacy') == "VISIBLE" else "secret"
    parent_policy = ""
    if team.get('parentTeam'):
        parent_team = team.get('parentTeam')
        parent_normalized_name = simplify(parent_team.get('name'))
        parent_policy = f"""
        parent_team_id  = github_team.{ parent_normalized_name }.id"""
    output = f"""resource "github_team" "{normalized_team_name}" {{
        name            = "{ team.get('name') }"
        description     = "{ team.get('description') }"
        privacy         = "{ privacy }" """ + parent_policy + f"""
    }}
    """
    print(output)
