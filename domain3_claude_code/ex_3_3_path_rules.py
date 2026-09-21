"""3.3 Configure path-specific rules with globs.

A rule file under .claude/rules/ with a paths glob loads only when
Claude touches a matching file, wherever that file lives.

Run it:  python ex_3_3_path_rules.py
"""
import fnmatch

# ---------------------------------------------------------------- START HERE
RULES = {
    ".claude/rules/testing.md":   ["**/*.test.ts", "**/*.test.tsx", "**/*.spec.ts"],
    ".claude/rules/terraform.md": ["infra/**/*.tf", "modules/**/*.tf"],
}
ROOT_CLAUDE_MD = "./CLAUDE.md"      # always loaded, whatever you are editing


def rules_for(path):
    """Which rule files load when Claude opens this file."""
    hits = [ROOT_CLAUDE_MD]
    for rule_file, globs in RULES.items():
        if any(fnmatch.fnmatch(path, g) for g in globs):
            hits.append(rule_file)
    return hits


def cost_of_root_only(files, lines_of_terraform_rules=300):
    """What putting the Terraform rules in the root file would cost."""
    return len(files) * lines_of_terraform_rules


if __name__ == "__main__":
    files = ["src/ui/Button.tsx", "src/ui/Button.test.tsx",
             "packages/admin/widgets/Chart.test.tsx",
             "infra/prod/main.tf", "modules/vpc/main.tf", "src/api/handler.ts"]
    for f in files:
        print(f"{f:38} -> {', '.join(rules_for(f))}")

    print(f"\nOne rule file covers every matching path, including directories")
    print(f"that do not exist yet. In the root file instead, those 300 lines")
    print(f"would load for all {len(files)} files "
          f"({cost_of_root_only(files)} lines of irrelevant context).")
