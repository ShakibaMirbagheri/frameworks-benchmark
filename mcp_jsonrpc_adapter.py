"""
JSON-RPC Adapter for MCP Servers.

This module provides adapters for MCP servers that use JSON-RPC 2.0 protocol,
including SSE (Server-Sent Events) based MCP servers.
"""

import logging
import requests
import json
import uuid
from typing import List, Dict, Any, Optional, Callable
from langchain_core.tools import Tool

logger = logging.getLogger(__name__)


class JSONRPCMCPClient:
    """Client for communicating with JSON-RPC 2.0 based MCP servers (including SSE)."""
    
    def __init__(self, base_url: str, timeout: int = 10, session_id: Optional[str] = None):
        """
        Initialize JSON-RPC MCP client.
        
        Args:
            base_url: Base URL of the MCP server (e.g., http://localhost:8080)
            timeout: Request timeout in seconds
            session_id: Optional session ID for SSE-based servers
        """
        self.base_url = base_url.rstrip('/')
        # Handle URLs that already end with /mcp
        if self.base_url.endswith('/mcp'):
            self.mcp_endpoint = self.base_url
        else:
            self.mcp_endpoint = f"{self.base_url}/mcp"
        self.timeout = timeout
        self.request_id = 1
        self.session_id = session_id or self._get_session_id()
        self.initialized = False
        self.protocol_version = "2024-11-05"
        logger.info(f"Initialized JSON-RPC MCP client for {self.base_url} with session {self.session_id}")
    
    def _get_session_id(self) -> str:
        """
        Try to get session ID from server headers, or use a default.
        
        Returns:
            Session ID to use for requests
        """
        # Check if this is a known server with a static session ID
        known_sessions = {
            'mcp-server-github-ai.n3s.ai': 'github-mcp-session',
            'github-ai.n3s.ai': 'github-mcp-session',
        }
        
        # Extract hostname from endpoint
        for hostname, session_id in known_sessions.items():
            if hostname in self.base_url:
                logger.info(f"Using known session ID for {hostname}: {session_id}")
                return session_id
        
        # Try to get session ID from server headers
        try:
            logger.debug(f"Attempting to retrieve session ID from {self.mcp_endpoint}")
            response = requests.get(
                self.mcp_endpoint,
                headers={"Accept": "text/event-stream"},
                timeout=min(self.timeout, 5),  # Use shorter timeout for session ID retrieval
                allow_redirects=False
            )
            
            # Check for mcp-session-id in response headers (works even with 4xx status)
            session_id = response.headers.get('mcp-session-id', '')
            if session_id:
                logger.info(f"Retrieved session ID from server headers: {session_id}")
                return session_id
            else:
                logger.debug(f"No mcp-session-id header found in response (status: {response.status_code})")
                
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout while retrieving session ID from {self.mcp_endpoint}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error while retrieving session ID: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error retrieving session ID: {e}")
        
        # Fallback to random UUID
        random_id = str(uuid.uuid4())
        logger.info(f"Using generated session ID: {random_id}")
        return random_id
    
    def _parse_sse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Server-Sent Events (SSE) response format.
        
        Args:
            response_text: Raw SSE response text
            
        Returns:
            Parsed JSON data from the SSE event
        """
        lines = response_text.strip().split('\n')
        data_line = None
        
        for line in lines:
            if line.startswith('data: '):
                data_line = line[6:]  # Remove 'data: ' prefix
                break
        
        if data_line:
            return json.loads(data_line)
        
        # If no 'data:' prefix found, try parsing the whole response
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse SSE response: {response_text}")
            raise Exception(f"Invalid SSE response format")
    
    def _make_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a JSON-RPC 2.0 request with SSE support.
        
        Args:
            method: JSON-RPC method name
            params: Method parameters
            
        Returns:
            Response data
            
        Raises:
            Exception: If request fails
        """
        payload = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method
        }
        
        # Only add params if provided
        if params is not None:
            payload["params"] = params
        
        self.request_id += 1
        
        try:
            logger.debug(f"Making JSON-RPC request to {self.mcp_endpoint}: {method}")
            
            # Headers for SSE-based MCP servers
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "mcp-session-id": self.session_id
            }
            
            response = requests.post(
                self.mcp_endpoint,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # Check if response is SSE format
            content_type = response.headers.get('Content-Type', '')
            if 'text/event-stream' in content_type:
                result = self._parse_sse_response(response.text)
            else:
                result = response.json()
            
            if "error" in result:
                error_msg = result["error"].get("message", "Unknown error")
                error_code = result["error"].get("code", -1)
                logger.error(f"JSON-RPC error ({error_code}): {error_msg}")
                raise Exception(f"JSON-RPC error ({error_code}): {error_msg}")
            
            logger.debug(f"JSON-RPC response received: {len(str(result))} chars")
            return result.get("result", result)
            
        except requests.exceptions.Timeout:
            logger.error(f"Request to {self.mcp_endpoint} timed out")
            raise Exception(f"Request timed out after {self.timeout}s")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error to {self.mcp_endpoint}: {e}")
            raise Exception(f"Connection failed: {str(e)}")
        except Exception as e:
            logger.error(f"Error making JSON-RPC request: {e}")
            raise
    
    def _send_initialized_notification(self) -> None:
        """
        Send the initialized notification after successful initialization.
        This is required by the MCP protocol.
        """
        try:
            # Notifications don't have an id field and don't expect a response
            payload = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "mcp-session-id": self.session_id
            }
            
            # Send notification (don't wait for response)
            requests.post(
                self.mcp_endpoint,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            logger.debug("Sent initialized notification")
            
        except Exception as e:
            logger.warning(f"Failed to send initialized notification: {e}")
            # Don't raise - this is not critical
    
    def initialize(self) -> Dict[str, Any]:
        """
        Initialize the MCP connection.
        Must be called before any other methods for proper MCP protocol compliance.
        
        Returns:
            Server information and capabilities
        """
        if self.initialized:
            logger.debug(f"MCP connection already initialized for {self.base_url}")
            return {"status": "already_initialized"}
        
        try:
            logger.info(f"Initializing MCP connection to {self.base_url}")
            result = self._make_request("initialize", {
                "protocolVersion": self.protocol_version,
                "capabilities": {},
                "clientInfo": {
                    "name": "mcp-system-client",
                    "version": "1.0.0"
                }
            })
            
            # Send initialized notification per MCP protocol
            self._send_initialized_notification()
            
            self.initialized = True
            logger.info(f"MCP connection initialized successfully")
            return result
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP connection to {self.base_url}: {e}")
            raise
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from the MCP server.
        Automatically initializes the connection if not already done.
        
        Returns:
            List of tool definitions
        """
        try:
            # Initialize if not already done
            if not self.initialized:
                self.initialize()
            
            logger.info(f"Listing tools from {self.base_url}")
            result = self._make_request("tools/list", {})
            
            # Handle different response formats
            if isinstance(result, dict):
                tools = result.get("tools", [])
            elif isinstance(result, list):
                tools = result
            else:
                logger.warning(f"Unexpected tools/list response format: {type(result)}")
                tools = []
            
            logger.info(f"Found {len(tools)} tools from {self.base_url}")
            return tools
            
        except Exception as e:
            logger.error(f"Failed to list tools from {self.base_url}: {e}")
            # Return empty list instead of raising to allow graceful degradation
            return []
    
    def call_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
        """
        Call a specific tool on the MCP server.
        Automatically initializes the connection if not already done.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        try:
            # Initialize if not already done
            if not self.initialized:
                self.initialize()
            
            logger.info(f"Calling tool '{tool_name}' on {self.base_url}")
            logger.debug(f"Tool arguments: {arguments}")
            
            result = self._make_request("tools/call", {
                "name": tool_name,
                "arguments": arguments or {}
            })
            
            logger.info(f"Tool '{tool_name}' executed successfully")
            logger.debug(f"Tool result: {str(result)[:200]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to call tool '{tool_name}': {e}")
            raise


def create_langchain_tool_from_jsonrpc(
    client: JSONRPCMCPClient,
    tool_def: Dict[str, Any]
) -> Tool:
    """
    Create a LangChain Tool from a JSON-RPC tool definition.
    
    Args:
        client: JSON-RPC MCP client
        tool_def: Tool definition from the MCP server
        
    Returns:
        LangChain Tool instance
    """
    tool_name = tool_def.get("name", "unknown_tool")
    tool_description = tool_def.get("description", f"Tool: {tool_name}")
    
    def tool_function(**kwargs) -> str:
        """Execute the tool via JSON-RPC."""
        try:
            logger.info(f"Executing JSON-RPC tool: {tool_name}")
            result = client.call_tool(tool_name, kwargs)
            
            # Format result as string for LangChain
            if isinstance(result, (dict, list)):
                return json.dumps(result, indent=2)
            return str(result)
            
        except Exception as e:
            error_msg = f"Error executing {tool_name}: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    return Tool(
        name=tool_name,
        description=tool_description,
        func=tool_function
    )


def get_jsonrpc_tools_for_server(server_url: str, timeout: int = 10) -> List[Tool]:
    """
    Get all available tools from a JSON-RPC MCP server as LangChain Tools.
    
    Args:
        server_url: URL of the MCP server
        timeout: Request timeout in seconds
        
    Returns:
        List of LangChain Tool instances
    """
    try:
        logger.info(f"Getting JSON-RPC tools from {server_url}")
        
        # Create client
        client = JSONRPCMCPClient(server_url, timeout=timeout)
        
        # List available tools
        tool_definitions = client.list_tools()
        
        if not tool_definitions:
            logger.warning(f"No tools found from {server_url}")
            return []
        
        # Create LangChain tools
        tools = []
        for tool_def in tool_definitions:
            try:
                tool = create_langchain_tool_from_jsonrpc(client, tool_def)
                tools.append(tool)
                logger.debug(f"Created LangChain tool: {tool.name}")
            except Exception as e:
                logger.error(f"Failed to create tool from {tool_def}: {e}")
                continue
        
        logger.info(f"Successfully created {len(tools)} LangChain tools from {server_url}")
        return tools
        
    except Exception as e:
        logger.error(f"Failed to get JSON-RPC tools from {server_url}: {e}")
        return []


def test_jsonrpc_server(server_url: str, timeout: int = 5) -> tuple[bool, Optional[str]]:
    """
    Test connection to a JSON-RPC MCP server (including SSE-based servers).
    
    Args:
        server_url: URL of the MCP server
        timeout: Request timeout in seconds
        
    Returns:
        Tuple of (is_connected, error_message)
    """
    try:
        client = JSONRPCMCPClient(server_url, timeout=timeout)
        
        # Try to initialize the connection
        try:
            client.initialize()
        except Exception as init_error:
            logger.warning(f"Initialization failed, but will try to list tools anyway: {init_error}")
        
        # Try to list tools
        tools = client.list_tools()
        
        if tools is not None:  # Even empty list means success
            return True, None
        else:
            return False, "Failed to get tools list"
            
    except Exception as e:
        return False, str(e)

