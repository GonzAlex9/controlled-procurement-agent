from __future__ import annotations

import os

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from pydantic import BaseModel

from procurement_agent.models import Budget, Vendor
from procurement_agent.store import DemoEnterpriseStore


class VendorLookupResult(BaseModel):
    found: bool
    vendor: Vendor | None


class BudgetLookupResult(BaseModel):
    found: bool
    budget: Budget | None


READ_ONLY_INTERNAL = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)


def build_mcp_server(store: DemoEnterpriseStore | None = None) -> MCPServer:
    enterprise_store = store or DemoEnterpriseStore()
    server = MCPServer(
        "controlled_procurement_context",
        version="0.1.0",
        instructions=(
            "Read-only enterprise procurement context. "
            "These tools can inspect fictional vendor and budget data, but they cannot "
            "approve spend, mutate vendor state, reserve budget, or execute purchases."
        ),
    )

    @server.tool(annotations=READ_ONLY_INTERNAL)
    def procurement_lookup_vendor(vendor_id: str) -> VendorLookupResult:
        """Read a vendor-master record by vendor ID without changing enterprise state."""
        vendor = enterprise_store.get_vendor(vendor_id)
        return VendorLookupResult(found=vendor is not None, vendor=vendor)

    @server.tool(annotations=READ_ONLY_INTERNAL)
    def procurement_lookup_budget(department: str) -> BudgetLookupResult:
        """Read remaining demo budget for a department without reserving or spending funds."""
        budget = enterprise_store.get_budget(department)
        return BudgetLookupResult(found=budget is not None, budget=budget)

    return server


mcp = build_mcp_server()


def main() -> None:
    transport = os.getenv("MCP_TRANSPORT", "stdio")

    if transport == "stdio":
        mcp.run()
        return

    if transport == "streamable-http":
        host = os.getenv("MCP_HOST", "127.0.0.1")
        port = int(os.getenv("MCP_PORT", "8001"))
        mcp.run(
            transport="streamable-http",
            host=host,
            port=port,
            stateless_http=True,
            json_response=True,
        )
        return

    raise ValueError("MCP_TRANSPORT must be 'stdio' or 'streamable-http'")


if __name__ == "__main__":
    main()
