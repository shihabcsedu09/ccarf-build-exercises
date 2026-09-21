"""2.4 Configure MCP servers with scoping and variables.

The committed file is the team's. The home file is yours. The token
comes from the shell, never from a file in the repository.

Run it:  python ex_2_4_mcp_config.py
"""
import json, os, re

# ---------------------------------------------------------------- START HERE
PROJECT_MCP_JSON = {          # .mcp.json, committed, shared with the team
    "mcpServers": {
        "postgres": {"command": "npx", "args": ["-y", "@company/postgres-mcp"],
                     "env": {"DATABASE_URL": "${DATABASE_URL}"}},
        "github":   {"command": "npx", "args": ["-y", "@mcp/server-github"],
                     "env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"}},
    }
}

USER_CLAUDE_JSON = {          # ~/.claude.json, yours alone, for experiments
    "mcpServers": {
        "figma-trial": {"command": "npx", "args": ["-y", "figma-mcp"],
                        "env": {"FIGMA_TOKEN": "${FIGMA_TOKEN}"}},
    }
}


def expand(config, environ):
    """Claude Code reads ${VAR} from the shell it was started in.
    A .env file inside the repository is not read."""
    out, missing = json.dumps(config), []

    def sub(m):
        name = m.group(1)
        if name not in environ:
            missing.append(name)
            return ""
        return environ[name]

    resolved = re.sub(r"\$\{([A-Z_]+)\}", sub, out)
    return json.loads(resolved), missing


def audit(config):
    """A literal secret in a committed file is the failure this prevents."""
    text = json.dumps(config)
    literals = re.findall(r'"(gh[pous]_[A-Za-z0-9]+|postgres://[^"]+)"', text)
    return literals


if __name__ == "__main__":
    shell = {"DATABASE_URL": "postgres://localhost/app", "GITHUB_TOKEN": "gho_xxx"}
    resolved, missing = expand(PROJECT_MCP_JSON, shell)
    print("with both variables set  -> missing:", missing or "none")

    _, missing = expand(PROJECT_MCP_JSON, {"DATABASE_URL": "postgres://localhost/app"})
    print("teammate without the token -> missing:", missing)
    print("   this is why /mcp shows no GitHub tools on their machine")

    leaked = dict(PROJECT_MCP_JSON)
    leaked["mcpServers"]["github"]["env"]["GITHUB_TOKEN"] = "gho_realsecret123"
    print("\naudit of a committed file with a literal token:", audit(leaked))
