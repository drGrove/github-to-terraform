#!/usr/bin/env python3
import argparse
import os

from utils import get_team_repositories, simplify
from utils import get_all_teams


def main():
    teams = get_all_teams()
    for team in teams:
        repositories = get_team_repositories(team.get('name'))
        team_name = team['name']
        for repository in repositories:
            repo_name = repository['node']['name']
            permission = repository['permission']
            output = f"""
            resource "github_team_repository" "{simplify(team_name)}-{simplify(repo_name)}" {{
                team_id = github_team.{simplify(team_name)}.id
                repository = github_repository.{simplify(repo_name)}.name
                permission = "{permission.lower()}"
            }}
            """
            print(output)


def gen_import():
    teams = get_all_teams()
    for team in teams:
        team_name = team['name']
        repositories = get_team_repositories(team_name)
        for repository in repositories:
            repo_name = repository['node']['name']
            print(f"terraform import github_team_repository.{simplify(repo_name)} {team['databaseId']}:{repo_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate membership for teams')
    parser.add_argument('--gen-imports', default=False, action='store_true')
    args = parser.parse_args()
    if args.gen_imports:
        gen_import()
    else:
        main()
