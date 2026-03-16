# MCP Server Configuration

This directory contains MCP (Model Context Protocol) server configurations for the Agentic Trader Platform.

## What is MCP?

The Model Context Protocol (MCP) is an open standard for connecting AI assistants with external tools and data sources. It allows AI agents to:

- Query code graphs and relationships
- Access external APIs securely
- Execute specialized tools
- Maintain context across sessions

## Configuration Files

| File | Purpose |
|------|---------|
| `config.json` | Main MCP server configuration |

## Available MCP Servers

### CodeGraphContext

Provides code graph analysis capabilities for token-efficient AI interactions.

**Tools:**
- `get_call_graph` - Get call graph for a specific function
- `get_symbol_context` - Get context around a symbol (function, class, variable)
- `query_graph` - Query the code graph with custom criteria

**Setup:**

1. Install CodeGraphContext:
   ```bash
   pip install codegraphcontext
   ```

2. Start the server:
   ```bash
   codegraphcontext-mcp --port 8000
   ```

3. The configuration is already in `.mcp/config.json`

## Integration with IDE

### VS Code / Cursor

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "codegraphcontext": {
      "command": "codegraphcontext-mcp",
      "args": ["--port", "8000"]
    }
  }
}
```

### Antigravity IDE

1. Open MCP Servers → Manage MCP Servers
2. Click "View raw config"
3. Paste the content from `.mcp/config.json`
4. Save and refresh

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CODEGRAPH_ROOT` | Root directory for code analysis | Workspace root |
| `CODEGRAPH_CACHE` | Cache directory for graph data | `.cache/codegraph` |
| `MCP_LOG_LEVEL` | Logging level | `info` |

## Troubleshooting

### Server Not Starting

Check if the port is available:
```bash
lsof -i :8000
```

### Connection Issues

Verify the server is running:
```bash
curl http://localhost:8000/mcp/config
```

### Tool Not Found

Ensure the server is properly configured in your IDE's MCP settings.

## Security Notes

- Never commit sensitive API keys to this repository
- Use environment variables for secrets
- The `.mcp/` directory is committed to share configurations, but not credentials
