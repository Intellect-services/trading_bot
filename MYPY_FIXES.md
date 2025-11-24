# MyPy Type Checking Status

## Current Status

MyPy is configured with **gradual typing** approach:
- `disallow_untyped_defs = false` - Allows untyped functions (warns instead of errors)
- `warn_untyped_defs = true` - Warns about untyped functions
- This allows the codebase to work while gradually adding type annotations

## Error Categories

### 1. Missing Type Annotations (Most Common)
- Functions without return type annotations
- Functions without parameter type annotations
- Variables without type annotations

### 2. Type Incompatibilities
- Flask route handlers returning tuples `(Response, int)` vs expected `Response`
- Return type mismatches
- Assignment type mismatches

### 3. None Attribute Errors
- Accessing attributes on potentially None values
- Need to add None checks or type guards

## Fixing Strategy

### Phase 1: Critical Files (Done)
- ✅ `src/utils/rbac.py` - Added type annotations to decorators
- ✅ `src/models/user.py` - Added type annotations to methods
- ✅ `src/models/user_credentials.py` - Added type annotations
- ✅ `src/utils/encryption.py` - Fixed return type
- ✅ `src/config/__init__.py` - Added return type
- ✅ `src/database.py` - Added parameter type

### Phase 2: Remaining Files (Gradual)

For production-ready code, you can:

1. **Run mypy with warnings only** (current setup):
   ```bash
   mypy src/ --ignore-missing-imports
   ```
   This will show warnings but not fail the build.

2. **Fix files incrementally**:
   - Start with most-used files (`src/app.py`, `src/core/bot.py`)
   - Add type annotations gradually
   - Use `# type: ignore` for complex cases that need refactoring

3. **Enable strict checking for new code**:
   - Add `# mypy: strict` to new files
   - Gradually migrate existing files

## Recommended Approach

For now, the codebase uses **gradual typing** which is acceptable for production. The mypy configuration:
- ✅ Catches real type errors
- ✅ Warns about missing annotations
- ⚠️ Doesn't block builds (allows gradual migration)

To make it stricter later:
1. Fix type errors in critical paths first
2. Add annotations to new code
3. Gradually migrate existing code
4. Eventually set `disallow_untyped_defs = true`

## Quick Fixes for Common Patterns

### Flask Route Handlers
```python
from flask import Response
from typing import Union

@app.route("/api/endpoint")
def my_endpoint() -> Union[Response, tuple[Response, int]]:
    return jsonify({"status": "ok"}), 200
```

### None Checks
```python
user = User.query.get(user_id)
if user is None:
    return None
# Now mypy knows user is not None
return user
```

### Generic Functions
```python
from typing import TypeVar, Callable

T = TypeVar('T')

def decorator(f: Callable[..., T]) -> Callable[..., T]:
    ...
```
