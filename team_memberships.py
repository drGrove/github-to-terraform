#!/usr/bin/env python3
import argparse
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
                    databaseId,
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

def main():
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
                username = github_membership.{simplify(username)}.username
                role     = "{role.lower()}"
            }}"""
            print(output)


def gen_import():
    teams = get_all_teams(query)
    for team in teams:
        users = team.get('node').get('members').get('edges')
        users = sorted(users, key=lambda u: u['node']['login'])
        for user in users:
            username = user['node']['login']
            team_id = team.get('node').get('databaseId')
            print(f"terraform import github_team_membership.{simplify(username)} {team_id}:{simplify(username)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate membership for teams')
    parser.add_argument('--gen-imports', default=False, action='store_true')
    args = parser.parse_args()
    if args.gen_imports:
        gen_import()
    else:
        main()
