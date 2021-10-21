#!/usr/bin/env python3
import argparse
import os
from utils import bool_to_str, simplify, tf_context_for_contexts, tf_resource_for_actor
from utils import get_branch_protection_rules
from utils import get_repositories
from utils import tf_resources_for_actors

LOGIN = os.environ.get('GITHUB_LOGIN')


def main():
    repositories = get_repositories()

    for repository in repositories:
        name = repository.get('name')
        rules = get_branch_protection_rules(LOGIN, name)
        newline = "\n"
        for rule in rules:
            review_dismissal_actors = [ actor for actor in
                    rule.get('ReviewDismissalAllowances').get('nodes')] if rule.get('ReviewDismissalAllowances') else []
            push_allowances = [ actor.get('actor') for actor in
                    rule.get('pushAllowances').get('nodes') ] if rule.get('pushAllowances') else []
            output = f"""
            resource "github_branch_protection" "{simplify(name)}-{simplify(rule.get('pattern'))}" {{
                repository = github_repository.{simplify(name)}.name
                pattern    = "{ rule.get('pattern') }"

                enforce_admins  = {bool_to_str(rule.get('isAdminEnforced'))}
                allow_deletions = {bool_to_str(rule.get('allowsDeletions'))}
                require_signed_commits = {bool_to_str(rule.get('requiresCommitSignatures'))}
                required_linear_history = {bool_to_str(rule.get('requiresLinearHistory'))}
                alllows_force_pushes = {bool_to_str(rule.get('allowsForcePushes'))}

                required_status_checks {{
                    strict = {bool_to_str(rule.get('requiresStatusChecks'))}
                    contexts = [
                        {newline.join(f'{context}' for context in tf_context_for_contexts(rule.get('requiredStatusCheckContexts')))}
                    ]
                }}

                required_pull_request_reviews {{
                    dismiss_stale_reviews = {bool_to_str(rule.get('dismissesStaleReviews'))}
                    restrict_dismissals = {bool_to_str(rule.get('restrictsReviewDismissals'))}
                    require_code_owner_reviews = {bool_to_str(rule.get('requiresCodeOwnerReviews'))}
                    required_approving_review_count = {rule.get('requiredApprovingReviewCount')}
                    dismissal_restrictions = [
                        {newline.join(resource for resource in tf_resources_for_actors(review_dismissal_actors))}
                    ]
                }}
                push_restrictions = [
                    {newline.join(resource for resource in tf_resources_for_actors(push_allowances))}
                ]
            }}
            """
            print(output)


def gen_import():
    repositories = get_repositories()
    for repository in repositories:
        name = repository.get('name')
        rules = get_branch_protection_rules(LOGIN, name)
        for rule in rules:
            pattern = rule['pattern']
            print(f"terraform import github_branch_protection.{simplify(name)}-{simplify(rule.get('pattern'))} {name}:{pattern}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate Repositories for login')
    parser.add_argument('--gen-imports', default=False, action='store_true')
    args = parser.parse_args()
    if args.gen_imports:
        gen_import()
    else:
        main()
