"""MCP Email Server — customer communication tools."""

import logging
from services import audit

logger = logging.getLogger(__name__)


class EmailServer:
    """MCP server for email operations."""

    def list_tools(self) -> list[dict]:
        return [
            {
                "name": "draft_reply",
                "description": "Draft a customer email reply (requires approval before sending)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "to": {"type": "string", "description": "Recipient email"},
                        "subject": {"type": "string"},
                        "body": {"type": "string"},
                        "template": {"type": "string"},
                    },
                    "required": ["to", "subject", "body"],
                },
            },
            {
                "name": "send_email",
                "description": "Send an email to a customer (requires approval)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "to": {"type": "string"},
                        "subject": {"type": "string"},
                        "body": {"type": "string"},
                    },
                    "required": ["to", "subject", "body"],
                },
            },
            {
                "name": "get_thread",
                "description": "Get previous interaction history for a customer",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "customer_email": {"type": "string"},
                    },
                    "required": ["customer_email"],
                },
            },
        ]

    def call_tool(self, tool_name: str, args: dict):
        handler = getattr(self, f"_tool_{tool_name}", None)
        if handler is None:
            raise ValueError(f"Unknown tool: {tool_name}")
        return handler(args)

    def _tool_draft_reply(self, args: dict) -> dict:
        return {
            "action": "send_email",
            "server": "email",
            "args": {
                "to": args["to"],
                "subject": args["subject"],
                "body": args["body"],
            },
            "requires_approval": True,
            "description": f"Send email to {args['to']}: {args['subject']}",
        }

    def _tool_send_email(self, args: dict) -> dict:
        return {
            "action": "send_email",
            "server": "email",
            "args": args,
            "requires_approval": True,
            "description": f"Send email to {args['to']}: {args['subject']}",
        }

    def _tool_get_thread(self, args: dict) -> list[dict]:
        entries = audit.read_audit_entries()
        email = args["customer_email"].lower()
        relevant = [
            e for e in entries
            if email in str(e.get("details", "")).lower()
            or email in str(e.get("entity_id", "")).lower()
        ]
        return relevant[-10:]

    def execute_action(self, action: dict) -> dict:
        """Execute approved email send. Logs to audit (no real SMTP yet)."""
        args = action["args"]
        logger.info(f"[EMAIL] Sending to {args['to']}: {args['subject']}")
        audit.write_audit_entry(
            source="mcp/email",
            action="email.sent",
            entity_type="email",
            entity_id=args["to"],
            actor="task-executor",
            details={"subject": args["subject"], "to": args["to"]},
            status="SENT",
        )
        return {
            "status": "sent",
            "to": args["to"],
            "subject": args["subject"],
            "note": "Logged to audit trail (SMTP not configured)",
        }
