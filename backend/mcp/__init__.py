"""MCP Server Registry -- central access point for all MCP tool servers."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

_servers = {}


def get_server(name: str, db=None):
    """Get an MCP server instance by name."""
    if name not in _servers:
        if name == "catalog":
            from mcp.catalog_server import CatalogServer
            _servers[name] = CatalogServer(db)
        elif name == "knowledge":
            from mcp.knowledge_server import KnowledgeServer
            _servers[name] = KnowledgeServer(db)
        elif name == "email":
            from mcp.email_server import EmailServer
            _servers[name] = EmailServer()
        else:
            raise ValueError(f"Unknown MCP server: {name}")
    if db is not None and hasattr(_servers[name], 'db'):
        _servers[name].db = db
    return _servers[name]


def get_all_tools(db=None) -> list[dict]:
    """Get all tool definitions from all MCP servers for Claude."""
    tools = []
    for name in ["catalog", "knowledge", "email"]:
        try:
            server = get_server(name, db)
            for tool in server.list_tools():
                tool["server"] = name
                tools.append(tool)
        except Exception as e:
            logger.warning(f"Failed to load MCP server '{name}': {e}")
    return tools


def call_tool(server_name: str, tool_name: str, args: dict, db=None):
    """Route a tool call to the correct MCP server."""
    server = get_server(server_name, db)
    return server.call_tool(tool_name, args)


def reset():
    """Clear cached server instances (for testing)."""
    _servers.clear()
