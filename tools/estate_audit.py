#!/usr/bin/env python3
"""Read-only GitHub estate inventory and cross-repository tree comparison.

Requires: Python 3.10+, GitHub CLI ('gh auth login').
No local repositories are cloned or modified. No GitHub writes are performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


def gh_json(endpoint: str, *, paginate: bool = False):
    cmd = ["gh", "api", endpoint]
    if paginate:
        cmd.append("--paginate")
        cmd.extend(["--slurp"])
    result = subprocess.run(
        cmd, capture_output=True, text=True, check=True, encoding="utf-8"
    )
    value = json.loads(result.stdout)
    if paginate:
        return [item for page in value for item in page]
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", default="TheRealDataBoss")
    parser.add_argument("--output", default="github-estate-audit.json")
    args = parser.parse_args()

    repos = gh_json(
        f"users/{args.owner}/repos?per_page=100&type=owner",
        paginate=True,
    )
    # The user endpoint may exclude private repos; supplement with the
    # authenticated viewer's own repos, deduplicating by full_name.
    viewer_repos = gh_json(
        "user/repos?per_page=100&affiliation=owner", paginate=True
    )
    by_name = {
        item["full_name"]: item
        for item in [*repos, *viewer_repos]
        if item["owner"]["login"].lower() == args.owner.lower()
    }
    records = []
    failures = []
    for name, repo in sorted(by_name.items()):
        branches = []
        try:
            branches = gh_json(
                f"repos/{name}/branches?per_page=100", paginate=True
            )
        except (subprocess.CalledProcessError, ValueError) as exc:
            failures.append({"repository": name, "stage": "branches",
                             "error": str(exc)})
        branch_records = []
        for branch in branches:
            branch_name = branch["name"]
            sha = branch["commit"]["sha"]
            try:
                commit = gh_json(f"repos/{name}/git/commits/{sha}")
                tree_sha = commit["tree"]["sha"]
                tree = gh_json(f"repos/{name}/git/trees/{tree_sha}?recursive=1")
                entries = tree.get("tree", [])
                truncated = bool(tree.get("truncated"))
                files = {
                    item["path"]: {
                        "sha": item["sha"],
                        "mode": item["mode"],
                        "type": item["type"],
                        "size": item.get("size"),
                    }
                    for item in entries
                    if item["type"] in ("blob", "commit")
                }
                canonical = json.dumps(
                    files, sort_keys=True, separators=(",", ":")
                ).encode("utf-8")
                branch_records.append({
                    "name": branch_name,
                    "head": sha,
                    "tree_sha": tree_sha,
                    "tree_truncated": truncated,
                    "entries": len(entries),
                    "files": files if not truncated else None,
                    "manifest_sha256": (
                        hashlib.sha256(canonical).hexdigest()
                        if not truncated else None
                    ),
                })
            except (subprocess.CalledProcessError, ValueError, KeyError) as exc:
                failures.append({"repository": name, "branch": branch_name,
                                 "stage": "tree", "error": str(exc)})
        records.append({
            "repository": name,
            "private": repo["private"],
            "archived": repo["archived"],
            "default_branch": repo["default_branch"],
            "size_kb": repo.get("size"),
            "branches": branch_records,
        })

    matches = defaultdict(list)
    for repo in records:
        for branch in repo["branches"]:
            if branch["tree_sha"] and not branch["tree_truncated"]:
                matches[branch["tree_sha"]].append(
                    f'{repo["repository"]}@{branch["name"]}'
                )
    exact_tree_groups = [
        {"tree_sha": sha, "references": refs}
        for sha, refs in sorted(matches.items())
        if len(refs) > 1
    ]
    report = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "owner": args.owner,
        "repository_count": len(records),
        "method": "GitHub Git Trees API; exact tree SHA equality",
        "limitations": [
            "Same tree SHA proves identical tracked file trees, not identical history.",
            "Different tree SHAs require file-by-file comparison.",
            "GitHub tree API may truncate very large trees; truncated results are excluded.",
            "Uncommitted local files and Git LFS object contents are not covered.",
            "GitHub Actions, secrets, releases, tags and protection rules require separate audit.",
        ],
        "exact_tree_groups": exact_tree_groups,
        "failures": failures,
        "repositories": records,
    }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        f"Saved {len(records)} repositories, "
        f"{len(exact_tree_groups)} exact-tree groups, "
        f"{len(failures)} inspection failures to {target}"
    )


if __name__ == "__main__":
    main()
