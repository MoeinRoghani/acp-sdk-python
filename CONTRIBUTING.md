# Contributing to ACP Python

Thank you for your interest in contributing to the Agent Communication Protocol (ACP) Python implementation! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Code Style](#code-style)
- [Testing](#testing)
- [Documentation](#documentation)
- [Issue Reporting](#issue-reporting)
- [Release Process](#release-process)

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to [moein.roghani@proton.me](mailto:moein.roghani@proton.me).

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Virtual environment tool (venv, conda, or poetry)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/acp-python.git
   cd acp-python
   ```

## Development Setup

### 1. Create Virtual Environment

```bash
# Using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Using conda
conda create -n acp-python python=3.11
conda activate acp-python
```

### 2. Install Development Dependencies

```bash
# Install in development mode with all extras
pip install -e ".[dev,test,docs,validation]"

# Or using poetry
poetry install --with dev,test,docs
```

### 3. Install Pre-commit Hooks

```bash
pre-commit install
```

### 4. Verify Installation

```bash
# Run tests
pytest

# Check code style
black --check .
flake8 .
mypy acp/

# Validate package
python -m acp.utils.schema info
```

## Contributing Guidelines

### Types of Contributions

We welcome the following types of contributions:

- **🐛 Bug fixes** - Fix issues in existing code
- **✨ New features** - Add new functionality to ACP
- **📚 Documentation** - Improve docs, examples, or guides
- **🧪 Tests** - Add or improve test coverage
- **🎨 Code quality** - Refactoring, performance improvements
- **🔧 Tooling** - CI/CD, development tools, automation

### Before You Start

1. **Search existing issues** - Check if your bug/feature is already reported
2. **Open an issue** - Discuss significant changes before implementing
3. **Check compatibility** - Ensure changes work with ACP specification
4. **Review guidelines** - Read this document thoroughly

## Pull Request Process

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 2. Make Changes

- Write clear, focused commits
- Follow [conventional commits](https://conventionalcommits.org/) format:
  ```
  feat: add stream message validation
  fix: resolve OAuth token refresh issue
  docs: update API reference for tasks.create
  test: add integration tests for streaming
  ```

### 3. Run Quality Checks

```bash
# Format code
black .
isort .

# Run linting
flake8 .
mypy acp/

# Run tests
pytest
pytest --cov=acp --cov-report=html

# Validate examples
python examples/client/basic_client.py --dry-run
python examples/server/basic_server.py --validate
```

### 4. Update Documentation

- Update docstrings for new/changed functions
- Add examples for new features
- Update README.md if needed
- Add/update protocol documentation if applicable

### 5. Submit Pull Request

1. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Create pull request on GitHub
3. Fill out the PR template completely
4. Link related issues using keywords (fixes #123)

### PR Requirements

✅ **Code Quality**
- [ ] Code follows project style guide
- [ ] All tests pass
- [ ] No decrease in test coverage
- [ ] Linting passes (black, flake8, mypy)

✅ **Documentation**
- [ ] Public APIs have docstrings
- [ ] Examples updated if needed
- [ ] CHANGELOG.md updated for user-facing changes

✅ **Testing**
- [ ] New features have tests
- [ ] Bug fixes include regression tests
- [ ] Edge cases covered

✅ **Compatibility**
- [ ] Changes follow ACP specification
- [ ] Backward compatibility maintained
- [ ] Python 3.8+ compatibility

## Code Style

### Python Style

We use:
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

### Configuration

Settings in `pyproject.toml`:

```toml
[tool.black]
line-length = 88
target-version = ['py38']

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.8"
strict = true
```

### Code Conventions

```python
# Good: Clear, documented function
async def create_task(
    self,
    initial_message: Message,
    priority: TaskPriority = TaskPriority.NORMAL,
    timeout: Optional[float] = None,
) -> TaskObject:
    """
    Create a new ACP task.
    
    Args:
        initial_message: The initial message for the task
        priority: Task execution priority
        timeout: Optional timeout in seconds
        
    Returns:
        Created task object
        
    Raises:
        ACPException: If task creation fails
        ValidationError: If parameters are invalid
    """
    # Implementation here
```

## Testing

### Test Structure

```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── e2e/           # End-to-end tests
├── fixtures/      # Test data and fixtures
└── conftest.py    # Pytest configuration
```

### Writing Tests

```python
import pytest
from acp import ACPClient
from acp.models.generated import TasksCreateParams, Message, Part

class TestTaskCreation:
    @pytest.fixture
    def client(self):
        return ACPClient("https://test.example.com")
    
    @pytest.mark.asyncio
    async def test_create_task_success(self, client, mock_response):
        # Arrange
        params = TasksCreateParams(
            initialMessage=Message(
                role="user",
                parts=[Part(type="TextPart", content="Test task")]
            )
        )
        
        # Act
        result = await client.tasks_create(params)
        
        # Assert
        assert result.taskId is not None
        assert result.status == "SUBMITTED"

    def test_validation_error(self):
        with pytest.raises(ValidationError):
            TasksCreateParams(initialMessage=None)
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=acp --cov-report=html

# Run specific test types
pytest tests/unit/
pytest tests/integration/
pytest -m "not slow"  # Skip slow tests

# Run tests in parallel
pytest -n auto
```

## Documentation

### Docstring Style

Use Google-style docstrings:

```python
def validate_message(message: Message) -> ValidationResult:
    """
    Validate an ACP message structure.
    
    This function performs comprehensive validation of message content,
    including part types, encoding, and size limits.
    
    Args:
        message: The message to validate
        
    Returns:
        ValidationResult containing success status and any errors
        
    Example:
        >>> result = validate_message(message)
        >>> if result.is_valid:
        ...     print("Message is valid!")
    """
```

### Building Documentation

```bash
# Install docs dependencies
pip install -e ".[docs]"

# Build documentation
cd docs/
make html

# Serve locally
make serve
```

## Issue Reporting

### Bug Reports

Use the bug report template and include:

- **Environment**: Python version, OS, ACP version
- **Steps to reproduce**: Minimal example
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Error messages**: Full traceback if applicable

### Feature Requests

Use the feature request template and include:

- **Problem statement**: What problem does this solve?
- **Proposed solution**: How should it work?
- **Alternatives considered**: Other approaches
- **ACP specification**: How does this align with the protocol?

### Security Issues

**Do not open public issues for security vulnerabilities.**

Email security issues to [moein.roghani@proton.me](mailto:moein.roghani@proton.me) with:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if known)

## Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Run full test suite
4. Create release PR
5. Tag release after merge
6. Build and publish to PyPI
7. Update documentation

## Getting Help

- **Documentation**: [https://acp-python.readthedocs.io](https://acp-python.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/moein-roghani/acp-python/issues)
- **Discussions**: [GitHub Discussions](https://github.com/moein-roghani/acp-python/discussions)
- **Email**: [moein.roghani@proton.me](mailto:moein.roghani@proton.me)

## Recognition

Contributors are recognized in:
- `CONTRIBUTORS.md` file
- Release notes
- Documentation credits

Thank you for contributing to ACP Python! 🚀 