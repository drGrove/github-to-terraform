#!/usr/bin/env python3
import argparse
import os
from utils import bool_to_str, simplify
from utils import get_repositories

def main():
    repositories = get_repositories()

    for repository in repositories:
        name = repository.get('name')
        output = f"""
        resource "github_repository" "{simplify(name)}" {{
            name         = "{name}"
            description  = "{repository.get('description')}"
            homepage_url = "{repository.get('homepageUrl')}"
            private      = {bool_to_str(repository.get('isPrivate'))}
            visibility   = "{repository.get('visibility').lower()}"
            has_issues   = {bool_to_str(repository.get('hasIssuesEnabled'))}
            has_projects = {bool_to_str(repository.get('hasProjectsEnabled'))}
            has_wiki     = {bool_to_str(repository.get('hasWikiEnabled'))}

            allow_merge_commit = {bool_to_str(repository.get('mergeCommitAllowed'))}
            allow_squash_merge = {bool_to_str(repository.get('squashMergeAllowed'))}
            allow_rebase_merge = {bool_to_str(repository.get('rebaseMergeAllowed'))}

            delete_branch_on_merge = {bool_to_str(repository.get('deleteBranchOnMerge'))}
        }}
        """
        print(output)


def gen_import():
    repositories = get_repositories()
    for repository in repositories:
        name = repository.get('name')
        print(f"terraform import github_repository.{simplify(name)} {name}")
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate Repositories for login')
    parser.add_argument('--gen-imports', default=False, action='store_true')
    args = parser.parse_args()
    if args.gen_imports:
        gen_import()
    else:
        main()
