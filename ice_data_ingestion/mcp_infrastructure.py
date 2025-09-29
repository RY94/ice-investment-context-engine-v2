# ice_data_ingestion/mcp_infrastructure.py
"""
MCP Infrastructure Manager for ICE Investment Context Engine
Manages Model Context Protocol server connections and health monitoring
Core component for zero-cost financial data ingestion via MCP servers
Relevant files: ice_rag.py, mcp_data_manager.py, mcp_connectors.py
"""

import json
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MCPServerStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    CONNECTING = "connecting"


@dataclass
class MCPServerConfig:
    """Configuration for MCP server connections"""
    name: str
    repository: str
    command: str
    args: List[str]
    capabilities: List[str]
    cost_tier: str  # 'free', 'freemium', 'premium'
    priority: int
    connection_type: str = "stdio"
    daily_limit: Optional[int] = None
    rate_limit: Optional[int] = None


@dataclass
class MCPHealthStatus:
    """Health status of an MCP server"""
    server_name: str
    status: MCPServerStatus
    last_check: datetime
    response_time_ms: Optional[int]
    error_message: Optional[str]
    consecutive_failures: int


class MCPInfrastructureManager:
    """Core MCP infrastructure management for ICE system"""
    
    def __init__(self, claude_config_path: Optional[str] = None):
        """Initialize MCP infrastructure manager"""
        self.claude_config_path = claude_config_path or self._get_default_claude_config()
        self.mcp_servers = self._initialize_mcp_servers()
        self.health_status = {}
        self.connection_pool = {}
        self.last_health_check = None
        
    def _get_default_claude_config(self) -> str:
        """Get default Claude Desktop config path"""
        import platform
        system = platform.system()
        
        if system == "Darwin":  # macOS
            return str(Path.home() / "Library/Application Support/Claude/claude_desktop_config.json")
        elif system == "Windows":
            return str(Path.home() / "AppData/Roaming/Claude/claude_desktop_config.json")
        else:  # Linux
            return str(Path.home() / ".config/Claude/claude_desktop_config.json")
    
    def _initialize_mcp_servers(self) -> Dict[str, MCPServerConfig]:
        """Initialize MCP server configurations based on strategy document"""
        return {
            'yahoo_finance': MCPServerConfig(
                name='yahoo_finance',
                repository='Alex2Yang97/yahoo-finance-mcp',
                command='uv',
                args=['--directory', '/path/to/yahoo-finance-mcp', 'run', 'server.py'],
                capabilities=['historical_data', 'real_time_quotes', 'company_info', 'financial_statements'],
                cost_tier='free',
                priority=1,
                rate_limit=None  # No limits for free Yahoo Finance
            ),
            'sec_edgar': MCPServerConfig(
                name='sec_edgar',
                repository='stefanoamorelli/sec-edgar-mcp',
                command='python',
                args=['/path/to/sec-edgar-mcp/server.py'],
                capabilities=['sec_filings', 'xbrl_parsing', 'insider_trading', 'company_lookup'],
                cost_tier='free',
                priority=1,
                rate_limit=10  # SEC API: 10 requests/second
            ),
            'alpha_vantage': MCPServerConfig(
                name='alpha_vantage',
                repository='berlinbra/alpha-vantage-mcp',
                command='node',
                args=['/path/to/alpha-vantage-mcp/server.js'],
                capabilities=['real_time_data', 'technical_indicators', 'news_sentiment', 'fundamentals'],
                cost_tier='freemium',
                priority=2,
                daily_limit=500,  # Free tier: 500 requests/day
                rate_limit=5  # 5 requests/minute
            ),
            'invest_mcp': MCPServerConfig(
                name='invest_mcp',
                repository='arrpitk/InvestMCP',
                command='python',
                args=['/path/to/invest-mcp/server.py'],
                capabilities=['sentiment_analysis', 'technical_analysis', 'portfolio_optimization', 'screening'],
                cost_tier='free',
                priority=2,
                rate_limit=None
            )
        }
    
    async def setup_claude_desktop_integration(self) -> bool:
        """Configure Claude Desktop for MCP server integration"""
        try:
            config_path = Path(self.claude_config_path)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Build MCP servers configuration
            mcp_config = {
                "mcpServers": {}
            }
            
            for server_name, server_config in self.mcp_servers.items():
                mcp_config["mcpServers"][server_name] = {
                    "command": server_config.command,
                    "args": server_config.args
                }
            
            # Write configuration
            with open(config_path, 'w') as f:
                json.dump(mcp_config, f, indent=2)
                
            logger.info(f"Claude Desktop MCP configuration written to {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Claude Desktop integration: {e}")
            return False
    
    async def validate_mcp_setup(self) -> Dict[str, bool]:
        """Validate all MCP servers are accessible and functioning"""
        validation_results = {}
        
        for server_name in self.mcp_servers:
            try:
                # Simulate MCP health check (actual implementation would use MCP protocol)
                health_status = await self._check_server_health(server_name)
                validation_results[server_name] = health_status.status == MCPServerStatus.HEALTHY
                
            except Exception as e:
                logger.error(f"MCP server {server_name} validation failed: {e}")
                validation_results[server_name] = False
                
        return validation_results
    
    async def _check_server_health(self, server_name: str) -> MCPHealthStatus:
        """Check health of a specific MCP server"""
        start_time = datetime.now()
        
        try:
            # Use real MCP client to check server health
            from .mcp_client_manager import mcp_client_manager
            
            # Check if server is configured and available
            server_status = await mcp_client_manager.get_server_status(server_name)
            
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            if server_status.get("status") == "healthy":
                is_healthy = True
                error_message = None
            else:
                is_healthy = False
                error_message = f"Server status: {server_status.get('status', 'unknown')}"
            
            status = MCPHealthStatus(
                server_name=server_name,
                status=MCPServerStatus.HEALTHY if is_healthy else MCPServerStatus.UNHEALTHY,
                last_check=datetime.now(),
                response_time_ms=response_time,
                error_message=error_message,
                consecutive_failures=0 if is_healthy else 1
            )
            
            self.health_status[server_name] = status
            return status
            
        except Exception as e:
            error_status = MCPHealthStatus(
                server_name=server_name,
                status=MCPServerStatus.UNHEALTHY,
                last_check=datetime.now(),
                response_time_ms=None,
                error_message=str(e),
                consecutive_failures=self.health_status.get(server_name, MCPHealthStatus(
                    server_name, MCPServerStatus.UNKNOWN, datetime.now(), None, None, 0
                )).consecutive_failures + 1
            )
            
            self.health_status[server_name] = error_status
            return error_status
    
    async def monitor_server_health(self, check_interval: int = 300) -> None:
        """Continuously monitor MCP server health"""
        while True:
            try:
                logger.info("Starting MCP server health check cycle")
                
                for server_name in self.mcp_servers:
                    await self._check_server_health(server_name)
                    
                self.last_health_check = datetime.now()
                
                # Log health summary
                healthy_count = sum(1 for status in self.health_status.values() 
                                   if status.status == MCPServerStatus.HEALTHY)
                total_count = len(self.mcp_servers)
                
                logger.info(f"Health check complete: {healthy_count}/{total_count} servers healthy")
                
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    def get_healthy_servers(self) -> List[str]:
        """Get list of currently healthy MCP servers"""
        return [
            server_name for server_name, status in self.health_status.items()
            if status.status == MCPServerStatus.HEALTHY
        ]
    
    def get_servers_by_capability(self, capability: str) -> List[str]:
        """Get MCP servers that support a specific capability"""
        matching_servers = []
        
        for server_name, server_config in self.mcp_servers.items():
            if capability in server_config.capabilities:
                # Only return if server is healthy
                if (server_name in self.health_status and 
                    self.health_status[server_name].status == MCPServerStatus.HEALTHY):
                    matching_servers.append(server_name)
                    
        # Sort by priority (lower number = higher priority)
        matching_servers.sort(key=lambda s: self.mcp_servers[s].priority)
        return matching_servers
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary for MCP server usage"""
        return {
            'total_monthly_cost': 0,  # All MCP servers are free
            'premium_savings': 577,   # Monthly savings vs premium APIs
            'enterprise_savings': 6177,  # Monthly savings vs enterprise APIs
            'free_servers': len([s for s in self.mcp_servers.values() if s.cost_tier == 'free']),
            'freemium_servers': len([s for s in self.mcp_servers.values() if s.cost_tier == 'freemium']),
            'total_servers': len(self.mcp_servers)
        }
    
    def get_status_dashboard_data(self) -> Dict[str, Any]:
        """Get data for status dashboard"""
        now = datetime.now()
        
        dashboard_data = {
            'last_updated': now.isoformat(),
            'servers': {},
            'summary': {
                'total_servers': len(self.mcp_servers),
                'healthy_servers': len(self.get_healthy_servers()),
                'cost_savings': self.get_cost_summary()
            }
        }
        
        for server_name, server_config in self.mcp_servers.items():
            health_status = self.health_status.get(server_name)
            
            dashboard_data['servers'][server_name] = {
                'name': server_config.name,
                'repository': server_config.repository,
                'capabilities': server_config.capabilities,
                'cost_tier': server_config.cost_tier,
                'priority': server_config.priority,
                'status': health_status.status.value if health_status else 'unknown',
                'last_check': health_status.last_check.isoformat() if health_status else None,
                'response_time_ms': health_status.response_time_ms if health_status else None,
                'error_message': health_status.error_message if health_status else None
            }
            
        return dashboard_data


# Singleton instance for global access
mcp_infrastructure = MCPInfrastructureManager()


async def initialize_mcp_infrastructure() -> bool:
    """Initialize MCP infrastructure and start monitoring"""
    try:
        # Setup Claude Desktop integration
        setup_success = await mcp_infrastructure.setup_claude_desktop_integration()
        if not setup_success:
            logger.warning("Claude Desktop integration setup failed")
            
        # Validate MCP servers
        validation_results = await mcp_infrastructure.validate_mcp_setup()
        healthy_servers = sum(1 for result in validation_results.values() if result)
        total_servers = len(validation_results)
        
        logger.info(f"MCP validation complete: {healthy_servers}/{total_servers} servers healthy")
        
        # Start health monitoring in background
        asyncio.create_task(mcp_infrastructure.monitor_server_health())
        
        return healthy_servers > 0
        
    except Exception as e:
        logger.error(f"Failed to initialize MCP infrastructure: {e}")
        return False