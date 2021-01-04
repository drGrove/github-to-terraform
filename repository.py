#!/usr/bin/env python3
import os

from utils import get_private_repositories
from utils import simplify


login = os.environ.get('GITHUB_LOGIN')
repo_filters = "isFork: false, first: 100"
query = f"""
{{
    organization(login: "{login}") {{
        name,
        repositories({repo_filters}) {{
            pageInfo {{
                endCursor
            }},
            totalCount,
            edges {{
                node {{
                    id,
                    name,
                    description,
                    homepageUrl,
                    isPrivate,
                    hasIssuesEnabled,
                    hasWikiEnabled,
                    hasProjectsEnabled,
                    mergeCommitAllowed,
                    squashMergeAllowed,
                    rebaseMergeAllowed,
                    deleteBranchOnMerge,
                    isArchived,
                }},
            }},
        }},
    }},
}}
"""

def main():
    repos = get_private_repositories(query)
    print(repos)

    for repo in repos:
        repo = repo.get('node')
        output = f"""
        resource "github_repository" "{simplify(repo.get('name'))}" {{
            name        = "{ repo.get('name') }"
            description = "{ repo.get('description') }"
        }}"""
        print(output)


main()
