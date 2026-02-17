"""Tests for MCP Email Server — customer communication tools."""
import pytest
from unittest.mock import patch, MagicMock
from mcp.email_server import EmailServer


@pytest.fixture
def server():
    return EmailServer()


def test_list_tools_returns_all_tools(server):
    tools = server.list_tools()
    names = [t["name"] for t in tools]
    assert "draft_reply" in names
    assert "send_email" in names
    assert "get_thread" in names
    assert len(names) == 3


def test_draft_reply_returns_plan(server):
    result = server.call_tool("draft_reply", {
        "to": "priya@gmail.com",
        "subject": "Re: Order #3",
        "body": "Hi Priya, your order is confirmed!",
    })
    assert result["action"] == "send_email"
    assert result["requires_approval"] is True
    assert result["args"]["to"] == "priya@gmail.com"


def test_send_email_returns_plan(server):
    result = server.call_tool("send_email", {
        "to": "priya@gmail.com",
        "subject": "Order Confirmation",
        "body": "Thank you for your order!",
    })
    assert result["action"] == "send_email"
    assert result["requires_approval"] is True


def test_get_thread_reads_audit(server):
    with patch("mcp.email_server.audit") as mock_audit:
        mock_audit.read_audit_entries.return_value = [
            {"entity_id": "INQUIRY_2026-02-17.md", "action": "task.completed", "details": {"email": "priya@gmail.com"}, "timestamp": "2026-02-17"},
        ]
        result = server.call_tool("get_thread", {"customer_email": "priya@gmail.com"})
        assert isinstance(result, list)


def test_call_tool_unknown_raises(server):
    with pytest.raises(ValueError, match="Unknown tool"):
        server.call_tool("nonexistent", {})
