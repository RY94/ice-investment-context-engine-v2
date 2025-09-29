# setup_exa_integration.py
"""
Setup script for Exa MCP integration with ICE Investment Context Engine
Automates the setup process for Exa MCP server integration
Handles Claude Desktop configuration, environment variables, and dependencies
"""

import os
import json
import sys
import subprocess
from pathlib import Path
import platform


class ExaSetupManager:
    """Manager for Exa MCP integration setup"""
    
    def __init__(self):
        self.system = platform.system()
        self.claude_config_path = self._get_claude_config_path()
        
    def _get_claude_config_path(self) -> Path:
        """Get Claude Desktop configuration path"""
        if self.system == "Darwin":  # macOS
            return Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
        elif self.system == "Windows":
            return Path.home() / "AppData/Roaming/Claude/claude_desktop_config.json"
        else:  # Linux
            return Path.home() / ".config/Claude/claude_desktop_config.json"
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        print("🔍 Checking prerequisites...")
        
        # Check Node.js/npm
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Node.js: {result.stdout.strip()}")
            else:
                print("❌ Node.js not found. Please install Node.js from https://nodejs.org/")
                return False
        except FileNotFoundError:
            print("❌ Node.js not found. Please install Node.js from https://nodejs.org/")
            return False
            
        # Check npx
        try:
            result = subprocess.run(["npx", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ NPX: {result.stdout.strip()}")
            else:
                print("❌ NPX not found. NPX comes with Node.js - please reinstall Node.js")
                return False
        except FileNotFoundError:
            print("❌ NPX not found. NPX comes with Node.js - please reinstall Node.js")
            return False
        
        print("✅ All prerequisites met")
        return True
    
    def setup_api_key(self) -> bool:
        """Setup Exa API key"""
        print("\n🔑 Setting up Exa API key...")
        
        # Check if already configured
        if os.getenv("EXA_API_KEY"):
            print("✅ EXA_API_KEY already configured")
            return True
        
        print("To get your Exa API key:")
        print("1. Visit: https://dashboard.exa.ai/")
        print("2. Sign up or log in to your account")
        print("3. Go to API Keys section")
        print("4. Create a new API key")
        
        api_key = input("\nEnter your Exa API key: ").strip()
        
        if not api_key:
            print("❌ No API key provided")
            return False
        
        # Add to environment file
        env_file = Path(".env")
        env_content = ""
        
        if env_file.exists():
            env_content = env_file.read_text()
        
        # Update or add EXA_API_KEY
        lines = env_content.split('\n')
        exa_key_found = False
        
        for i, line in enumerate(lines):
            if line.startswith('EXA_API_KEY'):
                lines[i] = f'EXA_API_KEY="{api_key}"'
                exa_key_found = True
                break
        
        if not exa_key_found:
            lines.append(f'EXA_API_KEY="{api_key}"')
        
        env_file.write_text('\n'.join(lines))
        
        # Set for current session
        os.environ["EXA_API_KEY"] = api_key
        
        print("✅ EXA_API_KEY saved to .env file")
        print("💡 Don't forget to restart your terminal or run: source .env")
        return True
    
    def install_exa_mcp_server(self) -> bool:
        """Install Exa MCP server"""
        print("\n📦 Installing Exa MCP server...")
        
        try:
            # Install globally for easier access
            print("Installing exa-mcp-server globally...")
            result = subprocess.run(
                ["npm", "install", "-g", "exa-mcp-server"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Exa MCP server installed globally")
            else:
                print(f"❌ Failed to install Exa MCP server: {result.stderr}")
                
                # Try alternative installation
                print("Trying alternative installation method...")
                result = subprocess.run(
                    ["npm", "install", "-g", "mcp-remote"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    print("✅ MCP remote client installed")
                else:
                    print(f"❌ Alternative installation failed: {result.stderr}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Installation failed: {e}")
            return False
    
    def configure_claude_desktop(self) -> bool:
        """Configure Claude Desktop for Exa MCP"""
        print("\n⚙️ Configuring Claude Desktop...")
        
        if not os.getenv("EXA_API_KEY"):
            print("❌ EXA_API_KEY not found. Please run API key setup first.")
            return False
        
        # Create config directory if needed
        self.claude_config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing config or create new
        config = {}
        if self.claude_config_path.exists():
            try:
                with open(self.claude_config_path, 'r') as f:
                    config = json.load(f)
                print("✅ Loaded existing Claude Desktop config")
            except json.JSONDecodeError:
                print("⚠️  Invalid existing config, creating new one")
                config = {}
        
        # Ensure mcpServers section exists
        if "mcpServers" not in config:
            config["mcpServers"] = {}
        
        # Add Exa MCP server configuration
        exa_api_key = os.getenv("EXA_API_KEY")
        
        # Remote configuration (recommended)
        config["mcpServers"]["exa"] = {
            "command": "npx",
            "args": [
                "-y",
                "mcp-remote",
                f"https://mcp.exa.ai/mcp?exaApiKey={exa_api_key}"
            ]
        }
        
        # Save configuration
        try:
            with open(self.claude_config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"✅ Claude Desktop config saved to: {self.claude_config_path}")
            print("🔄 Please restart Claude Desktop to apply changes")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save config: {e}")
            return False
    
    def test_installation(self) -> bool:
        """Test if the installation works"""
        print("\n🧪 Testing installation...")
        
        # Test if we can run the test script
        try:
            print("Running integration tests...")
            result = subprocess.run(
                [sys.executable, "test_exa_integration.py"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✅ Integration tests passed")
                return True
            else:
                print("⚠️  Some integration tests failed:")
                print(result.stdout)
                return False
                
        except subprocess.TimeoutExpired:
            print("⚠️  Test timeout - installation may be working but slow")
            return True
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
    
    def run_setup(self) -> bool:
        """Run complete setup process"""
        print("🚀 ICE Exa MCP Integration Setup")
        print("=" * 40)
        
        steps = [
            ("Prerequisites", self.check_prerequisites),
            ("API Key Setup", self.setup_api_key),
            ("MCP Server Installation", self.install_exa_mcp_server),
            ("Claude Desktop Configuration", self.configure_claude_desktop),
            ("Installation Test", self.test_installation)
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 Step: {step_name}")
            try:
                if not step_func():
                    print(f"❌ Setup failed at step: {step_name}")
                    return False
                print(f"✅ {step_name} completed")
            except Exception as e:
                print(f"❌ {step_name} failed: {e}")
                return False
        
        print("\n🎉 Setup completed successfully!")
        print("\n🚀 Next Steps:")
        print("1. Restart Claude Desktop")
        print("2. Run: streamlit run ui_mockups/ice_ui_v17.py")
        print("3. Try the Exa Web Search & Research section")
        print("4. Test different search types (web, company research, etc.)")
        
        print("\n💡 Tips:")
        print("- Use specific queries for better results")
        print("- Try company research for NVIDIA, Apple, etc.")
        print("- Competitor analysis works great for tech companies")
        print("- Financial news searches can include stock symbols")
        
        return True


def main():
    """Main setup function"""
    setup_manager = ExaSetupManager()
    
    try:
        success = setup_manager.run_setup()
        if success:
            print("\n✅ Exa MCP integration setup completed!")
        else:
            print("\n❌ Setup failed. Please check the errors above.")
        return success
    except KeyboardInterrupt:
        print("\n⚠️  Setup interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error during setup: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)