# Testing Guide

This document explains how to run tests locally and how the CI/CD pipeline works.

## Running Tests Locally

### API Tests (Python)

The API uses pytest for unit and integration testing.

```bash
# Navigate to API directory
cd apps/api

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Run all tests
pytest -v

# Run specific test file
pytest tests/test_sessions.py -v

# Run repository layout test
pytest tests/test_repo_layout.py -v

# Run with coverage
pytest --cov=vibeforge_api --cov-report=term-missing

# Run tests matching a pattern
pytest -k "test_workspace" -v
```

### UI Build (TypeScript/React)

The UI uses Vite for building and TypeScript for type checking.

```bash
# Navigate to UI directory
cd apps/ui

# Install dependencies (if not already installed)
npm install

# Build the UI (checks TypeScript compilation)
npm run build

# Run development server
npm run dev

# Type check without building
npx tsc --noEmit
```

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration.

### Workflow: `.github/workflows/ci.yml`

Triggers on:
- Push to `master` or `main` branch
- Pull requests to `master` or `main` branch

Jobs:
1. **API Tests** - Runs pytest on Python 3.11
   - Installs dependencies from `apps/api/requirements.txt`
   - Runs all pytest tests
   - Runs repository layout test to ensure structure integrity

2. **UI Build** - Builds UI with Node.js 20
   - Installs dependencies from `apps/ui/package-lock.json`
   - Runs `npm run build` to verify TypeScript compilation

### Caching

The CI workflow caches:
- Python pip packages
- Node.js npm packages

This speeds up subsequent runs.

## Test Organization

### API Tests

Located in `apps/api/tests/`:
- `test_sessions.py` - Session API endpoint tests
- `test_workspace.py` - Workspace management tests
- `test_patch.py` - Patch application tests
- `test_artifacts.py` - Artifact storage tests
- `test_command_runner.py` - Command execution tests
- `test_verifiers.py` - Build/test verification tests
- `test_gates.py` - Gate pipeline tests
- `test_config_loader.py` - Configuration loading tests
- `test_e2e_demo.py` - End-to-end workflow tests
- `test_repo_layout.py` - Repository structure validation

### Test Fixtures

Located in `apps/api/tests/fixtures/`:
- `node-project/` - Sample Node.js project for integration testing

## Writing Tests

### API Test Example

```python
import pytest
from vibeforge_api.models.types import SessionPhase

def test_create_session():
    """Test session creation."""
    # Arrange
    ...

    # Act
    ...

    # Assert
    assert session.phase == SessionPhase.QUESTIONNAIRE
```

### Best Practices

1. **Use descriptive test names**: `test_should_reject_invalid_email`
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Test one thing per test**: Each test should verify a single behavior
4. **Use fixtures for setup**: Share common setup code
5. **Mock external dependencies**: Don't call real APIs in tests
6. **Clean up after tests**: Use fixtures with cleanup or teardown

## Coverage Goals

- **Minimum**: 70% line coverage for critical paths
- **Target**: 85% line coverage overall
- **Focus**: High coverage for:
  - Gates (safety-critical)
  - Command runner (security-critical)
  - Patch applier (integrity-critical)

## Local CI Testing (Optional)

You can run the CI workflow locally using [act](https://github.com/nektos/act):

```bash
# Install act (macOS)
brew install act

# List available jobs
act -l

# Run API tests job
act -j api-tests

# Run UI build job
act -j ui-build

# Run all jobs
act
```

Note: `act` requires Docker to be running.

## Troubleshooting

### Tests fail with import errors
```bash
# Make sure you're in the correct directory
cd apps/api

# Reinstall dependencies
pip install -r requirements.txt
```

### UI build fails with TypeScript errors
```bash
# Clear cache and reinstall
cd apps/ui
rm -rf node_modules dist
npm install
npm run build
```

### Pytest not found
```bash
# Ensure pytest is installed
pip install pytest

# Or install all dev dependencies
cd apps/api
pip install -r requirements.txt
```

## Future Enhancements

Planned testing improvements:
- [ ] End-to-end UI tests with Playwright
- [ ] Load testing for API endpoints
- [ ] Integration tests with real model APIs (gated behind feature flag)
- [ ] Visual regression testing for UI components
- [ ] Security scanning (SAST/DAST)
