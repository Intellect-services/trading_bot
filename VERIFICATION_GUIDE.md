# Verification Guide - Production-Ready Codebase

This guide will help you verify all the improvements made to the codebase.

## Prerequisites

Ensure you have:

- Python 3.10+ installed
- Virtual environment activated
- Git repository clean (or commit your changes first)

## Step 1: Install Updated Dependencies

```bash
# Activate your virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install/update all dependencies
pip install -r requirements.txt
```

**Expected Result**: All packages install successfully, including Ruff, pre-commit, and MkDocs.

## Step 2: Verify Code Quality Tools

### 2.1 Check Ruff Installation

```bash
ruff --version
```

**Expected Result**: Ruff version is displayed (e.g., `ruff 0.1.x`)

### 2.2 Run Ruff Linting

```bash
# Check for linting issues
ruff check .

# Auto-fix issues where possible
ruff check . --fix

# Check code formatting
ruff format --check .
```

**Expected Result**:

- No critical errors (warnings are acceptable)
- Code is properly formatted

### 2.3 Run Type Checking

```bash
mypy src/ --ignore-missing-imports --disallow-untyped-defs
```

**Expected Result**: Type checking passes or shows only minor warnings.

### 2.4 Run Security Checks

```bash
# Bandit security scan
bandit -r src/ -c pyproject.toml

# Safety dependency check
safety scan --output screen
```

**Expected Result**: No critical security vulnerabilities found.

## Step 3: Set Up Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Test pre-commit hooks manually
pre-commit run --all-files
```

**Expected Result**:

- Hooks are installed successfully
- All hooks pass (or show only minor warnings)

## Step 4: Verify Test Infrastructure

### 4.1 Check Test Structure

```bash
# Verify test directories exist
ls -la tests/
ls -la tests/unit/
ls -la tests/integration/
ls -la tests/e2e/
```

**Expected Result**: All test directories exist with `__init__.py` files.

### 4.2 Run Unit Tests

```bash
# Run all tests with coverage
pytest tests/unit/ -v --cov=src --cov-report=term-missing

# Or run specific test files
pytest tests/unit/test_models.py -v
pytest tests/unit/test_encryption.py -v
```

**Expected Result**:

- All unit tests pass
- Coverage report is generated
- Coverage is above 70%

### 4.3 Run Integration Tests

```bash
pytest tests/integration/ -v
```

**Expected Result**: Integration tests pass (may require database setup).

### 4.4 Run All Tests

```bash
# Run complete test suite
pytest --cov=src --cov-report=html --cov-report=term-missing

# Check coverage report
open htmlcov/index.html  # On macOS
# Or: xdg-open htmlcov/index.html  # On Linux
```

**Expected Result**:

- All tests pass
- Coverage report shows current coverage percentage
- HTML coverage report opens in browser

## Step 5: Verify Code Consolidation

### 5.1 Verify Duplicate Files Removed

```bash
# Check that duplicate files are gone
ls src/core/alpaca_client.py 2>&1  # Should show "No such file"
ls src/utils/alpaca_client.py 2>&1  # Should show "No such file"
ls src/core/trading_bot.py 2>&1  # Should show "No such file"
ls src/api/app.py 2>&1  # Should show "No such file"
ls src/logger.py 2>&1  # Should show "No such file"
```

**Expected Result**: All duplicate files are removed (error messages confirm they don't exist).

### 5.2 Verify Imports Work

```bash
# Test Python imports
python -c "from src.core.alpaca_service import AlpacaService; print('✓ AlpacaService import works')"
python -c "from src.core.bot import TradingBot; print('✓ TradingBot import works')"
python -c "from src.core.strategy import Strategy; print('✓ Strategy import works')"
python -c "from src.config.constants import APP_URL; print('✓ Constants import works')"
```

**Expected Result**: All imports succeed without errors.

## Step 6: Verify Application Functionality

### 6.1 Check Environment Variables

```bash
# Verify .env file exists and has required variables
cat .env | grep -E "SECRET_KEY|ENCRYPTION_KEY|SQLALCHEMY_DATABASE_URI"
```

**Expected Result**: Required environment variables are set.

### 6.2 Test Backend Startup

```bash
# Start backend (in one terminal)
python run.py

# Or use isbot script
isbot start
```

**Expected Result**:

- Backend starts without errors
- No import errors
- Server listens on configured port (default: 5002)

### 6.3 Test Frontend

```bash
# In another terminal, start frontend
cd src/frontend
npm install  # If not already done
npm run dev
```

**Expected Result**:

- Frontend starts without errors
- No console errors about missing API_URL
- Frontend connects to backend

### 6.4 Test Basic Functionality

1. Open browser to `http://localhost:5173`
2. Try to register a new account
3. Check email verification flow
4. Try to log in
5. Navigate to dashboard

**Expected Result**:

- All pages load correctly
- No console errors
- API calls work (check Network tab in browser dev tools)

## Step 7: Verify Configuration Constants

### 7.1 Check Constants File

```bash
# View constants file
cat src/config/constants.py
```

**Expected Result**: File exists with all configuration constants.

### 7.2 Test Environment Variable Override

```bash
# Test that environment variables override defaults
export DEFAULT_TRADING_SYMBOLS="TSLA,NVDA"
python -c "from src.config.constants import DEFAULT_TRADING_SYMBOLS; print(DEFAULT_TRADING_SYMBOLS)"
```

**Expected Result**: Environment variable values are used.

## Step 8: Verify Documentation

### 8.1 Check Documentation Structure

```bash
# Verify docs directory structure
ls -la docs/
ls -la docs/getting-started/
```

**Expected Result**: Documentation files exist.

### 8.2 Build Documentation Locally

```bash
# Install MkDocs dependencies (if not already installed)
pip install mkdocs-material mkdocs-git-revision-date-localized-plugin

# Build documentation
mkdocs build

# Serve documentation locally
mkdocs serve
```

**Expected Result**:

- Documentation builds without errors
- Documentation server starts on `http://127.0.0.1:8000`
- All pages are accessible

### 8.3 Verify MkDocs Configuration

```bash
# Check MkDocs config
mkdocs --version
cat mkdocs.yml
```

**Expected Result**: MkDocs is installed and configuration is valid.

## Step 9: Verify CI/CD Workflows

### 9.1 Check Workflow Files

```bash
# Verify all workflow files exist
ls -la .github/workflows/
```

**Expected Result**:

- `ci.yml` exists
- `docs.yml` exists
- `deploy-staging.yml` exists
- `deploy-production.yml` exists

### 9.2 Validate Workflow Syntax

```bash
# Check if GitHub Actions CLI is available (optional)
# If you have `act` installed:
# act -l

# Or manually verify YAML syntax
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"
python -c "import yaml; yaml.safe_load(open('.github/workflows/docs.yml'))"
```

**Expected Result**: All YAML files are valid.

## Step 10: Final Verification Checklist

Run this comprehensive check:

```bash
# Create a verification script
cat > verify_all.sh << 'EOF'
#!/bin/bash
set -e

echo "=== Verification Checklist ==="
echo ""

echo "1. Checking dependencies..."
pip list | grep -E "ruff|mypy|bandit|pytest|mkdocs" || echo "⚠ Some dependencies missing"
echo "✓ Dependencies check complete"
echo ""

echo "2. Running Ruff linting..."
ruff check . --output-format=concise || echo "⚠ Linting issues found"
echo "✓ Linting complete"
echo ""

echo "3. Running type checking..."
mypy src/ --ignore-missing-imports --disallow-untyped-defs || echo "⚠ Type checking issues found"
echo "✓ Type checking complete"
echo ""

echo "4. Running tests..."
pytest tests/unit/ -v --tb=short || echo "⚠ Some tests failed"
echo "✓ Tests complete"
echo ""

echo "5. Checking for duplicate files..."
[ ! -f "src/core/alpaca_client.py" ] && echo "✓ Duplicate alpaca_client.py removed" || echo "⚠ File still exists"
[ ! -f "src/core/trading_bot.py" ] && echo "✓ Duplicate trading_bot.py removed" || echo "⚠ File still exists"
[ ! -f "src/api/app.py" ] && echo "✓ Dead code api/app.py removed" || echo "⚠ File still exists"
echo ""

echo "6. Verifying imports..."
python -c "from src.core.alpaca_service import AlpacaService" && echo "✓ AlpacaService import works"
python -c "from src.core.bot import TradingBot" && echo "✓ TradingBot import works"
python -c "from src.config.constants import APP_URL" && echo "✓ Constants import works"
echo ""

echo "7. Checking documentation..."
[ -f "mkdocs.yml" ] && echo "✓ MkDocs config exists" || echo "⚠ MkDocs config missing"
[ -d "docs" ] && echo "✓ Docs directory exists" || echo "⚠ Docs directory missing"
echo ""

echo "=== Verification Complete ==="
EOF

chmod +x verify_all.sh
./verify_all.sh
```

**Expected Result**: All checks pass with ✓ marks.

## Step 11: Test Pre-commit Hooks (Optional)

Make a small change to trigger hooks:

```bash
# Create a test file with intentional issues
echo "import os" > test_file.py
echo "x=1" >> test_file.py
echo "y=2" >> test_file.py

# Try to commit (this will trigger pre-commit hooks)
git add test_file.py
git commit -m "Test commit" || echo "Pre-commit hooks blocked commit (expected)"

# Clean up
rm test_file.py
```

**Expected Result**: Pre-commit hooks run and may block commit if issues found.

## Troubleshooting

### If Ruff fails:

```bash
# Update Ruff
pip install --upgrade ruff
```

### If tests fail:

```bash
# Check test database
# Ensure SQLALCHEMY_DATABASE_URI is set correctly
export SQLALCHEMY_DATABASE_URI="sqlite:///:memory:"
pytest tests/ -v
```

### If imports fail:

```bash
# Ensure you're in the project root
# Ensure virtual environment is activated
# Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### If documentation build fails:

```bash
# Install MkDocs dependencies
pip install mkdocs-material mkdocs-git-revision-date-localized-plugin
```

## Success Criteria

✅ All dependencies install successfully
✅ Ruff linting passes (or shows only warnings)
✅ Type checking passes
✅ All tests pass with >70% coverage
✅ No duplicate files exist
✅ All imports work
✅ Application starts without errors
✅ Documentation builds successfully
✅ CI/CD workflow files are valid
✅ Pre-commit hooks are installed and working

If all items are checked, your codebase is production-ready! 🎉
