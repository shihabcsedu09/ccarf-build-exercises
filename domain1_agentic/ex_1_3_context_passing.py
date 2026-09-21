"""1.3 Pass context with structured metadata.

A subagent starts empty. Whatever it must know goes in its prompt,
with the source attached to every finding.

Run it:  python ex_1_3_context_passing.py
"""

COORDINATOR_TOOLS = ["Task", "Read", "Grep"]     # no Task means nothing is delegated


# ---------------------------------------------------------------- START HERE
def finding(claim, url, document, published, excerpt):
    """Content and attribution stay in separate fields, so a paraphrase
    downstream cannot silently drop the source."""
    return {"claim": claim, "source_url": url, "document": document,
            "published": published, "excerpt": excerpt}


def writer_prompt(topic, findings):
    """Build the prompt the writer subagent receives. It has seen nothing else."""
    lines = [f"Topic: {topic}", "", "Findings you may use, and nothing else:"]
    for i, f in enumerate(findings, 1):
        lines.append(f"[{i}] {f['claim']}")
        lines.append(f"    source: {f['document']} <{f['source_url']}>, {f['published']}")
        lines.append(f"    excerpt: \"{f['excerpt']}\"")
    lines += ["", "Cite every claim as [n]. If a finding is missing, say so."]
    return "\n".join(lines)


def can_delegate(tools):
    return "Task" in tools


if __name__ == "__main__":
    findings = [
        finding("Solar capacity grew 38%", "https://iea.org/r1",
                "IEA Renewables 2025", "2025-11-02", "capacity grew 38% year on year"),
        finding("Wind additions slowed", "https://gwec.net/r2",
                "GWEC Global Wind 2025", "2025-09-14", "additions slowed to 4%"),
    ]
    print(writer_prompt("renewable energy", findings))
    print("\n--- what happens without Task in the coordinator's tools ---")
    for tools in (COORDINATOR_TOOLS, ["Read", "Grep"]):
        print(f"tools={tools} -> delegation possible: {can_delegate(tools)}")
