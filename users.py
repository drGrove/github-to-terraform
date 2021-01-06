#!/usr/bin/env python3
import argparse
import os

from utils import get_all_users
from utils import simplify

login = os.environ.get('GITHUB_LOGIN')
members_filter = "first: 100"
query = f"""
{{
  organization(login: "{login}") {{
    name,
    membersWithRole({members_filter}) {{
      pageInfo {{
        endCursor,
      }},
      totalCount,
      edges {{
        role,
        node {{
          id,
          login,
        }},
      }},
    }},
  }},
}}
"""

def main():
    users = get_all_users(query)
    for user in users:
        username = user.get('node').get('login')
        role = user.get('role').lower()
        output = f"""
        resource "github_membership" "{simplify(username)}" {{
            username = "{username}"
            role     = "{role}"
        }}"""
        print(output)


def gen_import():
    users = get_all_users(query)
    for user in users:
        username = user.get('node').get('login')
        print(f"terraform import github_membership.{simplify(username)} {login}:{username}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate teams')
    parser.add_argument('--gen-imports', default=False, action='store_true')
    args = parser.parse_args()
    if args.gen_imports:
        gen_import()
    else:
        main()
