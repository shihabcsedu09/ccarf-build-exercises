"""2.4 Configure MCP servers: scope, secrets, resources.

Real scenario: six developers need the same GitHub server, each with their own
token, and nothing secret may reach the repository.

Where you write the config decides who gets it. What you write decides whether
a token ends up in git history. And a server offers more than tools: publish a
catalogue as a resource and agents stop spending calls discovering what exists.

This writes real config files into a temp folder so you can read them.

Run it:
    python ex_2_4_mcp_config.py
"""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from claude_helpers import banner


# ---------------------------------------------------------------- START HERE
# Project scope. Committed, shared with the team, and holds no secret: the
# ${VAR} is expanded from each developer's own environment when Claude starts.
PROJECT_MCP_JSON = {
    "mcpServers": {
        "github": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"},
        },
        "postgres": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-postgres"],
            "env": {"DATABASE_URL": "${DATABASE_URL}"},
        },
    }
}

# User scope. One person's experiment, in their home directory, so nobody else
# gets a failing server at startup.
USER_MCP_JSON = {
    "mcpServers": {
        "figma": {"command": "npx", "args": ["-y", "figma-mcp"],
                  "env": {"FIGMA_TOKEN": "${FIGMA_TOKEN}"}}
    }
}

# Headless runs cannot click the one-time approval prompt, so say yes in the
# committed settings instead.
PROJECT_SETTINGS = {"enableAllProjectMcpServers": True}


def write_config(root):
    """Write the real files, in the real places Claude Code looks."""
    (root / ".mcp.json").write_text(json.dumps(PROJECT_MCP_JSON, indent=2))
    (root / ".claude").mkdir(exist_ok=True)
    (root / ".claude" / "settings.json").write_text(json.dumps(PROJECT_SETTINGS, indent=2))
    home = root / "home" / ".claude"
    home.mkdir(parents=True, exist_ok=True)
    (home / ".claude.json").write_text(json.dumps(USER_MCP_JSON, indent=2))
    return root


def expand(config, environment):
    """What Claude Code does with ${VAR} at startup, so you can see the result."""
    out = json.loads(json.dumps(config))
    for server in out["mcpServers"].values():
        for key, value in list(server.get("env", {}).items()):
            if value.startswith("${") and value.endswith("}"):
                server["env"][key] = environment.get(value[2:-1], "<<UNSET>>")
    return out


def secrets_in(text):
    """A crude check of the kind worth running in CI: does the tracked file
    contain something that looks like a real token?"""
    return [line.strip() for line in text.splitlines()
            if ("ghp_" in line or "sk-" in line or "postgres://" in line)]


# Tools are actions. Resources are content the client can read without spending
# a tool call, which is the fix for agents that probe to find out what exists.
RESOURCES = [
    {"uri": "catalog://tables", "name": "Database tables",
     "description": "Every table with its columns. Read this instead of probing."},
    {"uri": "catalog://policies", "name": "Refund policies",
     "description": "The 14 policy documents, by name."},
]

if __name__ == "__main__":
    banner("2.4 MCP scope, secrets and resources", api=False)
    root = pathlib.Path(tempfile.mkdtemp())
    write_config(root)

    print("files written:")
    for p in sorted(root.rglob("*")):
        if p.is_file():
            print("   ", p.relative_to(root))
    print()

    print("committed .mcp.json, as it sits in git:")
    print("   ", json.dumps(PROJECT_MCP_JSON["mcpServers"]["github"]["env"]))
    print("   token in the tracked file?", secrets_in((root / ".mcp.json").read_text()) or "none")
    print()

    print("same file after each developer's shell is read:")
    ana = expand(PROJECT_MCP_JSON, {"GITHUB_TOKEN": "ghp_anaOwnToken", "DATABASE_URL": "postgres://ana@localhost/app"})
    sam = expand(PROJECT_MCP_JSON, {"GITHUB_TOKEN": "ghp_samOwnToken", "DATABASE_URL": "postgres://sam@localhost/app"})
    print("   ana ->", ana["mcpServers"]["github"]["env"])
    print("   sam ->", sam["mcpServers"]["github"]["env"])
    missing = expand(PROJECT_MCP_JSON, {})
    print("   nobody exported it ->", missing["mcpServers"]["github"]["env"],
          "  (the server fails to start, which is the visible failure you want)")
    print()

    print("scope decides who gets a server:")
    print("   .mcp.json in the repo        the whole team, travels with git")
    print("   ~/.claude.json               only you, on this machine")
    print("   --mcp-config ci.json --strict-mcp-config   only what CI needs, nothing else")
    print()

    print("resources, so agents stop probing to find out what exists:")
    for r in RESOURCES:
        print("   %-22s %s" % (r["uri"], r["description"]))
    print()

    claude = shutil.which("claude")
    print("verify a server is actually connected:")
    print("   claude mcp list        ", "(claude found at %s)" % claude if claude
          else "(install Claude Code to run this)")
    if claude:
        out = subprocess.run([claude, "mcp", "list"], capture_output=True, text=True,
                             timeout=60, cwd=str(root))
        first = (out.stdout or out.stderr).strip().splitlines()[:3]
        for line in first:
            print("     ", line)
    shutil.rmtree(root, ignore_errors=True)
