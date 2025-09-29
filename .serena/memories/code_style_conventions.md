# ICE Code Style and Conventions

## Code Standards
- **Modularity**: Build lightweight, maintainable components
- **Simplicity**: Favor straightforward solutions over complex architectures
- **Traceability**: Every fact must have source attribution
- **Security**: Never expose API keys or proprietary data in commits
- **Performance**: Optimize for single developer maintainability

## Header Comments (MANDATORY)
Every file must start with these 4 comment lines:
1. Exact file location in codebase
2. Clear description of what this file does
3. Clear description of why this file exists (business purpose)
4. RELEVANT FILES: comma-separated list of 2-4 most relevant files

## Comment Requirements
- Write extensive comments explaining **thought process**, not obvious syntax
- NEVER delete explanatory comments unless wrong/obsolete
- Focus on non-obvious details, business logic, and design decisions
- Update obsolete comments rather than deleting them

## ICE-Specific Patterns
- **Edge Construction**: All edges must be source-attributed and timestamped
- **Query Processing**: Support 1-3 hop reasoning with confidence scoring
- **Context Assembly**: Combine short-term (query, session) + long-term (KG, documents) context
- **MCP Compatibility**: Format all outputs as structured JSON for tool interoperability
- **Lazy Expansion**: Build graph on-demand rather than pre-materializing
- **Evidence Grounding**: Every claim must trace back to verifiable source documents

## Python Style
- Use type hints where possible
- Docstrings for classes and public methods
- Follow PEP 8 naming conventions
- Prefer dataclasses for structured data
- Use context managers for resource handling

## Error Handling
- Implement robust retry mechanisms with circuit breakers
- Use structured logging with appropriate levels
- Validate inputs at API boundaries
- Graceful degradation for non-critical failures

## Testing Patterns
- Write general end-to-end tests that verify complete user workflows
- Store test files in `tests/` folder
- Use pytest framework
- Mock external API calls appropriately