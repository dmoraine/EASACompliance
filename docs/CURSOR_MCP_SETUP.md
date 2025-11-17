# 🔌 Connect Cursor to EASA MCP Server

Practical guide to launch the MCP server and connect it to Cursor IDE.

## 📋 Prerequisites

✅ EASA database built (`easa_complete.db`)  
✅ Dependencies installed (`uv sync`)  
✅ Python 3.10+ with `uv` available

---

## 🚀 Step 1: Verify the Database

```bash
# Navigate to your project directory
cd /path/to/EASACompliance

# Verify that the database exists
ls -lh easa_complete.db

# If it doesn't exist, build it:
python build_embeddings.py \
  --xml "Easy Access Rules for Air Operations - February 2025 - xml.xml" \
  --db easa_complete.db \
  --clear
```

---

## 🧪 Step 2: Test the Server (Optional)

Before connecting Cursor, test that the server works:

```bash
cd /path/to/EASACompliance
python examples/mcp_client_test.py
```

**Expected output:**
```
✅ Server connection established
✅ 6 tools available
✅ ALL TESTS PASSED
```

---

## ⚙️ Step 3: Configure Cursor

### 3.1 Locate the Configuration File

Cursor stores its MCP configuration in:

**Linux:**
```bash
~/.config/Cursor/User/globalStorage/mcp.json
# or
~/.cursor/mcp.json
```

**macOS:**
```bash
~/Library/Application Support/Cursor/User/globalStorage/mcp.json
```

**Windows:**
```bash
%APPDATA%\Cursor\User\globalStorage\mcp.json
```

### 3.2 Create/Edit the Configuration

Create or edit the MCP configuration file:

```bash
# Create the directory if necessary
mkdir -p ~/.config/Cursor/User/globalStorage

# Edit the file
nano ~/.config/Cursor/User/globalStorage/mcp.json
```

### 3.3 Complete Configuration

**Option 1: Use the template (recommended)**

Copy the template file and replace `{PROJECT_ROOT}`:

```bash
# Copy the template
cp examples/cursor_mcp_config.json ~/.config/Cursor/User/globalStorage/mcp.json

# Replace {PROJECT_ROOT} with your absolute path
# Replace /path/to/EASACompliance with your actual path
sed -i 's|{PROJECT_ROOT}|/path/to/EASACompliance|g' ~/.config/Cursor/User/globalStorage/mcp.json
```

**Option 2: Manual configuration**

Paste this configuration, replacing `/path/to/EASACompliance` with your absolute path:

```json
{
  "mcpServers": {
    "easa-regulations": {
      "command": "/path/to/EASACompliance/.venv/bin/python",
      "args": [
        "/path/to/EASACompliance/run_mcp_server.py"
      ],
      "env": {
        "EASA_DB_PATH": "/path/to/EASACompliance/easa_complete.db",
        "EASA_MODEL": "all-MiniLM-L12-v2",
        "EASA_MAX_RESULTS": "20",
        "EASA_CACHE": "true"
      }
    }
  }
}
```

**Important:** 
- Replace `/path/to/EASACompliance` with the **absolute path** of your project
- Use **absolute paths** for `run_mcp_server.py` and `easa_complete.db`
- See `examples/README.md` for more details

---

## 🔄 Step 4: Restart Cursor

1. **Completely close Cursor** (not just the window)
2. **Relaunch Cursor**
3. The MCP server should start automatically

---

## ✅ Step 5: Verify the Connection

### 5.1 Check in Logs

Open Cursor's console (View → Output) and look for:
```
✅ EASA MCP Server initialized
   Database: easa_complete.db
   Model: all-MiniLM-L12-v2
```

### 5.2 Test with Cursor Chat

In Cursor's chat, try:

```
Can you find me the EASA regulations about flight time 
limitations for crew members?
```

Cursor should automatically use the `search_regulations` tool.

### 5.3 Verify Available Tools

In Cursor, you can verify available MCP tools via:
- **Command Palette** (Ctrl+Shift+P / Cmd+Shift+P)
- Search for "MCP" or "Model Context Protocol"
- See the list of connected servers

---

## 🧪 Step 6: Practical Tests

### Test 1: Simple Search

```
👤 "What are the EASA regulations about crew rest?"

🤖 Cursor should use search_regulations and return:
   - ORO.FTL.210: Flight times and duty periods
   - AMC1 ORO.FTL.110: Operator responsibilities
   - etc.
```

### Test 2: Specific Retrieval

```
👤 "Retrieve regulation ORO.FTL.110"

🤖 Cursor should use get_regulation and return:
   - Complete reference
   - Title and content
   - Metadata
```

### Test 3: Regulatory Chain

```
👤 "Show me ORO.FTL.110 with all its associated AMC and GM"

🤖 Cursor should use get_regulatory_chain and return:
   - Main IR
   - All associated AMC
   - All associated GM
```

### Test 4: Compliance Validation

```
👤 "Validate this text against EASA:
'Pilots must have at least 12 hours of rest between two flights'"

🤖 Cursor should use validate_compliance and return:
   - Compliance score
   - Relevant regulations
   - Identified gaps
   - Recommendations
```

---

## 🐛 Troubleshooting

### Problem: Server doesn't start

**Check:**
```bash
# 1. Test the server in standalone mode
cd /path/to/EASACompliance
export EASA_DB_PATH="easa_complete.db"
timeout 3 python run_mcp_server.py

# Should display:
# ✅ EASA MCP Server initialized
```

**If error:**
- Verify that `uv` is in PATH
- Verify that the database exists
- Verify absolute paths in config

### Problem: Cursor doesn't see the server

**Solutions:**
1. Check the config file (`mcp.json`)
2. Completely restart Cursor
3. Check Cursor logs (View → Output)
4. Verify that the path to `run_mcp_server.py` is absolute

### Problem: "sentence-transformers not found"

**Solution:**
```bash
# Ensure the virtual environment is correct
cd /path/to/EASACompliance
./install.sh  # or: pip install -r requirements.txt
python -c "import sentence_transformers; print('OK')"
```

### Problem: Timeout or connection closed

**Solutions:**
1. Verify that the server starts correctly in standalone mode
2. Increase timeout in Cursor config (if possible)
3. Verify execution permissions:
   ```bash
   chmod +x run_mcp_server.py
   ```

---

## 📊 Configuration Structure

```json
{
  "mcpServers": {
    "easa-regulations": {          // Server name (arbitrary)
      "command": "uv",              // Command to execute
      "args": [                     // Arguments
        "run",
        "python",
        "/absolute/path/run_mcp_server.py"
      ],
      "env": {                      // Environment variables
        "EASA_DB_PATH": "/absolute/path/easa_complete.db",
        "EASA_MODEL": "all-MiniLM-L12-v2"
      }
    }
  }
}
```

---

## 🎯 Useful Commands

### Launch the server manually (for debugging)

```bash
cd /path/to/EASACompliance
export EASA_DB_PATH="easa_complete.db"
python run_mcp_server.py
```

### Test with Python client

```bash
cd /path/to/EASACompliance
python examples/mcp_client_test.py
```

### Automatic configuration (recommended)

```bash
cd /path/to/EASACompliance
python scripts/setup_cursor_mcp.py
```

This script automatically detects paths and configures Cursor for you.

### Check Cursor logs

1. Open **View → Output**
2. Select "MCP" or "Model Context Protocol"
3. See server messages

---

## 📚 Resources

- **Complete guide**: `docs/MCP_SERVER_GUIDE.md`
- **Test client**: `examples/mcp_client_test.py`
- **Config examples**: `examples/README.md` (templates for Cursor and Claude Desktop)
- **Automatic setup script**: `scripts/setup_cursor_mcp.py`
- **MCP documentation**: https://modelcontextprotocol.io

---

## ✅ Verification Checklist

- [ ] Database `easa_complete.db` exists
- [ ] Dependencies installed (`uv sync`)
- [ ] Server tested in standalone mode (works)
- [ ] `mcp.json` file created with correct config
- [ ] Absolute paths used in config
- [ ] Cursor completely restarted
- [ ] Server visible in Cursor logs
- [ ] Search test works in Cursor Chat

---

**Version**: 1.0.0  
**Date**: 2025-11-17  
**Status**: ✅ Tested and functional
