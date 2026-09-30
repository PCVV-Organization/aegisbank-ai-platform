"""Deterministic Azure Workload Identity and TokenCredential resolution for AegisBank.

Separates developer cloud testing (DefaultAzureCredential) from staging and production
environments, where deterministic Managed Identity (ManagedIdentityCredential) is preferred
to eliminate secret leakage and unintended credential fallback chains.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from .environment import RuntimeEnvironment, resolve_runtime_environment

logger = logging.getLogger("aegisbank.configuration.identity")


def resolve_azure_credential(
    environment: RuntimeEnvironment | None = None,
    client_id: str | None = None,
) -> Any:
    """Return the canonical TokenCredential appropriate to the runtime environment.

    - Production / Staging: Uses deterministic Managed Identity (ManagedIdentityCredential).
    - Development / Local Cloud: Uses DefaultAzureCredential for local developer convenience.
    - Local Offline: Azure packages are imported lazily, never executing at import time.
    """
    effective_env = environment or resolve_runtime_environment()
    effective_client_id = client_id or os.getenv("AZURE_CLIENT_ID")

    if effective_env is RuntimeEnvironment.PRODUCTION:
        from azure.identity import ManagedIdentityCredential

        if effective_client_id:
            return ManagedIdentityCredential(client_id=effective_client_id)
        return ManagedIdentityCredential()

    if effective_env is RuntimeEnvironment.STAGING:
        from azure.identity import DefaultAzureCredential, ManagedIdentityCredential

        if effective_client_id:
            try:
                return ManagedIdentityCredential(client_id=effective_client_id)
            except Exception:
                return DefaultAzureCredential()
        try:
            return ManagedIdentityCredential()
        except Exception:
            return DefaultAzureCredential()

    from azure.identity import DefaultAzureCredential

    return DefaultAzureCredential()
