"""
GCA Tools Registry
Defines the native understanding of OpenClaw tools within the GCA brain.
This allows GCA to reason about tools semantically rather than just as strings.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json

@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any]
    intent_vector: str  # The associated skill vector (e.g., "RESEARCH", "SYSTEM")

    def to_schema(self) -> Dict[str, Any]:
        """Return the tool definition in OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }

    def format_prompt(self) -> str:
        """Format the tool definition for the system prompt."""
        params_str = json.dumps(self.parameters, indent=2)
        return f"Tool: {self.name}\nDescription: {self.description}\nParameters: {params_str}\n"


class ToolRegistry:
    """
    Registry for all tools known to GCA.
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._load_standard_tools()

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Tool]:
        return list(self._tools.values())

    def _load_standard_tools(self):
        """Load the standard OpenClaw tools."""

        # Web Search
        self.register(Tool(
            name="web_search",
            description="Search the web for real-time information. Use this when you need current events, facts, or data not in your internal knowledge.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query."},
                    "count": {"type": "integer", "description": "Number of results (1-10). Default 5."},
                    "country": {"type": "string", "description": "2-letter country code (e.g., 'US', 'DE')."}
                },
                "required": ["query"]
            },
            intent_vector="RESEARCH"
        ))

        # Web Fetch
        self.register(Tool(
            name="web_fetch",
            description="Fetch the content of a specific URL. Use this to read articles, documentation, or web pages.",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to fetch."}
                },
                "required": ["url"]
            },
            intent_vector="RESEARCH"
        ))

        # Gateway (System Control)
        self.register(Tool(
            name="gateway",
            description="Control the OpenClaw gateway (restart, config). Use this for system maintenance or configuration changes.",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["restart", "config.get", "config.schema", "config.apply", "config.patch", "update.run"]},
                    "reason": {"type": "string", "description": "Reason for the action (for restart)."},
                    "raw": {"type": "string", "description": "Raw config JSON (for config.apply/patch)."}
                },
                "required": ["action"]
            },
            intent_vector="SYSTEM"
        ))

        # Generic Send Message (for channels)
        # Note: In reality, OpenClaw might expose specific tools like 'whatsapp_send', 'discord_send', etc.
        # But GCA can map generic intents to these. For now, we define a generic one.
        self.register(Tool(
            name="send_message",
            description="Send a message to a user on a specific channel. Use this for proactive communication.",
            parameters={
                "type": "object",
                "properties": {
                    "channel": {"type": "string", "description": "The channel ID or name (e.g., 'whatsapp', 'discord')."},
                    "to": {"type": "string", "description": "The recipient ID."},
                    "content": {"type": "string", "description": "The message content."}
                },
                "required": ["content"]
            },
            intent_vector="COMMUNICATION"
        ))

        # Bash / Shell Execution
        self.register(Tool(
            name="bash",
            description="Execute a shell command. Use this for running standard Linux/Windows tools (curl, grep, ffmpeg) or coding agents.",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to run."},
                    "pty": {"type": "boolean", "description": "Run in a pseudo-terminal (interactive mode). Default false."},
                    "workdir": {"type": "string", "description": "Working directory for the command."},
                    "background": {"type": "boolean", "description": "Run in background and return a session ID."},
                    "timeout": {"type": "integer", "description": "Timeout in seconds."}
                },
                "required": ["command"]
            },
            intent_vector="SYSTEM"
        ))
