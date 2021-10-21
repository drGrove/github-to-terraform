#!/usr/bin/env python3
import argparse
import os

from utils import simplify, get_collaborators_for_repository
from utils import get_repositories
from utils import ForbiddenAccessError


def main():
    repos = get_repositories()
    for repo in repos:
        repo_name = repo['name']
        if repo.get('isArchived'):
            # Skip  the repo if it's archived as GitHub API will fail
            continue
        collaborators = get_collaborators_for_repository(repo_name, affiliation="OUTSIDE")
        for collaborator in collaborators:
            username = collaborator['node']['login']
            permission = collaborator['permission']
            output = f"""
            resource "github_repository_collaborator" "{simplify(repo_name)}-{simplify(username)}" {{
                repository = github_repository.{simplify(repo_name)}.name
                username = "{username}"
                permission = "{permission.lower()}"
            }}
            """
            print(output)

def gen_import():
    repos = get_repositories()
    for repo in repos:
        repo_name = repo['name']
        if repo.get('isArchived'):
            # Skip  the repo if it's archived as GitHub API will fail
            continue
        collaborators = get_collaborators_for_repository(repo_name, affiliation="OUTSIDE")
        for collaborator in collaborators:
            username = collaborator['node']['login']
            print(f"terraform import github_repository_collaborator.{simplify(repo_name)}-{simplify(username)} {repo_name}:{username}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate Outside Collaborators for repos')
    parser.add_argument('--gen-imports', default=False, action='store_true')
    args = parser.parse_args()
    if args.gen_imports:
        gen_import()
    else:
        main()
