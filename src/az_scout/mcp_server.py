"""MCP server for Azure Availability Zone Mapping.

Exposes the same Azure ARM capabilities as the web UI – tenants,
subscriptions, regions, zone mappings and SKU availability – as
MCP tools so that AI agents can query them directly.

Run with:
    az-scout mcp            # stdio transport (default)
    az-scout mcp --http     # Streamable HTTP transport on port 8080

Or add to your MCP client config (e.g. Claude Desktop):
    {
      "mcpServers": {
        "az-scout": {
          "command": "az-scout",
          "args": ["mcp"]
        }
      }
    }
"""

import json
import logging
import os
from typing import Annotated

from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import Field

from az_scout import __version__, azure_api

logger = logging.getLogger(__name__)


def _build_transport_security() -> TransportSecuritySettings:
    """Build the DNS-rebinding policy for the HTTP transports.

    When deployed behind a reverse proxy (e.g. Azure Container Apps), DNS
    rebinding protection must either be disabled or the external hostname(s)
    added to the allow-list.  Set ``FASTMCP_ALLOWED_HOSTS`` to a comma-separated
    list of allowed ``Host`` header values (e.g. ``myapp.azurecontainerapps.io``).
    If empty/unset, rebinding protection is disabled for remote deployments.

    Note: the SDK auto-enables rebinding protection when no settings are passed
    and the bind host is loopback, so this must always be supplied explicitly to
    the transport to preserve the opt-in behaviour above.
    """
    allowed_hosts_env = os.environ.get("FASTMCP_ALLOWED_HOSTS", "")
    if allowed_hosts_env:
        # Drop empty entries so a stray/trailing comma can't inject "" into the
        # allow-list.  A malformed value still fails closed: protection stays on
        # with an empty list, which rejects every host.
        allowed_hosts = [h.strip() for h in allowed_hosts_env.split(",") if h.strip()]
        return TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=allowed_hosts,
        )
    return TransportSecuritySettings(enable_dns_rebinding_protection=False)


#: Transport-level security policy, passed explicitly to every HTTP transport.
TRANSPORT_SECURITY = _build_transport_security()

mcp = MCPServer(
    "az-scout",
    version=__version__,
    instructions=(
        "Azure Availability Zone mapping tools. "
        "Use these tools to discover Azure tenants, subscriptions and regions, "
        "then query logical-to-physical zone mappings and VM SKU availability. "
        "All tools require valid Azure credentials via DefaultAzureCredential "
        "(e.g. `az login`)."
    ),
)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def list_tenants() -> str:
    """List Azure AD tenants accessible by the current credential.

    Returns all tenants with their authentication status and the default
    tenant ID for the current auth context.  Use this first to discover
    available tenants before querying subscriptions.
    """
    result = azure_api.list_tenants()
    return json.dumps(result, indent=2)


@mcp.tool()
def list_subscriptions(
    tenant_id: Annotated[
        str | None, Field(description="Optional tenant ID to scope the query.")
    ] = None,
) -> str:
    """List enabled Azure subscriptions.

    Returns a JSON array of ``{"id": ..., "name": ...}`` objects sorted
    alphabetically.
    """
    result = azure_api.list_subscriptions(tenant_id)
    return json.dumps(result, indent=2)


@mcp.tool()
def list_regions(
    subscription_id: Annotated[
        str | None, Field(description="Subscription ID. Auto-discovered if omitted.")
    ] = None,
    tenant_id: Annotated[str | None, Field(description="Optional tenant ID.")] = None,
) -> str:
    """List Azure regions that support Availability Zones.

    Returns a JSON array of ``{"name": ..., "displayName": ...}`` for each
    AZ-enabled region.
    """
    result = azure_api.list_regions(subscription_id, tenant_id)
    return json.dumps(result, indent=2)
