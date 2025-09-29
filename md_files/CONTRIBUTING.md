# Contributing to ICE (Investment Context Engine)

**Location**: `/docs/CONTRIBUTING.md`
**Purpose**: Development guidelines and contribution standards for ICE project
**Business Value**: Maintains code quality and development consistency
**Relevant Files**: `CLAUDE.md`, `docs/ARCHITECTURE.md`, `src/`, `tests/`

---

## 🎯 Development Philosophy

ICE is built with **simplicity**, **traceability**, and **maintainability** as core principles. Every contribution should enhance the system's ability to provide reliable investment intelligence while maintaining clean, understandable code.

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- OpenAI API key
- Git

### Development Setup
```bash
# Clone and setup
git clone <repository-url>
cd capstone-project

# Install dependencies
pip install -r requirements.txt

# Setup environment
export OPENAI_API_KEY="your-key"
export PYTHONPATH="${PYTHONPATH}:."

# Run basic tests
python -m pytest tests/
python src/simple_demo.py
```

## 📁 Project Structure

### 🗂️ Directory Organization
```
ICE-Investment-Context-Engine/
├── 📄 Root Files          # Core docs and notebooks
├── 🧠 src/               # Production application code
├── 📊 ice_data_ingestion/ # Data pipeline infrastructure
├── 🧪 tests/             # Comprehensive test suite
├── 📋 docs/              # Documentation and specs
├── 🔧 setup/             # Environment configuration
├── 📂 data/              # Data utilities and samples
├── 🗂️ archive/           # Organized backups
└── 🏗️ sandbox/           # Development prototypes
```

### 🎯 Code Organization Rules
- **Production code**: Must go in `/src/` with proper package structure
- **Infrastructure**: Data pipelines stay at root level (`ice_data_ingestion/`)
- **Prototypes**: Development experiments go in `/sandbox/` (git-ignored)
- **Tests**: Mirror `/src/` structure in `/tests/`
- **Documentation**: All docs in `/docs/` with clear organization

## 💻 Development Standards

### 🏷️ Header Comments (MANDATORY)
Every Python file must start with these 4 lines:
```python
# /path/to/file.py
# Brief description of what this file does
# Why this file exists (business purpose/value)
# RELEVANT FILES: file1.py, file2.py, file3.py
```

### 💡 Code Quality Standards
1. **Simplicity First**: Choose straightforward solutions over complex ones
2. **Extensive Comments**: Explain thought process, not obvious syntax
3. **Traceability**: Every fact must trace to verifiable sources
4. **Modularity**: Build lightweight, maintainable components
5. **Security**: Never expose API keys or credentials

### 🧪 Testing Requirements
- **End-to-End Tests**: Focus on complete user workflows
- **Integration Tests**: Test system interactions
- **Unit Tests**: For critical business logic only
- **Test Data**: Use `/tests/mock_data/` for fixtures
- **Coverage**: Aim for meaningful coverage, not 100%

### 📊 ICE-Specific Patterns
- **Edge Construction**: All graph edges must be source-attributed and timestamped
- **Query Processing**: Support 1-3 hop reasoning with confidence scoring
- **Context Assembly**: Combine short-term + long-term context
- **MCP Compatibility**: Format outputs as structured JSON
- **Evidence Grounding**: Every claim traces back to source documents

## 🔧 Development Workflow

### 🌿 Branching Strategy
- **main**: Production-ready code
- **develop**: Integration branch for new features
- **feature/**: Individual feature development
- **hotfix/**: Critical bug fixes

### 📝 Commit Guidelines
```bash
# Commit message format
type(scope): brief description

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types**: feat, fix, docs, style, refactor, test, chore

### 🔍 Pull Request Process
1. **Branch from develop**
2. **Implement feature** with tests
3. **Update documentation** as needed
4. **Run full test suite**
5. **Create PR** with clear description
6. **Address review feedback**

## 🧪 Testing Guidelines

### 🎯 Testing Philosophy
- **Business Outcome Focus**: Test complete user workflows
- **Integration over Unit**: Test system interactions
- **Real Data Scenarios**: Use realistic financial data
- **Error Handling**: Test failure modes thoroughly

### 📁 Test Structure
```
tests/
├── test_ice_lightrag/     # AI engine tests
├── test_ice_core/         # Core system tests
├── test_integration/      # End-to-end tests
├── mock_data/            # Test fixtures
└── test_runner.py        # Main test execution
```

### ▶️ Running Tests
```bash
# Full test suite
python tests/test_runner.py

# Specific module tests
python -m pytest tests/test_ice_lightrag/

# Basic functionality test
python src/ice_lightrag/test_basic.py
```

## 📚 Documentation Standards

### 📝 Documentation Types
- **Architecture**: High-level system design (`docs/ARCHITECTURE.md`)
- **API Documentation**: Function and class documentation
- **User Guides**: How-to guides for end users
- **Development Guides**: Technical implementation details

### ✍️ Writing Guidelines
- **Clear and Concise**: Favor brevity over verbosity
- **User-Focused**: Write for the intended audience
- **Examples**: Include practical code examples
- **Current**: Keep documentation up-to-date with code changes

## 🔐 Security Guidelines

### 🛡️ Security Requirements
- **No Hardcoded Secrets**: Use environment variables
- **Secure APIs**: Validate all external inputs
- **Data Privacy**: Anonymize sensitive information
- **Audit Trails**: Log security-relevant actions

### 🔑 API Key Management
```bash
# Correct: Environment variables
export OPENAI_API_KEY="sk-..."
export BLOOMBERG_API_KEY="..."

# Wrong: Hardcoded in files
api_key = "sk-actual-key-here"  # NEVER DO THIS
```

## 🐛 Issue Reporting

### 🎯 Bug Reports
Include:
- **Environment**: Python version, OS, dependencies
- **Steps to Reproduce**: Clear, minimal example
- **Expected vs Actual**: What should happen vs what happens
- **Error Messages**: Full stack traces
- **Context**: What you were trying to accomplish

### 💡 Feature Requests
Include:
- **Business Value**: Why is this feature needed?
- **User Story**: Who benefits and how?
- **Acceptance Criteria**: How to know it's complete?
- **Implementation Ideas**: Suggestions for approach

## 🤝 Code Review Guidelines

### 👀 What to Look For
- **Business Logic**: Does it solve the right problem?
- **Code Quality**: Is it clean, readable, maintainable?
- **Testing**: Are critical paths tested?
- **Documentation**: Are changes documented?
- **Security**: Are there any security implications?

### ✅ Review Checklist
- [ ] Code follows ICE-specific patterns
- [ ] All functions have proper header comments
- [ ] Business logic is well-tested
- [ ] No hardcoded secrets or credentials
- [ ] Documentation updated if needed
- [ ] Import paths work correctly
- [ ] Error handling is appropriate

## 📞 Getting Help

### 💬 Communication Channels
- **Issues**: GitHub issues for bugs and features
- **Discussions**: GitHub discussions for questions
- **Code Review**: PR comments for implementation feedback

### 📖 Documentation Resources
- **[CLAUDE.md](../CLAUDE.md)**: Claude Code development guidance
- **[ARCHITECTURE.md](./ARCHITECTURE.md)**: System architecture overview
- **[PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md)**: Directory navigation guide

---

## 🎉 Recognition

Contributors who consistently follow these guidelines and make meaningful contributions will be recognized in:
- Project README acknowledgments
- Release notes attribution
- Academic publications (if applicable)

---

**Last Updated**: September 13, 2024
**Guidelines Version**: 1.0
**Next Review**: Quarterly