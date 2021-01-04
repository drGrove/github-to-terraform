#!/usr/bin/env python3
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

main()
