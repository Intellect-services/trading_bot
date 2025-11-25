# Dependency Conflict Explanation

## The Warning You're Seeing

```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
alpaca-trade-api 3.2.0 requires urllib3<2,>1.24, but you have urllib3 2.5.0 which is incompatible.
alpaca-trade-api 3.2.0 requires websockets<11,>=9.0, but you have websockets 15.0.1 which is incompatible.
```

## Is This a Problem?

**SHORT ANSWER: Probably not - it's just a warning, not an error.**

The packages are still installed and should work. However, there may be edge cases where the version mismatch causes issues.

## Why This Happens

1. **`alpaca-trade-api`** is installed (probably from pyproject.toml or was installed separately)
2. **`alpaca-trade-api 3.2.0`** has strict version requirements:
   - `urllib3<2,>1.24` (urllib3 version less than 2)
   - `websockets<11,>=9.0` (websockets version less than 11)
3. **Your `requirements.txt`** specifies:
   - `urllib3>=2.5.0` (version 2.5.0 or higher)
   - No explicit websockets version (but something installed 15.0.1)

## What We Actually Need

**Good news:** We DON'T actually need `alpaca-trade-api`! We use our own `AlpacaService` implementation that only needs `requests`.

The only place it was used was `bot_service.py` importing enums, and I just fixed that to use our own types.

## Solutions

### Option 1: Ignore It (Easiest)
The warning is non-fatal. The app should still work. If you encounter actual errors related to urllib3 or websockets, then fix it.

### Option 2: Remove alpaca-trade-api (Best)
Since we don't need it:
```bash
pip uninstall alpaca-trade-api
```

Then remove it from `pyproject.toml` and `setup.py` if you want.

### Option 3: Pin Versions (If Option 1 causes issues)
If you need to keep `alpaca-trade-api`, update `requirements.txt`:
```txt
urllib3>=1.26.0,<2.0.0  # Compatible with both
websockets>=9.0,<11.0   # Compatible with alpaca-trade-api
```

But we don't recommend this since we don't need `alpaca-trade-api`.

## Recommendation

**Just ignore the warning for now** and test if the app works. If everything works, you're fine. If you get errors, then uninstall `alpaca-trade-api`.

The warning won't prevent the bot from starting - it's just pip being cautious about potential conflicts.

## Verification

Test if the app imports successfully:
```bash
python3 -c "from src.app import app; print('✅ App works!')"
```

If that works, you're good to go!
