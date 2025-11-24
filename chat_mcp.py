#!/usr/bin/env python3
"""
Chat MCP Client - Interactive chat with EASA regulations via MCP server

This script allows you to chat with various LLMs (OpenAI, Ollama, Hyperbolic)
while connected to the EASA regulations MCP server for function calling.

Usage:
    python chat_mcp.py                    # Interactive provider selection
    python chat_mcp.py --provider openai  # Use OpenAI
    python chat_mcp.py --provider ollama  # Use Ollama (local)
    python chat_mcp.py --provider hyperbolic  # Use Hyperbolic
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional, Dict, List
from dataclasses import dataclass

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Using system environment variables.")

# OpenAI client (compatible with OpenAI, Ollama, Hyperbolic)
try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai package not found. Install with: pip install openai>=1.0.0")
    sys.exit(1)

# MCP imports
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.types import Tool
except ImportError:
    print("ERROR: mcp package not found. Install with: pip install mcp")
    sys.exit(1)


# ============================================================================
# Configuration Management
# ============================================================================

@dataclass
class ProviderConfig:
    """Configuration for an LLM provider"""
    name: str
    api_key: Optional[str]
    base_url: str
    model: str
    supports_streaming: bool = True
    supports_tools: bool = True
    supports_streaming_tools: bool = True  # Some providers don't stream tool calls properly


class ConfigManager:
    """Manages configuration for multiple LLM providers"""
    
    def __init__(self):
        self.providers: Dict[str, ProviderConfig] = {}
        self._load_providers()
    
    def _load_providers(self):
        """Load provider configurations from environment variables"""
        
        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        openai_base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")
        
        if openai_key:
            self.providers["openai"] = ProviderConfig(
                name="OpenAI",
                api_key=openai_key,
                base_url=openai_base,
                model=openai_model
            )
        
        # Ollama (local, no API key needed)
        ollama_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        
        self.providers["ollama"] = ProviderConfig(
            name="Ollama (Local)",
            api_key="ollama",  # Dummy key for local
            base_url=ollama_base,
            model=ollama_model
        )
        
        # Hyperbolic
        hyperbolic_key = os.getenv("HYPERBOLIC_API_KEY")
        hyperbolic_base = os.getenv("HYPERBOLIC_BASE_URL", "https://api.hyperbolic.xyz/v1")
        hyperbolic_model = os.getenv("HYPERBOLIC_MODEL", "meta-llama/Meta-Llama-3.1-70B-Instruct")
        
        if hyperbolic_key:
            self.providers["hyperbolic"] = ProviderConfig(
                name="Hyperbolic",
                api_key=hyperbolic_key,
                base_url=hyperbolic_base,
                model=hyperbolic_model,
                supports_streaming=False,  # Hyperbolic has streaming issues
                supports_streaming_tools=False  # Hyperbolic doesn't stream tool calls properly
            )
    
    def get_provider(self, provider_id: str) -> Optional[ProviderConfig]:
        """Get provider configuration by ID"""
        return self.providers.get(provider_id)
    
    def list_providers(self) -> List[str]:
        """List available provider IDs"""
        return list(self.providers.keys())
    
    def select_provider_interactive(self) -> Optional[str]:
        """Interactive provider selection"""
        providers = self.list_providers()
        
        if not providers:
            print("❌ No providers configured. Please check your .env file.")
            return None
        
        print("\n" + "=" * 80)
        print("🤖 Available LLM Providers")
        print("=" * 80)
        
        for i, provider_id in enumerate(providers, 1):
            config = self.providers[provider_id]
            print(f"{i}. {config.name} ({config.model})")
        
        print("=" * 80)
        
        while True:
            try:
                choice = input(f"\nSelect provider (1-{len(providers)}): ").strip()
                idx = int(choice) - 1
                
                if 0 <= idx < len(providers):
                    selected = providers[idx]
                    print(f"✅ Selected: {self.providers[selected].name}")
                    return selected
                else:
                    print(f"❌ Invalid choice. Please enter 1-{len(providers)}")
            except ValueError:
                print("❌ Please enter a number")
            except KeyboardInterrupt:
                print("\n👋 Cancelled")
                return None


# ============================================================================
# MCP Client
# ============================================================================

class MCPClient:
    """Client for interacting with MCP server"""
    
    def __init__(self, db_path: str = "easa_complete.db"):
        self.db_path = db_path
        self.session: Optional[ClientSession] = None
        self.tools: List[Tool] = []
        self.tools_dict: Dict[str, Tool] = {}
    
    async def connect(self):
        """Connect to the MCP server"""
        # Get absolute path to run_mcp_server.py
        root = Path(__file__).parent
        server_script = root / "run_mcp_server.py"
        
        if not server_script.exists():
            raise FileNotFoundError(f"MCP server script not found: {server_script}")
        
        # Check if database exists
        db_full_path = root / self.db_path
        if not db_full_path.exists():
            raise FileNotFoundError(f"Database not found: {db_full_path}")
        
        # Configure server parameters
        server_params = StdioServerParameters(
            command=sys.executable,  # Use current Python interpreter
            args=[str(server_script)],
            env={
                "EASA_DB_PATH": str(db_full_path),
                "EASA_MODEL": os.getenv("EASA_MODEL", "all-MiniLM-L6-v2"),
                "EASA_MAX_RESULTS": os.getenv("EASA_MAX_RESULTS", "20"),
                "EASA_CACHE": os.getenv("EASA_CACHE", "true")
            }
        )
        
        return server_params
    
    async def initialize(self, session: ClientSession):
        """Initialize the MCP session and load tools"""
        self.session = session
        await self.session.initialize()
        
        # Load available tools
        tools_response = await self.session.list_tools()
        self.tools = tools_response.tools
        self.tools_dict = {tool.name: tool for tool in self.tools}
        
        print(f"✅ Connected to MCP server: {len(self.tools)} tools available", file=sys.stderr)
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Call an MCP tool and return the result"""
        if not self.session:
            raise RuntimeError("MCP session not initialized")
        
        result = await self.session.call_tool(name, arguments)
        
        # Extract text content from result
        if result.content:
            return result.content[0].text
        return "{}"
    
    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """Convert MCP tools to OpenAI function format"""
        openai_tools = []
        
        for tool in self.tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            })
        
        return openai_tools


# ============================================================================
# LLM Client
# ============================================================================

class UnifiedLLMClient:
    """Unified client for OpenAI-compatible APIs"""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )
    
    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = True
    ) -> Any:
        """
        Send a chat completion request with optional tool support.
        
        Args:
            messages: List of chat messages
            tools: Optional list of tools in OpenAI format
            stream: Whether to stream the response
        
        Returns:
            Streaming or non-streaming response
        """
        # Disable streaming if provider doesn't support streaming tools and we have tools
        if tools and not self.config.supports_streaming_tools:
            stream = False
        
        kwargs = {
            "model": self.config.model,
            "messages": messages,
            "stream": stream
        }
        
        if tools and self.config.supports_tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        
        return self.client.chat.completions.create(**kwargs)


# ============================================================================
# Main Chat Application
# ============================================================================

class ChatMCPApp:
    """Main chat application with MCP integration"""
    
    def __init__(self, provider_id: str, config_manager: ConfigManager):
        self.provider_id = provider_id
        self.config_manager = config_manager
        self.provider_config = config_manager.get_provider(provider_id)
        
        if not self.provider_config:
            raise ValueError(f"Provider '{provider_id}' not configured")
        
        self.llm_client = UnifiedLLMClient(self.provider_config)
        self.mcp_client = MCPClient()
        self.running = False
    
    async def start(self):
        """Start the chat application"""
        print("\n" + "=" * 80)
        print("🚀 MCP Chat Client - EASA Regulations")
        print("=" * 80)
        print(f"📡 Provider: {self.provider_config.name}")
        print(f"🤖 Model: {self.provider_config.model}")
        print("=" * 80)
        
        # Connect to MCP server
        print("\n🔌 Connecting to MCP server...", file=sys.stderr)
        server_params = await self.mcp_client.connect()
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await self.mcp_client.initialize(session)
                
                # Show available commands
                self.print_help()
                
                # Start interactive loop
                self.running = True
                await self.interactive_loop()
    
    def print_help(self):
        """Print help message"""
        print("\n" + "-" * 80)
        print("📝 Commands:")
        print("  /quit, /exit - Exit the chat")
        print("  /provider    - Change LLM provider")
        print("  /tools       - List available MCP tools")
        print("  /help        - Show this help")
        print("-" * 80 + "\n")
    
    async def interactive_loop(self):
        """Main interactive loop"""
        while self.running:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.startswith("/"):
                    await self.handle_command(user_input)
                    continue
                
                # Process user query with LLM
                await self.process_query(user_input)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                self.running = False
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    async def handle_command(self, command: str):
        """Handle special commands"""
        cmd = command.lower()
        
        if cmd in ["/quit", "/exit"]:
            print("👋 Goodbye!")
            self.running = False
        
        elif cmd == "/provider":
            print("\n⚠️  Please restart the script to change provider")
        
        elif cmd == "/tools":
            print("\n📦 Available MCP Tools:")
            for tool in self.mcp_client.tools:
                print(f"  • {tool.name}: {tool.description}")
            print()
        
        elif cmd == "/help":
            self.print_help()
        
        else:
            print(f"❌ Unknown command: {command}")
            print("   Type /help for available commands")
    
    async def process_query(self, user_query: str):
        """Process a user query with the LLM and handle tool calls"""
        # Initial messages
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert assistant for EASA (European Union Aviation Safety Agency) regulations. "
                    "You have access to tools to search and retrieve EASA regulations. "
                    "Use these tools when needed to provide accurate, regulation-backed answers. "
                    "Always cite specific regulation references when available. "
                    "After using tools to gather information, provide a clear and complete answer to the user's question."
                )
            },
            {
                "role": "user",
                "content": user_query
            }
        ]
        
        # Get tools for LLM
        tools = self.mcp_client.get_tools_for_llm()
        
        # Maximum iterations to prevent infinite loops
        max_iterations = 10
        iteration = 0
        has_used_tools = False
        
        while iteration < max_iterations:
            iteration += 1
            
            # After tools are used once, we can optionally remove them to force a text response
            # This helps models that struggle with the tool->response transition
            current_tools = None if has_used_tools else tools
            
            # Determine if we should use streaming
            use_streaming = self.provider_config.supports_streaming
            
            # Some providers don't support streaming tool calls even if they support regular streaming
            if current_tools and not self.provider_config.supports_streaming_tools:
                use_streaming = False
            
            
            # Call LLM
            response = self.llm_client.chat_completion(
                messages=messages,
                tools=current_tools,
                stream=use_streaming
            )
            
            # Process response (streaming or non-streaming)
            assistant_message = {"role": "assistant", "content": "", "tool_calls": []}
            current_tool_call = None
            print("\nAssistant: ", end="", flush=True)
            
            if use_streaming:
                # Streaming mode
                for chunk in response:
                    if not chunk.choices:
                        continue
                    
                    choice = chunk.choices[0]
                    delta = choice.delta
                    
                    # Handle content
                    if delta.content:
                        print(delta.content, end="", flush=True)
                        assistant_message["content"] += delta.content
                    
                    # Handle tool calls
                    if delta.tool_calls:
                        for tc_chunk in delta.tool_calls:
                            if tc_chunk.index is not None:
                                # New tool call or continuation
                                while len(assistant_message["tool_calls"]) <= tc_chunk.index:
                                    assistant_message["tool_calls"].append({
                                        "id": "",
                                        "type": "function",
                                        "function": {"name": "", "arguments": ""}
                                    })
                                
                                current_tool_call = assistant_message["tool_calls"][tc_chunk.index]
                                
                                if tc_chunk.id:
                                    current_tool_call["id"] = tc_chunk.id
                                if tc_chunk.function:
                                    if tc_chunk.function.name:
                                        current_tool_call["function"]["name"] = tc_chunk.function.name
                                    if tc_chunk.function.arguments:
                                        current_tool_call["function"]["arguments"] += tc_chunk.function.arguments
            else:
                # Non-streaming mode
                if response.choices:
                    choice = response.choices[0]
                    message = choice.message
                    
                    # Handle content
                    if message.content:
                        print(message.content, end="", flush=True)
                        assistant_message["content"] = message.content
                    
                    # Handle tool calls
                    if message.tool_calls:
                        assistant_message["tool_calls"] = []
                        for tc in message.tool_calls:
                            assistant_message["tool_calls"].append({
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            })
            
            print()  # New line after response
            
            # Validate tool calls - check if we have complete, valid tool calls
            valid_tool_calls = []
            if assistant_message["tool_calls"]:
                for tc in assistant_message["tool_calls"]:
                    # A valid tool call must have id, name, and valid JSON arguments
                    if tc["id"] and tc["function"]["name"] and tc["function"]["arguments"]:
                        try:
                            # Verify arguments are valid JSON
                            json.loads(tc["function"]["arguments"])
                            valid_tool_calls.append(tc)
                        except json.JSONDecodeError:
                            # Skip invalid JSON silently
                            pass
            
            # Check if we have valid tool calls to execute
            if valid_tool_calls:
                # Update the message with only valid tool calls
                assistant_message["tool_calls"] = valid_tool_calls
                
                # For providers that don't support proper tool protocol, use a workaround
                if not self.provider_config.supports_streaming_tools:
                    # Don't add assistant message with tool_calls, use regular text instead
                    messages.append({
                        "role": "assistant",
                        "content": "Let me search for that information..."
                    })
                else:
                    # Add assistant message to history (with tool calls, content should be empty)
                    # Different providers handle this differently:
                    # - OpenAI: accepts None or no field
                    # - Hyperbolic: seems to require empty string or the field present
                    if assistant_message["tool_calls"]:
                        if not assistant_message["content"]:
                            assistant_message["content"] = ""  # Use empty string instead of None
                    
                    messages.append(assistant_message)
                
                has_used_tools = True
                
                # Execute tool calls
                print("\n🔧 Executing tool calls...", file=sys.stderr)
                
                for tool_call in valid_tool_calls:
                    tool_name = tool_call["function"]["name"]
                    tool_args = json.loads(tool_call["function"]["arguments"])
                    
                    print(f"   • {tool_name}({json.dumps(tool_args, indent=2)})", file=sys.stderr)
                    
                    # Call MCP tool
                    try:
                        result = await self.mcp_client.call_tool(tool_name, tool_args)
                        
                        # Add tool result to messages
                        # Some providers (like Hyperbolic) don't properly support role="tool"
                        # so we use role="user" as a workaround for those providers
                        if self.provider_config.supports_streaming_tools:
                            # Provider properly supports tool protocol
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call["id"],
                                "content": result
                            })
                        else:
                            # Workaround: convert tool result to user message
                            messages.append({
                                "role": "user",
                                "content": f"Tool '{tool_name}' result:\n{result}"
                            })
                        
                        print(f"   ✅ {tool_name} completed", file=sys.stderr)
                    
                    except Exception as e:
                        print(f"   ❌ {tool_name} failed: {e}", file=sys.stderr)
                        error_content = json.dumps({"error": str(e)})
                        
                        if self.provider_config.supports_streaming_tools:
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call["id"],
                                "content": error_content
                            })
                        else:
                            messages.append({
                                "role": "user",
                                "content": f"Tool '{tool_name}' error:\n{error_content}"
                            })
                
                print(file=sys.stderr)
                # Continue loop to get final response
                continue
            
            elif assistant_message["content"]:
                # We have content but no tool calls - we're done
                break
            
            else:
                # No content and no valid tool calls - something went wrong
                print("\n⚠️  Model produced no output.", file=sys.stderr)
                break
        
        if iteration >= max_iterations:
            print("\n⚠️  Maximum iterations reached.", file=sys.stderr)


# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Chat with EASA regulations via MCP server"
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["openai", "ollama", "hyperbolic"],
        help="LLM provider to use"
    )
    parser.add_argument(
        "--db",
        type=str,
        default="easa_complete.db",
        help="Path to EASA database"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config_manager = ConfigManager()
    
    # Select provider
    provider_id = args.provider
    if not provider_id:
        provider_id = config_manager.select_provider_interactive()
    
    if not provider_id:
        print("❌ No provider selected")
        sys.exit(1)
    
    # Verify provider is configured
    if provider_id not in config_manager.list_providers():
        print(f"❌ Provider '{provider_id}' not configured. Check your .env file.")
        sys.exit(1)
    
    # Create and start chat app
    try:
        app = ChatMCPApp(provider_id, config_manager)
        await app.start()
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

