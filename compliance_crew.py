#!/usr/bin/env python3
"""
CrewAI Compliance Validator - EASA Regulations Compliance Auditing

This script uses a CrewAI team (Auditor + QA Challenger) to validate the compliance
of a text against EASA regulations via the MCP server.

Usage:
    python compliance_crew.py --text "Text to validate" --output report.md
    python compliance_crew.py --file manual.txt --output report.md --provider openai
    python compliance_crew.py --interactive
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime
import argparse

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Using system environment variables.")

# MCP imports
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.types import Tool
except ImportError:
    print("ERROR: mcp package not found. Install with: pip install mcp")
    sys.exit(1)

# CrewAI imports
try:
    from crewai import Agent, Task, Crew, Process
    from crewai.tools import tool
except ImportError as e:
    print(f"ERROR: crewai package not found. Install with: pip install crewai crewai-tools")
    print(f"   Import error details: {e}")
    sys.exit(1)

# Import custom LLM classes
try:
    from easacompliance.llm import HyperbolicLLM, OllamaLLM
except ImportError:
    print("Warning: easacompliance.llm not found. Custom providers may not work correctly.")
    HyperbolicLLM = None
    OllamaLLM = None


# ============================================================================
# Configuration Management (reused from chat_mcp.py)
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
            api_key="ollama",
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
                model=hyperbolic_model
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
# MCP Client (reused from chat_mcp.py)
# ============================================================================

class MCPClient:
    """Client for interacting with MCP server"""
    
    def __init__(self, db_path: str = "easa_complete.db"):
        self.db_path = db_path
        self.session: Optional[ClientSession] = None
        self.tools: List[Tool] = []
        self.tools_dict: Dict[str, Tool] = {}
        self._read = None
        self._write = None
        self._server_process = None
    
    async def connect(self):
        """Connect to the MCP server"""
        root = Path(__file__).parent
        server_script = root / "run_mcp_server.py"
        
        if not server_script.exists():
            raise FileNotFoundError(f"MCP server script not found: {server_script}")
        
        db_full_path = root / self.db_path
        if not db_full_path.exists():
            raise FileNotFoundError(f"Database not found: {db_full_path}")
        
        server_params = StdioServerParameters(
            command=sys.executable,
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
        
        tools_response = await self.session.list_tools()
        self.tools = tools_response.tools
        self.tools_dict = {tool.name: tool for tool in self.tools}
        
        print(f"✅ Connected to MCP server: {len(self.tools)} tools available", file=sys.stderr)
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Call an MCP tool and return the result"""
        if not self.session:
            raise RuntimeError("MCP session not initialized")
        
        result = await self.session.call_tool(name, arguments)
        
        if result.content:
            return result.content[0].text
        return "{}"


# ============================================================================
# MCP Tools Wrappers for CrewAI
# ============================================================================

# Global MCP client instance (will be set during initialization)
_mcp_client: Optional[MCPClient] = None
_event_loop: Optional[asyncio.AbstractEventLoop] = None


def _sync_call_mcp_tool(tool_name: str, **kwargs) -> str:
    """Synchronous wrapper to call MCP tools from CrewAI"""
    global _mcp_client, _event_loop
    
    if not _mcp_client or not _event_loop:
        return json.dumps({"error": "MCP client not initialized"})
    
    try:
        # Run async call in the event loop running in main thread
        future = asyncio.run_coroutine_threadsafe(
            _mcp_client.call_tool(tool_name, kwargs),
            _event_loop
        )
        result = future.result(timeout=120)  # Increased timeout for complex queries
        return result
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"⚠️  MCP tool '{tool_name}' failed: {error_msg}", file=sys.stderr)
        return json.dumps({"error": error_msg})


@tool("search_easa_regulations")
def search_easa_regulations(query: str, top_k: int = 5, min_score: float = 0.0) -> str:
    """
    Search EASA regulations using semantic similarity.
    
    Args:
        query: Search query in natural language (e.g., 'flight time limitations for crew')
        top_k: Number of results to return (default: 5, max: 20)
        min_score: Minimum similarity score (0-1, default: 0)
    
    Returns:
        JSON string with search results including regulations, scores, and content
    """
    return _sync_call_mcp_tool("search_regulations", query=query, top_k=top_k, min_score=min_score)


@tool("get_easa_regulation")
def get_easa_regulation(reference: str) -> str:
    """
    Retrieve a specific EASA regulation by its exact reference.
    
    Args:
        reference: Exact regulation reference (e.g., 'ORO.FTL.110', 'AMC1 ORO.FTL.110')
    
    Returns:
        JSON string with full regulation details (reference, title, type, content, metadata)
    """
    return _sync_call_mcp_tool("get_regulation", reference=reference)


@tool("get_regulatory_chain")
def get_regulatory_chain(reference: str) -> str:
    """
    Get a complete regulatory chain for an IR (Implementing Rule).
    Returns the IR and all associated AMC and GM.
    
    Args:
        reference: IR reference (e.g., 'ORO.FTL.110')
    
    Returns:
        JSON string with the IR and all associated AMC and GM regulations
    """
    return _sync_call_mcp_tool("get_regulatory_chain", reference=reference)


@tool("list_easa_categories")
def list_easa_categories(limit: int = 20) -> str:
    """
    List all available EASA regulation categories.
    Returns categories sorted by number of regulations.
    
    Args:
        limit: Maximum number of categories to return (default: 20, max: 100)
    
    Returns:
        JSON string with categories and their regulation counts
    """
    return _sync_call_mcp_tool("list_categories", limit=limit)


@tool("validate_text_compliance")
def validate_text_compliance(text: str, top_k: int = 10, min_score: float = 0.3) -> str:
    """
    Validate compliance of a text against EASA regulations.
    Returns compliance score, relevant regulations, identified gaps, and recommendations.
    
    Args:
        text: Text to validate (manual section, procedure, policy, etc.)
        top_k: Number of relevant regulations to analyze (default: 10, max: 50)
        min_score: Minimum relevance score (0-1, default: 0.3)
    
    Returns:
        JSON string with compliance analysis, relevant regulations, gaps, and recommendations
    """
    return _sync_call_mcp_tool("validate_compliance", text=text, top_k=top_k, min_score=min_score)


@tool("get_statistics")
def get_easa_statistics() -> str:
    """
    Get comprehensive statistics about the EASA regulatory database.
    Returns total number of regulations, breakdown by type and category.
    
    Returns:
        JSON string with database statistics
    """
    return _sync_call_mcp_tool("get_statistics")


# ============================================================================
# CrewAI Agents Configuration
# ============================================================================

def create_compliance_auditor(llm_config: Dict[str, Any]) -> Agent:
    """Create the Compliance Auditor agent"""
    return Agent(
        role="EASA Compliance Auditor",
        goal="Thoroughly analyze the provided text and identify all potential compliance issues with EASA regulations",
        backstory="""You are a senior aviation compliance auditor with over 15 years of experience 
        in EASA regulations. You have audited hundreds of aviation operations and are known for your 
        meticulous attention to detail. You systematically analyze every aspect of operational texts 
        against the full scope of EASA regulations, leaving no stone unturned. You always cite specific 
        regulation references and provide clear explanations of any non-compliance.""",
        tools=[
            search_easa_regulations,
            get_easa_regulation,
            get_regulatory_chain,
            list_easa_categories,
            validate_text_compliance,
            get_easa_statistics
        ],
        verbose=True,
        allow_delegation=False,
        llm=llm_config["model"]
    )


def create_qa_challenger(llm_config: Dict[str, Any]) -> Agent:
    """Create the Quality Assurance Challenger agent"""
    return Agent(
        role="Quality Assurance Challenger",
        goal="Review and challenge the auditor's findings to ensure accuracy, completeness, and proper regulatory interpretation",
        backstory="""You are a critical quality assurance expert specializing in aviation compliance 
        audits. Your role is to be the devil's advocate - you question every finding, verify every 
        regulation reference, and identify any gaps in the audit. You have caught numerous errors in 
        past audits where regulations were misinterpreted or compliance issues were missed. You are 
        respected for your rigor and your ability to improve audit quality through constructive challenge. 
        You always back your challenges with specific regulatory evidence.""",
        tools=[
            search_easa_regulations,
            get_easa_regulation,
            get_regulatory_chain,
            list_easa_categories,
            validate_text_compliance,
            get_easa_statistics
        ],
        verbose=True,
        allow_delegation=False,
        llm=llm_config["model"]
    )


# ============================================================================
# CrewAI Tasks Configuration
# ============================================================================

def create_audit_task(text_to_audit: str, auditor: Agent) -> Task:
    """Create the initial audit task"""
    return Task(
        description=f"""Conduct a comprehensive compliance audit of the following text against EASA regulations:

TEXT TO AUDIT:
{text_to_audit}

AUDIT REQUIREMENTS:
1. Identify ALL applicable EASA regulations for this text
2. For each requirement in the text, determine if it complies with EASA regulations
3. Document EVERY non-compliance or ambiguous statement
4. Cite specific regulation references (e.g., ORO.FTL.110, AMC1 ORO.FC.115)
5. Provide the exact regulatory requirement for comparison
6. Assess criticality level: HIGH (safety-critical), MEDIUM (operational impact), LOW (administrative)

Use the available tools to:
- Search for relevant regulations
- Retrieve exact regulation text
- Get complete regulatory chains
- Validate compliance programmatically

OUTPUT FORMAT (provide structured data for each finding):
- Finding ID
- Criticality level
- Text excerpt from the document
- Regulation reference(s)
- Issue description
- Exact regulatory requirement
- Recommended correction
""",
        agent=auditor,
        expected_output="""A detailed list of compliance findings with:
- Unique ID for each finding
- Criticality level (HIGH/MEDIUM/LOW)
- Exact text excerpt that has the issue
- Specific EASA regulation reference(s)
- Clear description of the non-compliance
- The exact regulatory requirement
- Recommended corrective action"""
    )


def create_challenge_task(auditor: Agent, qa_challenger: Agent) -> Task:
    """Create the QA challenge task"""
    return Task(
        description="""Review the auditor's findings with a critical eye. Your responsibilities:

VERIFICATION TASKS:
1. Verify each regulation reference is correct and applicable
2. Check if the interpretation of regulations is accurate
3. Identify any findings that may be incorrect or overstated
4. Find any compliance issues that were MISSED by the auditor
5. Validate the criticality levels assigned
6. Ensure recommendations are appropriate and feasible

CHALLENGE PROCESS:
- For each finding, cross-check the regulation using the tools
- Look for alternative interpretations or exemptions
- Search for additional regulations that might apply
- Verify that the text excerpt accurately represents the issue
- Question any ambiguous criticality assessments

Use the same tools to independently verify:
- Regulation references
- Regulatory requirements
- Compliance gaps

OUTPUT FORMAT:
For each finding from the auditor:
- Finding ID (reference to auditor's finding)
- QA Status: CONFIRMED / CHALLENGED / REJECTED / MODIFIED
- Justification with regulatory evidence
- Additional findings missed by the auditor (if any)
""",
        agent=qa_challenger,
        expected_output="""A comprehensive QA review containing:
- Validation status for each auditor finding
- Specific evidence supporting confirmation or challenge
- Any additional findings not identified by the auditor
- Corrections to criticality levels if needed
- Final list of validated findings"""
        # Note: context will be set in create_crew() after task objects are created
    )


def create_final_report_task(auditor: Agent, qa_challenger: Agent, text_to_audit: str) -> Task:
    """Create the final report consolidation task"""
    return Task(
        description="""Consolidate the audit findings and QA review into a final compliance report.

CONSOLIDATION REQUIREMENTS:
1. Include only VALIDATED findings (confirmed by QA)
2. Incorporate additional findings identified by QA
3. Apply any criticality adjustments recommended by QA
4. Resolve any disagreements with clear regulatory justification
5. Organize findings by criticality and regulatory category
6. Provide an executive summary

REPORT STRUCTURE (Markdown format):
# EASA Compliance Audit Report

## Executive Summary
- Date and time of analysis
- Text analyzed (brief excerpt)
- Total findings: X
- Breakdown by criticality: HIGH (X), MEDIUM (X), LOW (X)
- Overall compliance assessment

## Detailed Findings

### HIGH CRITICALITY FINDINGS
For each finding:
#### Finding [ID]: [Brief Title]
- **Criticality**: HIGH
- **Regulation Reference**: [Exact reference]
- **Text Excerpt**: "[quote from audited text]"
- **Issue Description**: [What is wrong]
- **Regulatory Requirement**: [Exact quote from regulation]
- **Recommendation**: [How to fix]
- **QA Validation**: Confirmed / Modified

[Repeat for all HIGH findings]

### MEDIUM CRITICALITY FINDINGS
[Same structure]

### LOW CRITICALITY FINDINGS
[Same structure]

## Applicable Regulations Summary
List all EASA regulations referenced in this audit

## Recommendations Summary
Prioritized list of actions needed

## Conclusion
Overall assessment and next steps

IMPORTANT: Use proper Markdown formatting with headers, bold, lists, etc.
""",
        agent=auditor,  # Auditor writes final report after incorporating QA feedback
        expected_output="""A complete, well-formatted Markdown compliance audit report with:
- Executive summary with statistics
- All validated findings organized by criticality
- Complete regulatory references and quotes
- Actionable recommendations
- Professional formatting suitable for stakeholders"""
        # Note: context will be set in create_crew() after task objects are created
    )


# ============================================================================
# Compliance Crew Application
# ============================================================================

class ComplianceCrewApp:
    """Main application for EASA compliance auditing with CrewAI"""
    
    def __init__(self, provider_id: str, config_manager: ConfigManager, verbose: bool = True):
        self.provider_id = provider_id
        self.config_manager = config_manager
        self.provider_config = config_manager.get_provider(provider_id)
        self.verbose = verbose
        
        if not self.provider_config:
            raise ValueError(f"Provider '{provider_id}' not configured")
        
        # Setup LLM - use custom LLM classes for providers that don't work with litellm
        if provider_id == "hyperbolic" and HyperbolicLLM is not None:
            # Use custom HyperbolicLLM class to avoid litellm issues
            self.llm_instance = HyperbolicLLM(
                model=self.provider_config.model,
                api_key=self.provider_config.api_key,
                base_url=self.provider_config.base_url,
                temperature=0.1
            )
            self.llm_config = {"model": self.llm_instance}
        elif provider_id == "ollama" and OllamaLLM is not None:
            # Use custom OllamaLLM class to avoid litellm API key issues
            # Ollama doesn't require an API key, but litellm tries to validate it
            self.llm_instance = OllamaLLM(
                model=self.provider_config.model,
                base_url=self.provider_config.base_url,
                api_key=None,  # Not used, but kept for compatibility
                temperature=0.1
            )
            self.llm_config = {"model": self.llm_instance}
        else:
            # For OpenAI and other providers, use litellm via environment variables
            os.environ["OPENAI_API_KEY"] = self.provider_config.api_key
            os.environ["OPENAI_API_BASE"] = self.provider_config.base_url
            
            # Use OpenAI-compatible configuration
            self.llm_instance = None
            self.llm_config = {
                "model": self.provider_config.model,
            }
        
        self.mcp_client = MCPClient()
        self.crew = None
    
    async def initialize_mcp(self):
        """Initialize MCP connection"""
        global _mcp_client, _event_loop
        
        print("🔌 Connecting to MCP server...", file=sys.stderr)
        server_params = await self.mcp_client.connect()
        
        # Start MCP server and store connection
        from mcp.client.stdio import stdio_client
        
        self._stdio_context = stdio_client(server_params)
        read, write = await self._stdio_context.__aenter__()
        
        self._session_context = ClientSession(read, write)
        session = await self._session_context.__aenter__()
        
        await self.mcp_client.initialize(session)
        
        # Set global references for tool wrappers
        # IMPORTANT: Store the CURRENT event loop (where session was created)
        _mcp_client = self.mcp_client
        _event_loop = asyncio.get_running_loop()
        
        print("✅ MCP server connected with background event loop", file=sys.stderr)
    
    async def cleanup_mcp(self):
        """Cleanup MCP connection"""
        if hasattr(self, '_session_context'):
            await self._session_context.__aexit__(None, None, None)
        if hasattr(self, '_stdio_context'):
            await self._stdio_context.__aexit__(None, None, None)
    
    def create_crew(self, text_to_audit: str) -> Crew:
        """Create the compliance audit crew"""
        # Create agents
        auditor = create_compliance_auditor(self.llm_config)
        qa_challenger = create_qa_challenger(self.llm_config)
        
        # Create tasks
        audit_task = create_audit_task(text_to_audit, auditor)
        challenge_task = create_challenge_task(auditor, qa_challenger)
        final_report_task = create_final_report_task(auditor, qa_challenger, text_to_audit)
        
        # Link context manually
        challenge_task.context = [audit_task]
        final_report_task.context = [audit_task, challenge_task]
        
        # Create crew
        crew = Crew(
            agents=[auditor, qa_challenger],
            tasks=[audit_task, challenge_task, final_report_task],
            process=Process.sequential,
            verbose=self.verbose,
            memory=False  # Disable memory to avoid embedding authentication issues
        )
        
        return crew
    
    async def run_audit(self, text_to_audit: str, output_file: str):
        """Run the compliance audit"""
        print("\n" + "=" * 80)
        print("🔍 EASA Compliance Audit - CrewAI")
        print("=" * 80)
        print(f"📡 Provider: {self.provider_config.name}")
        print(f"🤖 Model: {self.provider_config.model}")
        print(f"📝 Text length: {len(text_to_audit)} characters")
        print(f"💾 Output: {output_file}")
        print("=" * 80 + "\n")
        
        # Initialize MCP
        await self.initialize_mcp()
        
        try:
            # Create and run crew
            print("🚀 Starting compliance audit crew...\n", file=sys.stderr)
            crew = self.create_crew(text_to_audit)
            
            # Run the crew in a thread to keep event loop free for MCP calls
            import concurrent.futures
            import threading
            
            result_container = {}
            exception_container = {}
            
            def run_crew_sync():
                """Run crew.kickoff() in a separate thread"""
                try:
                    result_container['result'] = crew.kickoff()
                except Exception as e:
                    exception_container['exception'] = e
            
            print("🔄 Launching crew in background thread (keeping event loop free for MCP calls)...", file=sys.stderr)
            crew_thread = threading.Thread(target=run_crew_sync, daemon=False)
            crew_thread.start()
            
            # Keep event loop active while crew runs
            while crew_thread.is_alive():
                await asyncio.sleep(0.1)  # Allow event loop to process MCP calls
            
            # Check for exceptions
            if 'exception' in exception_container:
                raise exception_container['exception']
            
            result = result_container.get('result')
            
            # Extract text from CrewOutput object
            # CrewAI returns a CrewOutput object, we need to get the string content
            report_text = str(result.raw) if hasattr(result, 'raw') else str(result)
            
            # Save report
            print(f"\n💾 Saving report to {output_file}...", file=sys.stderr)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            
            print(f"✅ Report saved successfully!", file=sys.stderr)
            print("\n" + "=" * 80)
            print("📄 REPORT PREVIEW")
            print("=" * 80)
            print(report_text[:1000] + "\n..." if len(report_text) > 1000 else report_text)
            print("=" * 80)
            
            return report_text
            
        finally:
            # Cleanup MCP connection
            await self.cleanup_mcp()


# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="EASA Compliance Audit with CrewAI"
    )
    
    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--text",
        type=str,
        help="Text to audit (as command line argument)"
    )
    input_group.add_argument(
        "--file",
        type=str,
        help="File containing text to audit"
    )
    input_group.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive mode (enter text interactively)"
    )
    
    # Other options
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output file for the compliance report (Markdown format)"
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["openai", "ollama", "hyperbolic"],
        help="LLM provider to use"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce verbosity (less agent output)"
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
    
    if provider_id not in config_manager.list_providers():
        print(f"❌ Provider '{provider_id}' not configured. Check your .env file.")
        sys.exit(1)
    
    # Get text to audit
    text_to_audit = None
    
    if args.text:
        text_to_audit = args.text
    elif args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ File not found: {args.file}")
            sys.exit(1)
        with open(file_path, 'r', encoding='utf-8') as f:
            text_to_audit = f.read()
    elif args.interactive:
        print("\n" + "=" * 80)
        print("📝 Interactive Mode - Enter text to audit")
        print("=" * 80)
        print("Enter or paste your text below.")
        print("Press Ctrl+D (Unix) or Ctrl+Z (Windows) when done, or type 'END' on a new line:")
        print("-" * 80)
        
        lines = []
        try:
            while True:
                line = input()
                if line.strip() == "END":
                    break
                lines.append(line)
        except EOFError:
            pass
        
        text_to_audit = "\n".join(lines)
        
        if not text_to_audit.strip():
            print("❌ No text provided")
            sys.exit(1)
    
    # Validate output path
    output_path = Path(args.output)
    if output_path.exists():
        response = input(f"⚠️  File {args.output} already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("❌ Aborted")
            sys.exit(1)
    
    # Create and run audit
    try:
        app = ComplianceCrewApp(
            provider_id,
            config_manager,
            verbose=not args.quiet
        )
        await app.run_audit(text_to_audit, args.output)
        
        print(f"\n✅ Audit complete! Report saved to: {args.output}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Audit interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import io
    
    # Suppress CrewAI's FilteredStream cleanup error
    # This is a known CrewAI bug where FilteredStream tries to flush after sys.stderr is closed
    # We temporarily redirect stderr during cleanup to hide the error message
    original_stderr = sys.stderr
    
    try:
        asyncio.run(main())
    finally:
        # Temporarily suppress stderr to hide CrewAI cleanup error
        sys.stderr = io.StringIO()
        # Give time for any background cleanup
        import time
        time.sleep(0.1)
        # Restore stderr
        sys.stderr = original_stderr

