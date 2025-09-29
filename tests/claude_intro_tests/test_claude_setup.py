#!/usr/bin/env python3
"""
Test script for Claude API setup
This script verifies that the Anthropic SDK is properly installed and can connect to Claude.
"""

import os
import anthropic
from anthropic import Anthropic

def test_claude_setup():
    """Test basic Claude API setup and functionality."""
    
    print("🔍 Testing Claude API Setup...")
    print("=" * 50)
    
    # Check if API key is set
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY environment variable not found!")
        print("   Please set your API key:")
        print("   export ANTHROPIC_API_KEY='your-api-key-here'")
        print("   Or add it to your .zshrc file for permanent setup")
        return False
    
    print("✅ API key found in environment variables")
    
    try:
        # Initialize the client
        client = Anthropic(api_key=api_key)
        print("✅ Anthropic client initialized successfully")
        
        # Test a simple message
        print("\n🧪 Testing Claude with a simple message...")
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=100,
            messages=[
                {
                    "role": "user",
                    "content": "Hello! Please respond with 'Hello from Claude!' and nothing else."
                }
            ]
        )
        
        print("✅ Claude responded successfully!")
        print(f"📝 Response: {message.content[0].text}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Claude API: {e}")
        return False

def show_examples():
    """Show examples of what you can do with Claude."""
    
    print("\n📚 Claude API Examples:")
    print("=" * 50)
    
    examples = [
        {
            "title": "Basic Chat",
            "description": "Simple conversation with Claude",
            "code": '''
client = Anthropic(api_key="your-api-key")
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Explain quantum computing"}]
)
print(response.content[0].text)
'''
        },
        {
            "title": "Streaming Responses",
            "description": "Get responses in real-time",
            "code": '''
with client.messages.stream(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Write a short story"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
'''
        },
        {
            "title": "Tool Use",
            "description": "Use Claude with tools/functions",
            "code": '''
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1000,
    messages=[{"role": "user", "content": "What's the weather like?"}],
    tools=[{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather information",
            "parameters": {...}
        }
    }]
)
'''
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['title']}")
        print(f"   {example['description']}")
        print(f"   Code:")
        print(f"   {example['code']}")

def show_next_steps():
    """Show next steps for using Claude."""
    
    print("\n🚀 Next Steps:")
    print("=" * 50)
    
    steps = [
        "1. Get your API key from https://console.anthropic.com/",
        "2. Set your API key: export ANTHROPIC_API_KEY='your-key'",
        "3. Explore the anthropic-cookbook directory for examples",
        "4. Check out the SDK documentation in anthropic-sdk-python/",
        "5. Start building your own Claude-powered applications!"
    ]
    
    for step in steps:
        print(f"   {step}")

if __name__ == "__main__":
    print("🤖 Claude API Setup Test")
    print("=" * 50)
    
    # Test the setup
    success = test_claude_setup()
    
    if success:
        print("\n🎉 Claude API is ready to use!")
        show_examples()
    else:
        print("\n⚠️  Setup incomplete. Please check the issues above.")
    
    show_next_steps()
