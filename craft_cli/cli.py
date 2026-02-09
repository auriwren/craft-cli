"""Click CLI entry point for craft-cli."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from .client import CraftClient
from .config import DEFAULT_FOLDER_ID
from .utils import (block_tree, console, doc_table, error, folder_tree,
                    output_json, task_table)


def get_client() -> CraftClient:
    try:
        return CraftClient()
    except RuntimeError as e:
        error(str(e))


@click.group()
@click.option("--json-output", "use_json", is_flag=True, help="Output as JSON")
@click.pass_context
def cli(ctx, use_json):
    """Craft.do document management CLI."""
    ctx.ensure_object(dict)
    ctx.obj["json"] = use_json


# ── Documents ──────────────────────────────────────────────────────

@cli.group("doc")
def doc_group():
    """Document management commands."""


@doc_group.command("list")
@click.option("--folder", "folder_id", help="Filter by folder ID")
@click.option("--location", type=click.Choice(["unsorted", "trash", "templates", "daily_notes"]))
@click.option("--metadata", is_flag=True, help="Include metadata")
@click.pass_context
def doc_list(ctx, folder_id, location, metadata):
    """List documents."""
    client = get_client()
    result = client.list_documents(folder_id=folder_id, location=location,
                                    fetch_metadata=metadata)
    items = result.get("items", [])
    if ctx.obj.get("json"):
        output_json(result)
    else:
        doc_table(items, show_metadata=metadata)


@doc_group.command("create")
@click.argument("title")
@click.option("--folder", "folder_id", default=DEFAULT_FOLDER_ID,
              help="Folder ID (default: Auri folder)")
@click.option("--content", help="Markdown content (string or @filepath)")
@click.pass_context
def doc_create(ctx, title, folder_id, content):
    """Create a document and optionally populate with content."""
    client = get_client()
    result = client.create_document(title, folder_id=folder_id)
    items = result.get("items", [])
    if not items:
        error("No document created")
    doc = items[0]
    doc_id = doc["id"]  # CORRECT ID for block operations

    if content:
        # Support @filepath
        if content.startswith("@"):
            p = Path(content[1:])
            if not p.exists():
                error(f"File not found: {p}")
            content = p.read_text()
        client.add_blocks(doc_id, content)

    if ctx.obj.get("json"):
        output_json(result)
    else:
        console.print(f"[green]Created:[/] {doc.get('title', title)}")
        console.print(f"[cyan]ID:[/] {doc_id}")
        link = doc.get("clickableLink", "")
        if link:
            console.print(f"[dim]Link:[/] {link}")


@doc_group.command("read")
@click.argument("doc_id")
@click.option("--format", "fmt", type=click.Choice(["json", "markdown"]), default="json")
@click.pass_context
def doc_read(ctx, doc_id, fmt):
    """Read a document's content."""
    client = get_client()
    if fmt == "markdown":
        text = client.get_blocks(doc_id, accept_markdown=True)
        print(text)
    else:
        result = client.get_blocks(doc_id)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            block_tree(result)


@doc_group.command("delete")
@click.argument("doc_id")
@click.pass_context
def doc_delete(ctx, doc_id):
    """Delete a document (move to trash)."""
    client = get_client()
    result = client.delete_documents([doc_id])
    if ctx.obj.get("json"):
        output_json(result)
    else:
        console.print(f"[yellow]Deleted:[/] {doc_id}")


@doc_group.command("move")
@click.argument("doc_id")
@click.option("--to-folder", required=True, help="Destination folder ID")
@click.pass_context
def doc_move(ctx, doc_id, to_folder):
    """Move a document to a folder."""
    client = get_client()
    result = client.move_documents([doc_id], folder_id=to_folder)
    if ctx.obj.get("json"):
        output_json(result)
    else:
        console.print(f"[green]Moved:[/] {doc_id} -> {to_folder}")


@doc_group.command("search")
@click.argument("query")
@click.pass_context
def doc_search(ctx, query):
    """Search documents across the space."""
    client = get_client()
    result = client.search_documents(query)
    items = result.get("items", [])
    if ctx.obj.get("json"):
        output_json(result)
    else:
        for item in items:
            console.print(f"[cyan]{item.get('documentId', '')}[/] {item.get('markdown', '')[:120]}")
        if not items:
            console.print("[dim]No results.[/]")


# ── Blocks ─────────────────────────────────────────────────────────

@cli.group("block")
def block_group():
    """Block content management commands."""


@block_group.command("list")
@click.argument("doc_id")
@click.pass_context
def block_list(ctx, doc_id):
    """List blocks in a document."""
    client = get_client()
    result = client.get_blocks(doc_id)
    if ctx.obj.get("json"):
        output_json(result)
    else:
        block_tree(result)


@block_group.command("add")
@click.argument("doc_id")
@click.option("--markdown", "-m", required=True, help="Markdown text or @filepath")
@click.option("--position", type=click.Choice(["start", "end"]), default="end")
@click.pass_context
def block_add(ctx, doc_id, markdown, position):
    """Add blocks to a document."""
    if markdown.startswith("@"):
        p = Path(markdown[1:])
        if not p.exists():
            error(f"File not found: {p}")
        markdown = p.read_text()
    client = get_client()
    result = client.add_blocks(doc_id, markdown, position=position)
    if ctx.obj.get("json"):
        output_json(result)
    else:
        items = result.get("items", [])
        console.print(f"[green]Added {len(items)} block(s)[/]")
        for item in items:
            console.print(f"  [cyan]{item.get('id', '')}[/] {item.get('markdown', '')[:80]}")


@block_group.command("delete")
@click.argument("block_ids", nargs=-1, required=True)
@click.pass_context
def block_delete(ctx, block_ids):
    """Delete blocks by ID."""
    client = get_client()
    result = client.delete_blocks(list(block_ids))
    if ctx.obj.get("json"):
        output_json(result)
    else:
        console.print(f"[yellow]Deleted {len(block_ids)} block(s)[/]")


@block_group.command("update")
@click.argument("block_id")
@click.option("--markdown", "-m", required=True, help="New markdown content")
@click.pass_context
def block_update(ctx, block_id, markdown):
    """Update a block's content."""
    client = get_client()
    result = client.update_blocks([{"id": block_id, "markdown": markdown}])
    if ctx.obj.get("json"):
        output_json(result)
    else:
        console.print(f"[green]Updated:[/] {block_id}")


@block_group.command("move")
@click.argument("block_id")
@click.option("--to-doc", required=True, help="Destination document ID")
@click.option("--position", type=click.Choice(["start", "end"]), default="end")
@click.pass_context
def block_move(ctx, block_id, to_doc, position):
    """Move a block to another document."""
    client = get_client()
    result = client.move_blocks([block_id], to_doc, position=position)
    if ctx.obj.get("json"):
        output_json(result)
    else:
        console.print(f"[green]Moved:[/] {block_id} -> {to_doc}")


@block_group.command("search")
@click.argument("doc_id")
@click.argument("pattern")
@click.pass_context
def block_search(ctx, doc_id, pattern):
    """Search within a document."""
    client = get_client()
    result = client.search_blocks(doc_id, pattern)
    items = result.get("items", [])
    if ctx.obj.get("json"):
        output_json(result)
    else:
        for item in items:
            console.print(f"[cyan]{item.get('blockId', '')}[/] {item.get('markdown', '')[:120]}")
        if not items:
            console.print("[dim]No matches.[/]")


# ── Folders ────────────────────────────────────────────────────────

@cli.group("folder")
def folder_group():
    """Folder management commands."""


@folder_group.command("list")
@click.pass_context
def folder_list(ctx):
    """List all folders."""
    client = get_client()
    result = client.list_folders()
    items = result.get("items", [])
    if ctx.obj.get("json"):
        output_json(result)
    else:
        folder_tree(items)


@folder_group.command("create")
@click.argument("name")
@click.option("--parent", help="Parent folder ID")
@click.pass_context
def folder_create(ctx, name, parent):
    """Create a folder."""
    client = get_client()
    result = client.create_folder(name, parent_id=parent)
    if ctx.obj.get("json"):
        output_json(result)
    else:
        items = result.get("items", [])
        if items:
            console.print(f"[green]Created:[/] {items[0].get('name', name)} [cyan]{items[0].get('id', '')}[/]")


@folder_group.command("delete")
@click.argument("folder_id")
@click.pass_context
def folder_delete(ctx, folder_id):
    """Delete a folder."""
    client = get_client()
    result = client.delete_folders([folder_id])
    if ctx.obj.get("json"):
        output_json(result)
    else:
        console.print(f"[yellow]Deleted:[/] {folder_id}")


@folder_group.command("move")
@click.argument("folder_id")
@click.option("--parent", help="Parent folder ID (omit for root)")
@click.pass_context
def folder_move(ctx, folder_id, parent):
    """Move a folder."""
    client = get_client()
    result = client.move_folders([folder_id], parent_id=parent)
    if ctx.obj.get("json"):
        output_json(result)
    else:
        dest = parent or "root"
        console.print(f"[green]Moved:[/] {folder_id} -> {dest}")


# ── Tasks ──────────────────────────────────────────────────────────

@cli.group("task")
def task_group():
    """Task management commands."""


@task_group.command("list")
@click.option("--scope", required=True,
              type=click.Choice(["inbox", "active", "upcoming", "logbook", "document"]))
@click.option("--doc", "document_id", help="Document ID (required for scope=document)")
@click.pass_context
def task_list(ctx, scope, document_id):
    """List tasks by scope."""
    client = get_client()
    result = client.list_tasks(scope, document_id=document_id)
    items = result.get("items", [])
    if ctx.obj.get("json"):
        output_json(result)
    else:
        task_table(items)


@task_group.command("add")
@click.argument("text")
@click.option("--schedule", help="Schedule date")
@click.option("--deadline", help="Deadline date")
@click.option("--location", "loc_type", default="inbox",
              type=click.Choice(["inbox", "daily", "document"]))
@click.option("--doc", "document_id", help="Document ID (for location=document)")
@click.option("--date", help="Date for daily note location")
@click.pass_context
def task_add(ctx, text, schedule, deadline, loc_type, document_id, date):
    """Add a task."""
    client = get_client()
    lt = "dailyNote" if loc_type == "daily" else loc_type
    result = client.add_task(text, location_type=lt, date=date,
                             document_id=document_id,
                             schedule_date=schedule, deadline_date=deadline)
    if ctx.obj.get("json"):
        output_json(result)
    else:
        items = result.get("items", [])
        if items:
            console.print(f"[green]Created task:[/] {items[0].get('id', '')}")


@task_group.command("update")
@click.argument("task_id")
@click.option("--state", type=click.Choice(["todo", "done", "canceled"]))
@click.option("--schedule", help="Schedule date")
@click.option("--deadline", help="Deadline date")
@click.pass_context
def task_update(ctx, task_id, state, schedule, deadline):
    """Update a task."""
    client = get_client()
    result = client.update_task(task_id, state=state,
                                schedule_date=schedule, deadline_date=deadline)
    if ctx.obj.get("json"):
        output_json(result)
    else:
        console.print(f"[green]Updated:[/] {task_id}")


@task_group.command("delete")
@click.argument("task_id")
@click.pass_context
def task_delete(ctx, task_id):
    """Delete a task."""
    client = get_client()
    result = client.delete_tasks([task_id])
    if ctx.obj.get("json"):
        output_json(result)
    else:
        console.print(f"[yellow]Deleted:[/] {task_id}")


# ── Collections ────────────────────────────────────────────────────

@cli.group("collection")
def collection_group():
    """Collection management commands."""


@collection_group.command("list")
@click.option("--doc", "doc_id", help="Filter by document ID")
@click.pass_context
def collection_list(ctx, doc_id):
    """List collections."""
    client = get_client()
    doc_ids = [doc_id] if doc_id else None
    result = client.list_collections(document_ids=doc_ids)
    items = result.get("items", [])
    if ctx.obj.get("json"):
        output_json(result)
    else:
        from rich.table import Table
        t = Table(title="Collections")
        t.add_column("ID", style="cyan")
        t.add_column("Name", style="green")
        t.add_column("Items", style="yellow")
        t.add_column("Document", style="dim")
        for item in items:
            t.add_row(item.get("id", ""), item.get("name", ""),
                      str(item.get("itemCount", 0)), item.get("documentId", ""))
        console.print(t)


@collection_group.command("schema")
@click.argument("collection_id")
@click.pass_context
def collection_schema(ctx, collection_id):
    """Get collection schema."""
    client = get_client()
    result = client.get_collection_schema(collection_id)
    output_json(result)


@collection_group.command("items")
@click.argument("collection_id")
@click.pass_context
def collection_items(ctx, collection_id):
    """List collection items."""
    client = get_client()
    result = client.get_collection_items(collection_id)
    if ctx.obj.get("json"):
        output_json(result)
    else:
        items = result.get("items", [])
        for item in items:
            props = item.get("properties", {})
            props_str = " | ".join(f"{k}={v}" for k, v in props.items()) if props else ""
            console.print(f"[cyan]{item.get('id', '')}[/] {item.get('title', '')} [dim]{props_str}[/]")


@collection_group.command("add-item")
@click.argument("collection_id")
@click.option("--title", required=True)
@click.option("--props", multiple=True, help="KEY=VALUE properties")
@click.pass_context
def collection_add_item(ctx, collection_id, title, props):
    """Add an item to a collection."""
    client = get_client()
    item: dict = {"title": title}
    if props:
        item["properties"] = {}
        for p in props:
            k, v = p.split("=", 1)
            item["properties"][k] = v
    result = client.add_collection_items(collection_id, [item])
    if ctx.obj.get("json"):
        output_json(result)
    else:
        items = result.get("items", [])
        if items:
            console.print(f"[green]Added:[/] {items[0].get('id', '')}")


@collection_group.command("update-item")
@click.argument("collection_id")
@click.argument("item_id")
@click.option("--props", multiple=True, help="KEY=VALUE properties")
@click.pass_context
def collection_update_item(ctx, collection_id, item_id, props):
    """Update a collection item."""
    client = get_client()
    update: dict = {"id": item_id}
    if props:
        update["properties"] = {}
        for p in props:
            k, v = p.split("=", 1)
            update["properties"][k] = v
    result = client.update_collection_items(collection_id, [update])
    if ctx.obj.get("json"):
        output_json(result)
    else:
        console.print(f"[green]Updated:[/] {item_id}")


@collection_group.command("delete-item")
@click.argument("collection_id")
@click.argument("item_id")
@click.pass_context
def collection_delete_item(ctx, collection_id, item_id):
    """Delete a collection item."""
    client = get_client()
    result = client.delete_collection_items(collection_id, [item_id])
    if ctx.obj.get("json"):
        output_json(result)
    else:
        console.print(f"[yellow]Deleted:[/] {item_id}")


# ── Utility ────────────────────────────────────────────────────────

@cli.command("connection")
@click.pass_context
def connection_cmd(ctx):
    """Show space connection info."""
    client = get_client()
    result = client.get_connection()
    output_json(result)


@cli.command("daily")
@click.option("--date", default="today", help="Date (YYYY-MM-DD, today, yesterday, tomorrow)")
@click.option("--format", "fmt", type=click.Choice(["json", "markdown"]), default="json")
@click.pass_context
def daily_cmd(ctx, date, fmt):
    """Read the daily note."""
    client = get_client()
    if fmt == "markdown":
        result = client._request("GET", "/blocks", params={"date": date},
                                 headers={"Accept": "text/markdown"})
        print(result)
    else:
        result = client.get_daily_note(date)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            block_tree(result)


@cli.command("upload")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--to-doc", required=True, help="Document ID")
@click.option("--position", type=click.Choice(["start", "end"]), default="end")
@click.pass_context
def upload_cmd(ctx, file_path, to_doc, position):
    """Upload a file to a document."""
    client = get_client()
    result = client.upload_file(file_path, to_doc, position)
    output_json(result)


if __name__ == "__main__":
    cli()
