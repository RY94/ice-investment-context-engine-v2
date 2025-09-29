# Claude Code Setup for Mac

This directory contains everything you need to work with Claude's API and code examples on your Mac.

## 📁 What's Included

### 1. **anthropic-sdk-python/**
The official Python SDK for Claude API
- Complete source code
- Documentation and examples
- Latest version with all features

### 2. **anthropic-cookbook/**
Official cookbook with practical examples
- Code examples for common use cases
- Best practices and patterns
- Advanced features like streaming, tools, etc.

### 3. **test_claude_setup.py**
A test script to verify your setup is working correctly

## 🚀 Quick Start

### Step 1: Get Your API Key
1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Create a new API key
4. Copy the key (it starts with `sk-ant-`)

### Step 2: Set Up Your Environment
```bash
# Set your API key (replace with your actual key)
export ANTHROPIC_API_KEY="sk-ant-your-actual-key-here"

# For permanent setup, add to your ~/.zshrc file:
echo 'export ANTHROPIC_API_KEY="sk-ant-your-actual-key-here"' >> ~/.zshrc
source ~/.zshrc
```

### Step 3: Test Your Setup
```bash
python test_claude_setup.py
```

## 📚 Available Resources

### SDK Documentation
```bash
cd anthropic-sdk-python
# Open README.md or docs/ directory
```

### Cookbook Examples
```bash
cd anthropic-cookbook
# Explore various examples and tutorials
```

## 🔧 Basic Usage Examples

### Simple Chat
```python
from anthropic import Anthropic

client = Anthropic(api_key="your-api-key")
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Hello, Claude!"}]
)
print(response.content[0].text)
```

### Streaming Response
```python
with client.messages.stream(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Tell me a story"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

## 🛠️ Installation Details

The following packages are already installed:
- `anthropic` - Official Python SDK
- All required dependencies (httpx, pydantic, etc.)

## 📖 Next Steps

1. **Explore the Cookbook**: Check out `anthropic-cookbook/` for advanced examples
2. **Read the SDK Docs**: Look at `anthropic-sdk-python/README.md`
3. **Build Your Own App**: Start with the test script and modify it
4. **Join the Community**: Visit [Anthropic's Discord](https://discord.gg/anthropic)

## 🔍 Troubleshooting

### Common Issues

**API Key Not Found**
```bash
# Make sure you've set the environment variable
echo $ANTHROPIC_API_KEY
```

**Permission Errors**
```bash
# Make sure you have the right permissions
chmod +x test_claude_setup.py
```

**Import Errors**
```bash
# Reinstall the package if needed
pip install --upgrade anthropic
```

## 📞 Support

- **Anthropic Documentation**: https://docs.anthropic.com/
- **API Reference**: https://docs.anthropic.com/en/api
- **Community**: https://discord.gg/anthropic

---

**Happy coding with Claude! 🤖✨**
