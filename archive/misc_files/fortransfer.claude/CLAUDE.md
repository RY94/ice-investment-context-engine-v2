# GLOBAL RULES CONFIGURATION for Claude Code

## CORE PRINCIPLES
- IMPLEMENTATION-FIRST APPROACH: Always provide complete, working solutions
- NO PLACEHOLDERS: Never use TODO comments or mock functions
- SECURITY-FIRST: Defensive security tasks only, no malicious code
- MINIMIZE TOKENS: Concise responses, avoid unnecessary explanations
- KISS (Keep it simple, stupid): Simplicity should be a key goal in design; choose straightforward solutions over complex ones whenever possible; simple solutions are easier to understand, maintain and debug.
- YAGNI (You aren’t gonna need it): Avoid building functionality on speculation. Implement features only when they are needed, not when you anticipate they might be useful in the future.
- Don't fix what is not broken: May suggest improvement first but do not atttempt to change the code for something that is already working, without firm running through me.
- Do not brute force.


## ANTI-PATTERNS - NEVER DO THESE
- Mock functions or placeholder implementations
- Incomplete error handling
- Committing secrets or credentials
- Creating unnecessary documentation files
- Adding comments unless explicitly requested

## WORKFLOW REQUIREMENTS
YOU MUST FOLLOW THIS SEQUENCE:
1. Use TodoWrite for multi-step tasks
2. Research codebase before implementing
3. Follow existing conventions and patterns
4. Run tests after changes
5. Execute lint/typecheck commands
6. Only commit when explicitly asked

## AI DEVELOPMENT STANDARDS
- Always check existing libraries before assuming availability
- Prefer local LLM implementation over paid APIs, unless derived business values justify the cost.
- Follow security best practices for API keys and credentials
- Implement proper error handling and logging
- Use environment variables for configuration
- Design for scalability and maintainability

## PROJECT DISCOVERY COMMANDS
- `npm run dev` / `python -m venv` / language-specific start commands
- `npm test` / `pytest` / framework testing commands  
- `npm run lint` / `ruff check` / linting tools
- `npm run build` / build processes

## TECHNOLOGY PREFERENCES
- Prefer existing project dependencies over new ones
- Follow established architectural patterns
- Use TypeScript when available
- Implement proper typing and interfaces
- Prefer functional programming patterns when appropriate

## CODE QUALITY GATES
CRITICAL: Before completing any task:
- ✅ All tests pass
- ✅ No lint errors
- ✅ No type errors
- ✅ Security best practices followed
- ✅ Performance considerations addressed

## RESPONSE FORMAT
- Direct answers without preamble
- Use file_path:line_number references
- Batch tool calls for efficiency
- Mark todos as completed immediately when done
