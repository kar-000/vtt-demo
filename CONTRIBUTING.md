# Contributing to VTT

## Development Setup

### 1. Clone the Repository
```bash
git clone https://github.com/kar-000/vtt-demo.git
cd vtt-demo
```

### 2. Set Up Pre-Commit Hooks

We use pre-commit hooks to automatically check code quality before commits.

**Install pre-commit:**
```bash
pip install pre-commit
```

**Install the git hooks:**
```bash
pre-commit install
```

That's it! Now pre-commit will run automatically on every commit.

### 3. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Frontend Setup
```bash
cd frontend
npm install
```

## Pre-Commit Hooks

The following checks run automatically before each commit:

### Backend (Python)
- **black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting

### Frontend (JavaScript/React)
- **prettier**: Code formatting

### General
- Trailing whitespace removal
- End-of-file fixing
- YAML syntax validation
- Large file detection
- Merge conflict detection

## Manual Checks

You can run checks manually without committing:

**Run on all files:**
```bash
pre-commit run --all-files
```

**Run on staged files only:**
```bash
pre-commit run
```

**Run specific hook:**
```bash
pre-commit run black
pre-commit run prettier
```

## Bypassing Hooks (Not Recommended)

If you absolutely need to bypass pre-commit checks:
```bash
git commit --no-verify -m "Your message"
```

⚠️ **Warning**: Bypassing hooks means your code won't be checked, and CI/CD pipelines may fail.

## Running Tests

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Code Style Guidelines

### Python (Backend)
- Follow PEP 8 with 127 character line length
- Use type hints where appropriate
- Write docstrings for public functions/classes
- Keep functions focused and single-purpose

### JavaScript/React (Frontend)
- Use functional components with hooks
- Follow React best practices
- Use meaningful variable names
- Keep components small and reusable

## Pull Request Process

1. Create a new branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Ensure all tests pass: `pytest` and `npm test`
4. Commit your changes (pre-commit hooks will run)
5. Push to your branch: `git push origin feature/your-feature-name`
6. Create a Pull Request on GitHub
7. Wait for CI/CD checks to pass
8. Request review from maintainers

## Need Help?

- Check existing issues on GitHub
- Create a new issue if you find a bug
- Ask questions in pull request discussions
