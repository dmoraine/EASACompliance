# MCP Configuration Examples

This directory contains example configuration files for connecting the EASA MCP server to various clients.

## 📋 Files

- **`cursor_mcp_config.json`** - Configuration template for Cursor IDE
- **`claude_desktop_config.json`** - Configuration template for Claude Desktop
- **`mcp_client_test.py`** - Python test client for the MCP server

## 🔧 How to Use

### For Cursor IDE

1. **Locate your Cursor MCP configuration file:**
   - **Linux**: `~/.config/Cursor/User/globalStorage/mcp.json`
   - **macOS**: `~/Library/Application Support/Cursor/User/globalStorage/mcp.json`
   - **Windows**: `%APPDATA%\Cursor\User\globalStorage\mcp.json`

2. **Copy the template:**
   ```bash
   cp examples/cursor_mcp_config.json ~/.config/Cursor/User/globalStorage/mcp.json
   ```

3. **Replace `{PROJECT_ROOT}` with your actual project path:**
   ```bash
   # Example: if your project is at /home/user/projects/EASACompliance
   sed -i 's|{PROJECT_ROOT}|/home/user/projects/EASACompliance|g' ~/.config/Cursor/User/globalStorage/mcp.json
   ```
   
   Or manually edit the file and replace all occurrences of `{PROJECT_ROOT}` with your absolute project path.

4. **Restart Cursor completely**

### For Claude Desktop

1. **Locate your Claude Desktop configuration file:**
   - **Linux**: `~/.config/claude-desktop/claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. **Copy the template:**
   ```bash
   cp examples/claude_desktop_config.json ~/.config/claude-desktop/claude_desktop_config.json
   ```

3. **Replace `{PROJECT_ROOT}` with your actual project path** (same as above)

4. **Restart Claude Desktop**

## 🤖 Automated Setup

Alternatively, use the automated setup script:

```bash
python scripts/setup_cursor_mcp.py
```

This script will:
- Detect your Cursor configuration location
- Generate the correct paths automatically
- Create/update the MCP configuration
- Provide final instructions

## 📝 Notes

- **`{PROJECT_ROOT}`** must be replaced with the **absolute path** to your EASACompliance project directory
- The database file (`easa_complete.db`) must exist before using the MCP server
- Make sure you have built the embeddings database first:
  ```bash
  python build_embeddings.py --xml "your-easa-file.xml" --db easa_complete.db --clear
  ```

## ✅ Verification

After configuration, verify the setup:

1. **Check Cursor/Claude logs** for: `✅ EASA MCP Server initialized`
2. **Test in chat**: "Find EASA regulations about flight time limitations"
3. **Verify tools are available** in the MCP tools list

## 🐛 Troubleshooting

- **Server not starting**: Check that `easa_complete.db` exists
- **Path errors**: Ensure `{PROJECT_ROOT}` is replaced with an absolute path
- **Permission errors**: Make sure the Python script is executable: `chmod +x run_mcp_server.py`

