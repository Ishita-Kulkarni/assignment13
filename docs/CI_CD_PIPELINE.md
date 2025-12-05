# CI/CD Pipeline Documentation

## Overview

This project uses GitHub Actions for continuous integration and continuous deployment (CI/CD). The pipeline automatically runs on every commit to `main` and `develop` branches, as well as on pull requests.

## Pipeline Workflow

### Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    COMMIT TO MAIN/DEVELOP                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  JOB 1: Unit & Integration Tests                            │
│  - Spin up PostgreSQL database                              │
│  - Run linting (flake8)                                     │
│  - Run pytest with coverage                                 │
│  - Upload coverage to Codecov                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  JOB 2: E2E Tests with Playwright                           │
│  - Spin up PostgreSQL database                              │
│  - Install Python & Node.js dependencies                    │
│  - Install Playwright browsers                              │
│  - Start FastAPI application                                │
│  - Run Playwright E2E tests                                 │
│  - Upload test reports & artifacts                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  JOB 3: Build & Test Docker Image                           │
│  - Build Docker image                                        │
│  - Start PostgreSQL with docker-compose                     │
│  - Run container from built image                           │
│  - Test health endpoint                                     │
│  - Test docs endpoint                                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  JOB 4: Push to Docker Hub (main branch only)               │
│  - Log in to Docker Hub                                     │
│  - Tag image with: latest, branch name, commit SHA         │
│  - Push image to Docker Hub                                 │
│  - Update Docker Hub description                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  JOB 5: Workflow Summary                                    │
│  - Generate summary report                                  │
│  - Display all job statuses                                 │
└─────────────────────────────────────────────────────────────┘
```

## Required GitHub Secrets

To enable the full CI/CD pipeline, you need to configure the following secrets in your GitHub repository:

### Setting Up Secrets

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the following secrets:

### Required Secrets

| Secret Name | Description | How to Get |
|------------|-------------|------------|
| `DOCKERHUB_USERNAME` | Your Docker Hub username | Your Docker Hub account username |
| `DOCKERHUB_TOKEN` | Docker Hub access token | Generate at https://hub.docker.com/settings/security |

### How to Generate Docker Hub Access Token

1. Log in to [Docker Hub](https://hub.docker.com/)
2. Go to **Account Settings** → **Security**
3. Click **New Access Token**
4. Give it a description (e.g., "GitHub Actions CI/CD")
5. Set permissions to **Read, Write, Delete**
6. Copy the token (you won't be able to see it again!)
7. Add it as `DOCKERHUB_TOKEN` secret in GitHub

### Optional Secrets

| Secret Name | Description | Default |
|------------|-------------|---------|
| `CODECOV_TOKEN` | Codecov integration token | Not required for public repos |

## Workflow File

**Location:** `.github/workflows/ci-cd-e2e.yml`

### Triggers

The workflow runs on:
- **Push** to `main` or `develop` branches
- **Pull requests** targeting `main` or `develop` branches

### Jobs

#### 1. Unit & Integration Tests
- **Runs on:** `ubuntu-latest`
- **Python versions:** 3.11, 3.12 (matrix)
- **Database:** PostgreSQL 15 (GitHub Actions service)
- **Steps:**
  - Checkout code
  - Set up Python environment
  - Install dependencies
  - Run flake8 linting
  - Run pytest with coverage
  - Upload coverage to Codecov

#### 2. E2E Tests with Playwright
- **Runs on:** `ubuntu-latest`
- **Dependencies:** Needs `unit-tests` to pass
- **Database:** PostgreSQL 15 (GitHub Actions service)
- **Steps:**
  - Checkout code
  - Set up Python and Node.js
  - Install dependencies (Python + Node.js)
  - Install Playwright browsers (Chromium)
  - Start FastAPI application in background
  - Run Playwright tests
  - Upload test reports and results

#### 3. Build & Test Docker Image
- **Runs on:** `ubuntu-latest`
- **Dependencies:** Needs `unit-tests` and `e2e-tests` to pass
- **Steps:**
  - Checkout code
  - Set up Docker Buildx
  - Build Docker image
  - Start PostgreSQL with docker-compose
  - Run container from built image
  - Test health and docs endpoints
  - Cleanup

#### 4. Push to Docker Hub
- **Runs on:** `ubuntu-latest`
- **Dependencies:** Needs all previous jobs to pass
- **Condition:** Only on `push` to `main` branch
- **Steps:**
  - Checkout code
  - Set up Docker Buildx
  - Log in to Docker Hub
  - Extract metadata and tags
  - Build and push Docker image with tags:
    - `latest` (for main branch)
    - `main-<commit-sha>` (unique identifier)
    - `main` (branch name)

#### 5. Workflow Summary
- **Runs on:** `ubuntu-latest`
- **Condition:** Always runs (even if previous jobs fail)
- **Steps:**
  - Generate summary report showing all job statuses

## Docker Image Tags

When pushed to Docker Hub, images are tagged with:

- **`latest`** - Latest successful build from main branch
- **`main`** - Latest from main branch
- **`main-<commit-sha>`** - Specific commit (e.g., `main-abc1234`)

Example:
```bash
docker pull yourusername/fastapi-user-management:latest
docker pull yourusername/fastapi-user-management:main
docker pull yourusername/fastapi-user-management:main-a1b2c3d
```

## Local Testing

### Test the Docker Build Locally

```bash
# Build the image
docker build -t fastapi-user-management:test .

# Run with docker-compose
docker-compose up -d

# Test the application
curl http://localhost:8000/health
curl http://localhost:8000/docs

# Cleanup
docker-compose down
```

### Run Playwright Tests Locally

```bash
# Install dependencies
npm install
npx playwright install

# Start the application
uvicorn app.main:app --reload

# In another terminal, run tests
npm test

# Or run with UI
npm run test:ui
```

### Run All Tests Locally

```bash
# Python tests
pytest tests/ -v --cov=app

# E2E tests
npm test
```

## Monitoring the Pipeline

### View Workflow Status

1. Go to your repository on GitHub
2. Click the **Actions** tab
3. Select the workflow run you want to view
4. See the status of each job

### Download Artifacts

The pipeline uploads the following artifacts:

- **Playwright Report** - HTML report of E2E test results (30 days retention)
- **Playwright Results** - Test results including screenshots/videos (30 days retention)
- **Coverage Report** - Code coverage report (uploaded to Codecov)

To download:
1. Go to the workflow run
2. Scroll down to **Artifacts**
3. Click on the artifact name to download

## Troubleshooting

### Pipeline Fails at Unit Tests

**Common causes:**
- Database connection issues
- Missing dependencies
- Test failures

**Solution:**
- Check the test logs in GitHub Actions
- Run tests locally: `pytest tests/ -v`
- Verify database configuration

### Pipeline Fails at E2E Tests

**Common causes:**
- FastAPI server not starting
- Playwright browser issues
- Element locators changed

**Solution:**
- Check if the server is starting: Look for "FastAPI server is ready" in logs
- Run tests locally: `npm test`
- Use debug mode: `npm run test:debug`

### Pipeline Fails at Docker Build

**Common causes:**
- Dockerfile syntax errors
- Missing files referenced in Dockerfile
- Build context issues

**Solution:**
- Test Docker build locally: `docker build -t test .`
- Check Dockerfile syntax
- Verify all required files are present

### Pipeline Fails at Docker Push

**Common causes:**
- Missing or incorrect Docker Hub credentials
- Invalid repository name
- Network issues

**Solution:**
- Verify `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets
- Check that the repository exists on Docker Hub
- Verify token has write permissions

### Tests Pass Locally but Fail in CI

**Common causes:**
- Environment differences
- Timing issues (race conditions)
- Database state pollution

**Solution:**
- Check environment variables in workflow file
- Add wait conditions for async operations
- Ensure tests clean up after themselves

## Best Practices

### 1. Always Run Tests Locally First
```bash
# Before pushing
pytest tests/ -v
npm test
```

### 2. Use Descriptive Commit Messages
```bash
git commit -m "feat: add user authentication endpoint"
git commit -m "fix: resolve password validation bug"
git commit -m "test: add E2E tests for login flow"
```

### 3. Check Pipeline Status Before Merging
- Wait for all checks to pass
- Review test results and coverage
- Address any failures before merging

### 4. Monitor Docker Hub for Successful Pushes
- Check Docker Hub repository after main branch commits
- Verify tags are created correctly
- Test pulling and running the published image

### 5. Keep Dependencies Updated
```bash
# Update Python dependencies
pip list --outdated

# Update Node.js dependencies
npm outdated

# Update in requirements.txt and package.json as needed
```

## Environment Variables in CI

The workflow uses the following environment variables:

```yaml
DATABASE_URL: postgresql://calculator_user:calculator_pass@localhost:5432/calculator_db
SECRET_KEY: test-secret-key-for-ci-cd-do-not-use-in-production
ALGORITHM: HS256
ACCESS_TOKEN_EXPIRE_MINUTES: 30
```

**Note:** These are for testing only. Production environment variables should be configured separately.

## Workflow Configuration

### Caching

The workflow uses caching to speed up builds:

- **pip cache** - Python dependencies
- **npm cache** - Node.js dependencies
- **Docker layer cache** - Docker build layers (GitHub Actions cache)

### Timeouts

- **FastAPI startup**: 30 seconds
- **PostgreSQL ready**: 30 seconds (with health checks)

### Test Parallelization

- Unit tests run on multiple Python versions in parallel (matrix strategy)
- E2E tests run sequentially (to avoid database conflicts)

## Cost Optimization

### For Public Repositories
- GitHub Actions is **free** for public repositories
- Unlimited minutes

### For Private Repositories
- 2,000 free minutes per month
- Additional minutes billed at standard rates
- Consider:
  - Reducing matrix size (fewer Python versions)
  - Skipping E2E tests on PRs (only run on main)
  - Using self-hosted runners

## Security Considerations

### Secrets Management
- ✅ Never commit secrets to the repository
- ✅ Use GitHub Secrets for sensitive data
- ✅ Rotate Docker Hub tokens periodically
- ✅ Use least-privilege access tokens

### Image Security
- ✅ Use official base images (python:3.11-slim)
- ✅ Keep dependencies updated
- ✅ Scan images for vulnerabilities (consider adding Trivy or Snyk)
- ✅ Use specific version tags, not `latest` in production

## Future Enhancements

Possible improvements to the CI/CD pipeline:

- [ ] Add vulnerability scanning (Trivy, Snyk)
- [ ] Add SAST (Static Application Security Testing)
- [ ] Add performance testing
- [ ] Add deployment to staging/production environments
- [ ] Add automatic release notes generation
- [ ] Add Slack/Discord notifications
- [ ] Add automatic dependency updates (Dependabot)
- [ ] Add multi-architecture builds (ARM64)

## Support

For issues with the CI/CD pipeline:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review workflow logs in GitHub Actions
3. Test locally to isolate the issue
4. Check GitHub Actions status page for service issues

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [Playwright CI/CD](https://playwright.dev/docs/ci)
- [Docker Hub Documentation](https://docs.docker.com/docker-hub/)
