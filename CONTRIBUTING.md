# Contributing to AI Risk Radar

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help maintain a welcoming environment

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in Issues
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, Node version, AWS region)
   - Relevant logs or screenshots

### Suggesting Features

1. Check if the feature has been suggested in Issues
2. Create a new issue with:
   - Clear description of the feature
   - Use case and benefits
   - Potential implementation approach

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes**:
   - Follow existing code style
   - Add tests for new functionality
   - Update documentation as needed
4. **Run tests**: Ensure all tests pass
   ```bash
   cd backend && pytest
   ```
5. **Commit your changes**: Use clear, descriptive commit messages
6. **Push to your fork**: `git push origin feature/your-feature-name`
7. **Submit a pull request**

## Development Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pytest
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Code Style

### Python (Backend)

- Follow PEP 8
- Use type hints
- Write docstrings for functions and classes
- Keep functions focused and small
- Use Pydantic models for data validation

### TypeScript (Frontend)

- Use TypeScript strict mode
- Follow React best practices
- Use functional components with hooks
- Keep components focused and reusable

## Testing Guidelines

- Write tests for all new functionality
- Maintain or improve code coverage
- Use property-based testing (Hypothesis) for invariants
- Test edge cases and error conditions
- Mock external services (AWS, Bedrock) in unit tests

## Documentation

- Update README.md if adding features
- Add inline comments for complex logic
- Update API documentation for endpoint changes
- Include examples in docstrings

## Commit Message Format

```
type: brief description

Longer description if needed

Fixes #issue-number
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `chore`: Maintenance tasks

## Questions?

Open an issue with the `question` label or reach out to the maintainers.

Thank you for contributing!
