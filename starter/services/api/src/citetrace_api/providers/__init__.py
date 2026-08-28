# citetrace_api.providers

from citetrace_api.providers.http import ProviderHttpClient
from citetrace_api.providers.models import (
    BibliographicQuery,
    ProviderCandidate,
    ProviderJsonResponse,
)
from citetrace_api.providers.protocols import ScholarlyMetadataProvider

__all__ = [
    "BibliographicQuery",
    "ProviderCandidate",
    "ProviderHttpClient",
    "ProviderJsonResponse",
    "ScholarlyMetadataProvider",
]
