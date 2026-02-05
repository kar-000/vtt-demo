# GitHub Actions Workflows

This directory contains CI/CD workflows for the VTT project.

## Workflows

### tests.yml
Runs automated tests for both backend and frontend.

**Triggers:**
- On push to master/main branch
- On pull requests to master/main
- **Nightly at 2 AM UTC** (scheduled)
- Manual trigger via workflow_dispatch

**Jobs:**
- `backend-tests`: Runs pytest on Python backend
- `frontend-tests`: Runs npm tests and builds frontend
- `notify-on-failure`: Sends notification if nightly tests fail

### quality.yml
Runs code quality checks and linting.

**Triggers:**
- On push to master/main branch
- On pull requests to master/main
- **Nightly at 3 AM UTC** (scheduled)
- Manual trigger via workflow_dispatch

**Jobs:**
- `backend-quality`: Checks Python code with black, isort, and flake8
- `frontend-quality`: Lints JavaScript/React code with ESLint and Prettier

## Running Workflows Manually

You can manually trigger any workflow from the GitHub Actions tab:
1. Go to Actions tab in your repository
2. Select the workflow you want to run
3. Click "Run workflow" button
4. Choose the branch and click "Run workflow"

## Viewing Results

- All workflow runs are visible in the Actions tab
- Failed runs will show which job/step failed
- Artifacts (test results) are uploaded and available for download
- Nightly run failures trigger notifications

## Local Testing

Before pushing, you can run the same checks locally:

**Backend:**
```bash
cd backend
python -m pytest tests/ -v
black --check app/ tests/
isort --check-only app/ tests/
flake8 app/ tests/
```

**Frontend:**
```bash
cd frontend
npm test
npm run lint
npm run build
```
