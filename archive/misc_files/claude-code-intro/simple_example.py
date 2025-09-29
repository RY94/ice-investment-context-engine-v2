#!/usr/bin/env python3
"""
Simple Claude API Example
This script demonstrates basic usage of Claude's API with practical examples.
"""

import os
import json
from anthropic import Anthropic

def setup_client():
    """Set up the Anthropic client with API key."""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("Please set ANTHROPIC_API_KEY environment variable")
    
    return Anthropic(api_key=api_key)

def simple_chat_example(client):
    """Demonstrate simple chat with Claude."""
    print("💬 Simple Chat Example")
    print("-" * 40)
    
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": "Explain the concept of machine learning in simple terms, as if explaining to a 10-year-old."
                }
            ]
        )
        
        print("✅ Response received:")
        print(response.content[0].text)
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def streaming_example(client):
    """Demonstrate streaming responses from Claude."""
    print("🌊 Streaming Response Example")
    print("-" * 40)
    
    try:
        print("Claude is thinking...")
        with client.messages.stream(
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": "Write a short haiku about programming."
                }
            ]
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
        print("\n✅ Streaming complete!\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def json_mode_example(client):
    """Demonstrate Claude's JSON mode for structured output."""
    print("📋 JSON Mode Example")
    print("-" * 40)
    
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": "Analyze this text and provide a JSON response with the following structure: {\"sentiment\": \"positive/negative/neutral\", \"key_topics\": [\"topic1\", \"topic2\"], \"summary\": \"brief summary\"}. Text: 'I love this new programming language! It makes coding so much easier and more enjoyable. The syntax is clean and the community is very helpful.'"
                }
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse the JSON response
        json_data = json.loads(response.content[0].text)
        print("✅ Structured JSON response:")
        print(json.dumps(json_data, indent=2))
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def conversation_example(client):
    """Demonstrate multi-turn conversation."""
    print("🔄 Multi-turn Conversation Example")
    print("-" * 40)
    
    try:
        # First message
        messages = [
            {
                "role": "user",
                "content": "Hi! I'm learning Python. Can you help me understand what a function is?"
            }
        ]
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,
            messages=messages
        )
        
        print("User: Hi! I'm learning Python. Can you help me understand what a function is?")
        print(f"Claude: {response.content[0].text}")
        
        # Add Claude's response to the conversation
        messages.append({
            "role": "assistant",
            "content": response.content[0].text
        })
        
        # Second message (follow-up question)
        messages.append({
            "role": "user",
            "content": "Can you show me a simple example of a function?"
        })
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=400,
            messages=messages
        )
        
        print(f"\nUser: Can you show me a simple example of a function?")
        print(f"Claude: {response.content[0].text}")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run all examples."""
    print("🤖 Claude API Examples")
    print("=" * 50)
    
    try:
        client = setup_client()
        print("✅ Client initialized successfully\n")
        
        # Run examples
        simple_chat_example(client)
        streaming_example(client)
        json_mode_example(client)
        conversation_example(client)
        
        print("🎉 All examples completed successfully!")
        
    except ValueError as e:
        print(f"❌ Setup Error: {e}")
        print("\nTo fix this:")
        print("1. Get your API key from https://console.anthropic.com/")
        print("2. Set it: export ANTHROPIC_API_KEY='your-key-here'")
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

if __name__ == "__main__":
    main()
