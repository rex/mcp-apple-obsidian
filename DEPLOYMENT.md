# MCP Apple Obsidian - Deployment Guide

This guide covers all methods for deploying and distributing the MCP Apple Obsidian server.

## Table of Contents

1. [PyPI Publication (Recommended)](#pypi-publication)
2. [GitHub Releases](#github-releases)
3. [Local Installation](#local-installation)
4. [MCP Server Configuration](#mcp-server-configuration)
5. [Distribution Methods](#distribution-methods)

---

## PyPI Publication (Recommended)

Publishing to PyPI makes the package installable via `pip` and `uvx`.

### Prerequisites

- PyPI account (create at [pypi.org](https://pypi.org))
- API token from PyPI (recommended over password)

### Step-by-Step

```bash
# 1. Install publishing tools
pip install uv

# 2. Configure PyPI credentials
# Option A: Environment variable
export UV_PUBLISH_TOKEN="pypi-..."

# Option B: Keyring (secure)
uv keyring set pypi

# 3. Build and test on TestPyPI first
make build
make publish-test

# 4. Install from TestPyPI to verify
uvx --from testpypi mcp-apple-obsidian

# 5. Publish to production PyPI
make publish
```

### Using the Makefile

```bash
# One-command release workflow
make release VERSION=0.1.0

# Individual steps
make bump-version VERSION=0.1.0
make build
make publish-test
make publish
```

### PyPI Package Details

After publishing, users can install via:

```bash
# Direct pip install
pip install mcp-apple-obsidian

# Using uv (faster)
uv pip install mcp-apple-obsidian

# Run without installing (uvx)
uvx mcp-apple-obsidian
```

---

## GitHub Releases

GitHub Releases provide downloadable assets and release notes.

### Automated Release (Recommended)

Create `.github/workflows/release.yml`:

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install uv
        run: pip install uv
      
      - name: Build
        run: |
          uv sync
          uv build
      
      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            dist/*.whl
            dist/*.tar.gz
          generate_release_notes: true
      
      - name: Publish to PyPI
        env:
          UV_PUBLISH_TOKEN: ${{ secrets.PYPI_TOKEN }}
        run: uv publish dist/*
```

### Manual Release

```bash
# 1. Create and push a tag
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0

# 2. Build release assets
make build

# 3. Create GitHub release
gh release create v0.1.0 \
  --title "v0.1.0" \
  --notes "Release notes..." \
  dist/*.whl dist/*.tar.gz
```

---

## Local Installation

For development or testing before publication.

### Method 1: Editable Install

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-apple-obsidian.git
cd mcp-apple-obsidian

# Install in editable mode
make install-dev

# Or manually:
uv pip install -e .
```

### Method 2: Direct from Git

```bash
# Install directly from GitHub
pip install git+https://github.com/yourusername/mcp-apple-obsidian.git

# Specific version/branch
pip install git+https://github.com/yourusername/mcp-apple-obsidian.git@v0.1.0
```

### Method 3: Using Makefile

```bash
# Set up everything
make setup

# Install for local testing
make install-local

# Configure for Claude
make install-claude

# Configure for Kimi
make install-kimi
```

---

## MCP Server Configuration

### Claude Desktop (macOS)

**Config file:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "apple-obsidian": {
      "command": "uvx",
      "args": ["mcp-apple-obsidian"],
      "env": {
        "OBSIDIAN_DEFAULT_VAULT": "My Vault"
      }
    }
  }
}
```

**Install command:**
```bash
make install-claude
```

### Kimi CLI (macOS/Linux)

**Config file:** `~/.kimi/mcp.json`

```json
{
  "mcpServers": {
    "apple-obsidian": {
      "command": "uvx",
      "args": ["mcp-apple-obsidian"],
      "env": {
        "OBSIDIAN_DEFAULT_VAULT": "My Vault"
      }
    }
  }
}
```

**Install command:**
```bash
make install-kimi
```

### Cursor (VS Code)

**Config file:** `.cursor/mcp.json` or global settings

```json
{
  "mcpServers": {
    "apple-obsidian": {
      "command": "uvx",
      "args": ["mcp-apple-obsidian"],
      "env": {
        "OBSIDIAN_DEFAULT_VAULT": "My Vault"
      }
    }
  }
}
```

### Generic MCP Client

```json
{
  "mcpServers": {
    "apple-obsidian": {
      "command": "uvx",
      "args": [
        "--from",
        "mcp-apple-obsidian",
        "mcp-apple-obsidian"
      ]
    }
  }
}
```

---

## Distribution Methods

### 1. PyPI (Easiest for Users)

**Pros:**
- One-command install: `uvx mcp-apple-obsidian`
- Automatic dependency management
- Version management
- Widely supported

**Cons:**
- Requires PyPI account
- Public visibility

**Best for:** General public distribution

### 2. GitHub Releases

**Pros:**
- Direct downloads
- Release notes integration
- Versioned assets
- Free hosting

**Cons:**
- Manual download/install
- No dependency resolution

**Best for:** Beta releases, enterprise distribution

### 3. Direct Git Install

**Pros:**
- Always up-to-date
- No publication step
- Works with private repos

**Cons:**
- Requires git
- Slower installation
- No version pinning

**Best for:** Development, internal tools

### 4. Homebrew (macOS)

Create `Formula/mcp-apple-obsidian.rb`:

```ruby
class McpAppleObsidian < Formula
  include Language::Python::Virtualenv

  desc "MCP server for Obsidian on macOS"
  homepage "https://github.com/yourusername/mcp-apple-obsidian"
  url "https://files.pythonhosted.org/packages/.../mcp-apple-obsidian-0.1.0.tar.gz"
  sha256 "..."
  license "MIT"

  depends_on "python@3.11"

  resource "mcp" do
    url "https://files.pythonhosted.org/packages/.../mcp-1.0.0.tar.gz"
    sha256 "..."
  end

  # ... other dependencies

  def install
    virtualenv_install_with_resources
  end

  test do
    system bin/"mcp-apple-obsidian", "--version"
  end
end
```

**Pros:**
- Native macOS experience
- Automatic updates
- Clean uninstall

**Cons:**
- Requires Homebrew tap
- macOS only

**Best for:** macOS power users

### 5. Docker (Cross-platform)

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install uv && \
    uv sync && \
    uv pip install -e .

ENV OBSIDIAN_DEFAULT_VAULT=""
ENV OBSIDIAN_APP_PATH="/Applications/Obsidian.app"

CMD ["mcp-apple-obsidian"]
```

**Pros:**
- Cross-platform
- Isolated environment
- Easy deployment

**Cons:**
- Large image size
- No macOS app integration

**Best for:** Server deployments, CI/CD

---

## Environment Variables for Users

Document these for end users:

| Variable | Description | Default |
|----------|-------------|---------|
| `OBSIDIAN_DEFAULT_VAULT` | Default vault name | (none) |
| `OBSIDIAN_APP_PATH` | Path to Obsidian.app | `/Applications/Obsidian.app` |
| `OBSIDIAN_CREATE_BACKUPS` | Create backups before modifications | `true` |
| `OBSIDIAN_BACKUP_DIR` | Backup directory | `~/.obsidian-mcp-backups` |
| `OBSIDIAN_MAX_FILE_SIZE` | Max note size to read | `10485760` (10MB) |

---

## Pre-release Checklist

Before publishing:

```bash
# 1. Run all checks
make check

# 2. Verify tests
make test-coverage

# 3. Update version
make bump-version VERSION=0.1.0

# 4. Update CHANGELOG.md
# Edit CHANGELOG.md manually

# 5. Build and test locally
make build
make verify

# 6. Test installation
make install-local
# Test with MCP client

# 7. Publish to TestPyPI
make publish-test

# 8. Test from TestPyPI
uvx --from testpypi mcp-apple-obsidian

# 9. If all good, release
make release
```

---

## Post-Release

After publishing:

1. **Update documentation**
   - Update README with new version
   - Update API.md if needed
   - Update CHANGELOG.md

2. **Announce**
   - GitHub Discussions
   - Twitter/X
   - Obsidian Forums
   - MCP community

3. **Monitor**
   - PyPI download stats
   - GitHub issues
   - Error reports

---

## Troubleshooting

### PyPI Upload Failed

```bash
# Check credentials
uv keyring get pypi

# Or use token
UV_PUBLISH_TOKEN=pypi-... uv publish dist/*
```

### Version Already Exists

PyPI doesn't allow overwriting. Bump version:

```bash
make bump-version VERSION=0.1.1
```

### Build Artifacts Too Large

```bash
# Clean and rebuild
make clean build
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Install dependencies | `make setup` |
| Run tests | `make test` |
| Build package | `make build` |
| Test publish | `make publish-test` |
| Full release | `make release VERSION=0.1.0` |
| Install for Claude | `make install-claude` |
| Install for Kimi | `make install-kimi` |

---

## Support

- Issues: [GitHub Issues](https://github.com/yourusername/mcp-apple-obsidian/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/mcp-apple-obsidian/discussions)
- Email: your.email@example.com
