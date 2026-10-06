import pytest
from mcp.client import Client

from procurement_agent.mcp_server import build_mcp_server
from procurement_agent.store import DemoEnterpriseStore


@pytest.mark.asyncio
async def test_mcp_exposes_only_read_only_enterprise_tools():
    server = build_mcp_server(DemoEnterpriseStore())

    async with Client(server, raise_exceptions=True) as client:
        response = await client.list_tools()

    tools = {tool.name: tool for tool in response.tools}
    assert set(tools) == {
        "procurement_lookup_vendor",
        "procurement_lookup_budget",
    }

    for tool in tools.values():
        assert tool.annotations is not None
        assert tool.annotations.read_only_hint is True
        assert tool.annotations.destructive_hint is False
        assert tool.annotations.idempotent_hint is True
        assert tool.annotations.open_world_hint is False


@pytest.mark.asyncio
async def test_mcp_returns_structured_vendor_and_budget_context():
    server = build_mcp_server(DemoEnterpriseStore())

    async with Client(server, raise_exceptions=True) as client:
        vendor = await client.call_tool(
            "procurement_lookup_vendor",
            {"vendor_id": "vendor-cloud"},
        )
        budget = await client.call_tool(
            "procurement_lookup_budget",
            {"department": "IT"},
        )
        missing = await client.call_tool(
            "procurement_lookup_vendor",
            {"vendor_id": "vendor-missing"},
        )

    assert vendor.is_error is False
    assert vendor.structured_content["found"] is True
    assert vendor.structured_content["vendor"]["name"] == "CloudWorks Europe"

    assert budget.is_error is False
    assert budget.structured_content["found"] is True
    assert budget.structured_content["budget"]["remaining_eur"] == 50_000

    assert missing.is_error is False
    assert missing.structured_content == {"found": False, "vendor": None}
