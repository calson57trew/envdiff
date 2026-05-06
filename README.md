# envdiff

Compare `.env` files across environments and report missing or mismatched keys.

---

## Installation

```bash
pip install envdiff
```

Or install from source:

```bash
git clone https://github.com/youruser/envdiff.git
cd envdiff && pip install -e .
```

---

## Usage

```bash
# Compare two .env files
envdiff .env.development .env.production

# Compare multiple environments against a base file
envdiff .env .env.staging .env.production
```

**Example output:**

```
Comparing .env → .env.production

  MISSING in .env.production:
    - DEBUG
    - CACHE_TTL

  MISMATCHED keys:
    - DATABASE_URL  (values differ)

2 missing, 1 mismatched
```

You can also use it programmatically:

```python
from envdiff import compare

results = compare(".env", ".env.production")
print(results.missing)
print(results.mismatched)
```

---

## Options

| Flag | Description |
|------|-------------|
| `--strict` | Exit with non-zero code if any differences are found |
| `--ignore KEY` | Ignore a specific key during comparison |
| `--json` | Output results as JSON |
| `--values` | Include actual values in the diff output (use with caution) |

---

## CI Integration

envdiff works well in CI pipelines to catch missing environment variables before deployment:

```yaml
# GitHub Actions example
- name: Check env parity
  run: envdiff .env.example .env.production --strict
```

---

## License

MIT © 2024 Your Name
