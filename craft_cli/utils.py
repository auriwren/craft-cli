"""Helpers for CLI output formatting."""

from __future__ import annotations

import json
import sys
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.tree import Tree

console = Console()
err_console = Console(stderr=True)


def output_json(data: Any) -> None:
    print(json.dumps(data, indent=2))


def error(msg: str) -> None:
    err_console.print(f"[bold red]Error:[/] {msg}")
    sys.exit(1)


def doc_table(items: list[dict], show_metadata: bool = False) -> None:
    t = Table(title="Documents")
    t.add_column("ID", style="cyan", no_wrap=True)
    t.add_column("Title", style="green")
    if show_metadata:
        t.add_column("Modified", style="dim")
        t.add_column("Created", style="dim")
    for item in items:
        row = [item.get("id", ""), item.get("title", "")]
        if show_metadata:
            row += [item.get("lastModifiedAt", ""), item.get("createdAt", "")]
        t.add_row(*row)
    console.print(t)


def folder_tree(items: list[dict]) -> None:
    tree = Tree("[bold]Craft Space[/]")
    def _add(parent: Tree, folders: list[dict]):
        for f in folders:
            label = f"[cyan]{f.get('name', '')}[/] ({f.get('documentCount', 0)} docs) [dim]{f.get('id', '')}[/]"
            node = parent.add(label)
            _add(node, f.get("folders", []))
    _add(tree, items)
    console.print(tree)


def block_tree(block: dict, depth: int = 0) -> None:
    indent = "  " * depth
    md = block.get("markdown", "")
    bid = block.get("id", "")
    btype = block.get("type", "")
    console.print(f"{indent}[dim]{bid}[/] [{btype}] {md[:120]}")
    for child in block.get("content", []):
        block_tree(child, depth + 1)


def task_table(items: list[dict]) -> None:
    t = Table(title="Tasks")
    t.add_column("ID", style="cyan", no_wrap=True)
    t.add_column("Task", style="green")
    t.add_column("State", style="yellow")
    t.add_column("Schedule", style="dim")
    t.add_column("Deadline", style="dim")
    for item in items:
        info = item.get("taskInfo", {})
        t.add_row(
            item.get("id", ""),
            item.get("markdown", ""),
            info.get("state", ""),
            info.get("scheduleDate", ""),
            info.get("deadlineDate", ""),
        )
    console.print(t)
