# MCP Apple Obsidian - Project Summary

## Overview
A comprehensive Model Context Protocol (MCP) server for Obsidian on macOS with 42 tools for vault management, notes, properties, tags, tasks, and app control.

## Project Structure

```
mcp-apple-obsidian/
├── src/mcp_apple_obsidian/     # Source code
│   ├── __init__.py             # Package entry point
│   ├── server.py               # MCP server (42 tools)
│   ├── config.py               # Configuration management
│   ├── vault_fs.py             # File system operations
│   ├── applescript.py          # AppleScript interface
│   └── uri_handler.py          # URI scheme handler
├── tests/                       # Test suite (138 tests)
│   ├── test_import.py          # Import tests (9)
│   ├── test_vault_fs.py        # File system tests (62)
│   ├── test_applescript.py     # AppleScript tests (19)
│   ├── test_uri_handler.py     # URI handler tests (24)
│   └── test_server_integration.py # Integration tests (24)
├── .github/workflows/           # CI/CD
│   ├── test.yml                # Test workflow
│   └── release.yml             # Release workflow
├── examples/                    # Example configurations
├── Makefile                     # Build automation
├── pyproject.toml              # Project configuration
├── uv.lock                     # Dependency lock file
├── README.md                   # Main documentation
├── API.md                      # API reference
├── API_SPEC.json               # Machine-readable API spec
├── AGENTS.md                   # Development guide
├── TESTING.md                  # Testing documentation
├── DEPLOYMENT.md               # Deployment guide
├── CHANGELOG.md                # Version history
└── LICENSE                     # MIT License
```

## Key Metrics

| Metric | Value |
|--------|-------|
| **MCP Tools** | 42 |
| **Test Coverage** | 138 tests, 100% |
| **Lines of Code** | ~3,500 (source) |
| **Lines of Tests** | ~2,800 |
| **Test Execution Time** | ~2 seconds |

## Tools by Category

| Category | Count | Tools |
|----------|-------|-------|
| Vault Management | 3 | list, info, stats |
| Note Reading | 3 | read, list, metadata |
| Note Writing | 6 | write, create, delete, move, append, prepend |
| Properties | 5 | get, set, delete, search |
| Tags | 7 | get, add, remove, rename (note/vault), list all |
| Tasks | 7 | get, add, complete, uncomplete, delete, update, search |
| Search | 2 | search notes, find backlinks |
| App Control | 9 | check, launch, open, focus, etc. |

## Makefile Targets

```bash
make setup              # Setup dev environment
make test               # Run all tests
make test-coverage      # Run with coverage
make lint               # Run linters
make format             # Format code
make check              # Run all checks
make build              # Build distribution
make publish-test       # Publish to TestPyPI
make publish            # Publish to PyPI
make release VERSION=x  # Full release
make install-claude     # Configure for Claude
make install-kimi       # Configure for Kimi
make inspector          # Run MCP Inspector
```

## Deployment Options

1. **PyPI** (Recommended)
   ```bash
   uvx mcp-apple-obsidian
   ```

2. **GitHub Releases**
   - Download wheel/sdist
   - Manual installation

3. **Direct from Git**
   ```bash
   pip install git+https://github.com/...
   ```

4. **Local Development**
   ```bash
   make install-local
   ```

## CI/CD

- **Test Workflow**: Runs on macOS + Ubuntu, Python 3.11 + 3.12
- **Release Workflow**: Triggered by version tags
- **Auto-publish**: Publishes to PyPI on release

## Documentation

| Document | Purpose |
|----------|---------|
| README.md | User-facing overview |
| API.md | Complete API reference |
| API_SPEC.json | Machine-readable spec |
| AGENTS.md | Development guide |
| TESTING.md | Testing documentation |
| DEPLOYMENT.md | Deployment guide |
| CHANGELOG.md | Version history |

## License

MIT License - See LICENSE file

## Quick Start for Developers

```bash
# Clone and setup
git clone <repo>
cd mcp-apple-obsidian
make setup

# Run tests
make test

# Build and verify
make build
make verify

# Configure for your MCP client
make install-claude  # or make install-kimi
```
