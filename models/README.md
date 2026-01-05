# Model Adapters

This directory contains adapters for different LLM providers.

## Purpose
Provides a unified interface for interacting with various language models:
- Claude (Anthropic API)
- OpenAI (future)
- Local models (future)

## Structure
```
models/
├── base/           # Base adapter interface
├── claude/         # Claude API adapter
└── openai/         # OpenAI adapter (future)
```

## Responsibilities
- Abstract model-specific APIs into a common interface
- Handle model-specific prompt formatting
- Manage API keys and authentication
- Implement retries and error handling
- Support streaming responses

## Principles
- Adapter pattern: Each provider implements a common interface
- Fail gracefully: Handle API errors and rate limits
- Configurable: Model selection driven by config files
- Testable: Mock adapters for testing

## Dependencies
- Should depend only on respective SDK packages (anthropic, openai, etc.)
- Used by: orchestration/ (for agent dispatch)
