#!/usr/bin/env python3
import argparse

from utils import get_all_teams
from utils import simplify


def main():
    teams = get_all_teams()

    for team in teams:
        normalized_team_name = simplify(team.get('node').get('name'))
        privacy = "closed" if team.get('node').get('privacy') == "VISIBLE" else "secret"
        parent_policy = ""
        if team.get('node').get('parentTeam'):
            parent_team = team.get('node').get('parentTeam')
            parent_normalized_name = simplify(parent_team.get('name'))
            parent_policy = f"""
            parent_team_id  = github_team.{ parent_normalized_name }.id"""
        output = f"""resource "github_team" "{normalized_team_name}" {{
            name            = "{ team.get('node').get('name') }"
            description     = "{ team.get('node').get('description') }"
            privacy         = "{ privacy }" """ + parent_policy + f"""
        }}
        """
        print(output)


def gen_import():
    teams = get_all_teams()
    for team in teams:
        print(f"terraform import github_team.{simplify(team.get('node').get('name'))} {team.get('node').get('databaseId')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate teams')
    parser.add_argument('--gen-imports', default=False, action='store_true')
    args = parser.parse_args()
    if args.gen_imports:
        gen_import()
    else:
        main()
