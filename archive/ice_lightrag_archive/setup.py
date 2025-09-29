# lightrag/setup.py
"""
Simple setup script for ICE LightRAG integration
"""

import os
import subprocess
import sys


def install_requirements():
    """Install required packages"""
    print("📦 Installing LightRAG dependencies...")
    
    requirements_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", requirements_file
        ])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False


def check_api_key():
    """Check if OpenAI API key is set"""
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("⚠️  OPENAI_API_KEY not found in environment variables")
        print("Please set it with: export OPENAI_API_KEY='your-api-key-here'")
        return False
    else:
        print("✅ OpenAI API key found")
        return True


def main():
    """Main setup function"""
    print("🚀 Setting up ICE LightRAG integration...")
    
    # Install dependencies
    if not install_requirements():
        sys.exit(1)
    
    # Check API key
    check_api_key()
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Set OPENAI_API_KEY if not already set")
    print("2. Test with: python lightrag/test_basic.py")
    print("3. Integrate with your Streamlit app")


if __name__ == "__main__":
    main()
