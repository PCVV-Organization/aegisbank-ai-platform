"""Administrative provisioning for synthetic staging customer identities."""

from __future__ import annotations

import argparse
import getpass

from .customer_auth import CosmosAuthStore, CustomerAuth


def main() -> int:
    parser = argparse.ArgumentParser(description="Provision a synthetic AegisBank customer")
    parser.add_argument("create-user", nargs="?", help="Provision a user")
    parser.add_argument("--dni", required=True)
    parser.add_argument("--customer-id", required=True)
    parser.add_argument("--rotate", action="store_true")
    args = parser.parse_args()
    password = getpass.getpass("Synthetic password (not echoed): ")
    CustomerAuth(CosmosAuthStore()).enroll(args.dni, password, args.customer_id, rotate=args.rotate)
    print("Synthetic customer provisioned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
