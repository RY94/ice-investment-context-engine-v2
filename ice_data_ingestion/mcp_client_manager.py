# ice_data_ingestion/mcp_client_manager.py
"""
MCP Client Manager for ICE Investment Context Engine
Manages Model Context Protocol server connections and data retrieval
Provides unified interface to MCP servers with fallback to direct APIs
Relevant files: mcp_infrastructure.py, mcp_data_manager.py, free_api_connectors.py
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from contextlib import AsyncExitStack
from dataclasses import dataclass
import json

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logging.warning("MCP SDK not available. Install with: pip install mcp")

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for MCP server"""
    name: str
    path: str
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None
    enabled: bool = True
    runtime: str = "python"  # python, node, or binary


@dataclass
class MCPResponse:
    """Standardized MCP response"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    server_name: Optional[str] = None
    processing_time: float = 0.0
    tool_name: Optional[str] = None


class MCPClientManager:
    """Manages MCP client connections and server lifecycle"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize MCP client manager"""
        if config_path is None:
            # Look for config in project root
            project_root = Path(__file__).parent.parent
            self.config_path = str(project_root / "ice_config.json")
        else:
            self.config_path = config_path
        self.servers: Dict[str, MCPServerConfig] = {}
        self.active_sessions: Dict[str, ClientSession] = {}
        self.exit_stack = AsyncExitStack()
        self.enabled = MCP_AVAILABLE
        
        self._load_config()
    
    def _load_config(self) -> None:
        """Load MCP server configurations"""
        try:
            config_path = Path(self.config_path)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    
                mcp_config = config.get('mcp_servers', {})
                
                # Set enabled state from config (but don't return early)
                self.enabled = mcp_config.get('enabled', False) and MCP_AVAILABLE
                
                if not self.enabled:
                    logger.info("MCP servers disabled in configuration")
                
                # Always load server configurations regardless of enabled state
                self._load_server_configs(mcp_config)
                        
        except Exception as e:
            logger.warning(f"Could not load MCP config: {e}")
            self.enabled = False
    
    def _load_server_configs(self, mcp_config: Dict[str, Any]) -> None:
        """Load server configurations from config"""
        # Clear existing servers
        self.servers.clear()
        
        # Load server configurations
        for server_name, server_config in mcp_config.get('servers', {}).items():
            if server_config.get('installed', False):
                self.servers[server_name] = MCPServerConfig(
                    name=server_name,
                    path=server_config['path'],
                    command=server_config.get('command', 'python'),
                    args=server_config.get('args', []),
                    env=server_config.get('env'),
                    enabled=server_config.get('enabled', True),
                    runtime=server_config.get('runtime', 'python')
                )
    
    async def connect_to_server(self, server_name: str) -> bool:
        """Connect to a specific MCP server"""
        if not self.enabled or not MCP_AVAILABLE:
            return False
            
        if server_name in self.active_sessions:
            return True  # Already connected
            
        if server_name not in self.servers:
            logger.warning(f"Server {server_name} not configured")
            return False
            
        server_config = self.servers[server_name]
        if not server_config.enabled:
            return False
            
        try:
            # Check if server path exists (resolve relative paths from project root)
            if server_config.path.startswith('./'):
                project_root = Path(__file__).parent.parent
                server_path = project_root / server_config.path[2:]
            else:
                server_path = Path(server_config.path)
                
            if not server_path.exists():
                logger.warning(f"MCP server path does not exist: {server_path}")
                return False
            
            # Create server parameters - always use absolute path
            server_params = StdioServerParameters(
                command=server_config.command,
                args=[str(server_path)],
                env=server_config.env
            )
            
            # Connect via stdio
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            stdio, write = stdio_transport
            
            # Create session
            session = await self.exit_stack.enter_async_context(
                ClientSession(stdio, write)
            )
            
            # Initialize connection
            await session.initialize()
            
            # Verify server has tools
            tools_response = await session.list_tools()
            if not tools_response.tools:
                logger.warning(f"MCP server {server_name} has no tools available")
                return False
            
            self.active_sessions[server_name] = session
            logger.info(f"Connected to MCP server {server_name} with {len(tools_response.tools)} tools")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {server_name}: {type(e).__name__}: {e}")
            logger.error(f"Server config: command={server_config.command}, path={server_config.path}")
            return False
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> MCPResponse:
        """Call a tool on a specific MCP server"""
        start_time = datetime.now()
        
        if not self.enabled or not MCP_AVAILABLE:
            return MCPResponse(
                success=False,
                error="MCP not available",
                server_name=server_name,
                tool_name=tool_name
            )
        
        # Ensure connection
        if not await self.connect_to_server(server_name):
            return MCPResponse(
                success=False,
                error=f"Could not connect to server {server_name}",
                server_name=server_name,
                tool_name=tool_name
            )
        
        try:
            session = self.active_sessions[server_name]
            result = await session.call_tool(tool_name, arguments)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return MCPResponse(
                success=True,
                data=result,
                server_name=server_name,
                tool_name=tool_name,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"MCP tool call failed: {server_name}.{tool_name}: {type(e).__name__}: {e}")
            logger.error(f"Arguments: {arguments}")
            
            return MCPResponse(
                success=False,
                error=f"{type(e).__name__}: {str(e)}",
                server_name=server_name,
                tool_name=tool_name,
                processing_time=processing_time
            )
    
    async def list_server_tools(self, server_name: str) -> Dict[str, Any]:
        """List available tools for a server"""
        if not await self.connect_to_server(server_name):
            return {}
        
        try:
            session = self.active_sessions[server_name]
            tools_response = await session.list_tools()
            
            return {
                tool.name: {
                    "description": tool.description,
                    "parameters": tool.inputSchema if hasattr(tool, 'inputSchema') else None
                }
                for tool in tools_response.tools
            }
        except Exception as e:
            logger.error(f"Failed to list tools for {server_name}: {e}")
            return {}
    
    async def get_server_status(self, server_name: str) -> Dict[str, Any]:
        """Get status of a specific server"""
        if server_name not in self.servers:
            return {"status": "not_configured"}
        
        server_config = self.servers[server_name]
        
        if not server_config.enabled:
            return {"status": "disabled"}
        
        # Resolve path properly
        if server_config.path.startswith('./'):
            project_root = Path(__file__).parent.parent
            server_path = project_root / server_config.path[2:]
        else:
            server_path = Path(server_config.path)
        
        if not server_path.exists():
            return {"status": "not_installed", "path": server_config.path}
        
        # Test connection
        connected = await self.connect_to_server(server_name)
        
        if connected:
            tools = await self.list_server_tools(server_name)
            return {
                "status": "healthy",
                "connected": True,
                "tools_count": len(tools),
                "tools": list(tools.keys())
            }
        else:
            return {"status": "connection_failed"}
    
    async def get_all_server_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all configured servers"""
        status = {}
        
        for server_name in self.servers:
            status[server_name] = await self.get_server_status(server_name)
        
        return status
    
    def is_enabled(self) -> bool:
        """Check if MCP is enabled and available"""
        return self.enabled and MCP_AVAILABLE
    
    def reload_config(self, enabled: Optional[bool] = None) -> None:
        """Reload configuration with optional enabled override"""
        # Load from file first
        self._load_config()
        
        # Override enabled state if requested
        if enabled is not None:
            self.enabled = enabled and MCP_AVAILABLE
            logger.info(f"MCP enabled state overridden to: {self.enabled}")
    
    def set_enabled(self, enabled: bool) -> None:
        """Set MCP enabled state at runtime"""
        self.enabled = enabled and MCP_AVAILABLE
        logger.info(f"MCP runtime enabled state set to: {self.enabled}")
    
    def clear_state(self) -> None:
        """Clear all sessions and reset state"""
        # Close any active sessions
        if hasattr(self, 'active_sessions'):
            self.active_sessions.clear()
        
        # Reset exit stack if needed
        # Note: We don't recreate exit_stack here as it may be in use
    
    def get_configured_servers(self) -> List[str]:
        """Get list of configured server names"""
        return list(self.servers.keys())
    
    def get_installed_servers(self) -> List[str]:
        """Get list of installed server names (regardless of enabled state)"""
        return [name for name, config in self.servers.items() if Path(config.path).exists()]
    
    async def cleanup(self) -> None:
        """Clean up all connections"""
        try:
            await self.exit_stack.aclose()
            self.active_sessions.clear()
            logger.info("MCP client connections cleaned up")
        except Exception as e:
            logger.error(f"Error during MCP cleanup: {e}")


# Singleton instance for global access
mcp_client_manager = MCPClientManager()


async def get_mcp_data(server_name: str, tool_name: str, **kwargs) -> MCPResponse:
    """Convenience function to get data from MCP server"""
    return await mcp_client_manager.call_tool(server_name, tool_name, kwargs)


async def is_mcp_available() -> bool:
    """Check if any MCP servers are available"""
    if not mcp_client_manager.is_enabled():
        return False
    
    status = await mcp_client_manager.get_all_server_status()
    return any(s.get("status") == "healthy" for s in status.values())