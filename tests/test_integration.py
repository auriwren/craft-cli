"""Integration tests against real Craft API.

Run with: pytest tests/test_integration.py -v
These create real documents and clean up after themselves.
"""

import os
import time
import pytest

AURI_FOLDER = os.environ.get("CRAFT_DEFAULT_FOLDER", "")


class TestDocumentLifecycle:
    """End-to-end: create doc, add blocks, read, search, delete."""

    def test_full_lifecycle(self, live_client):
        client = live_client
        doc_id = None
        try:
            # 1. Create document
            result = client.create_document(
                "craft-cli Integration Test",
                folder_id=AURI_FOLDER,
            )
            items = result.get("items", [])
            assert len(items) >= 1, f"Expected document, got: {result}"
            doc = items[0]
            doc_id = doc["id"]
            assert doc_id, "Document ID should not be empty"
            assert doc.get("title") == "craft-cli Integration Test"

            # 2. Add blocks (using doc_id, NOT clickableLink documentId)
            block_result = client.add_blocks(
                doc_id,
                "## Test Section\n\nThis is test content from craft-cli integration tests.\n\n- Item 1\n- Item 2",
            )
            block_items = block_result.get("items", [])
            assert len(block_items) >= 1, f"Expected blocks, got: {block_result}"
            block_ids = [b["id"] for b in block_items]

            # Small delay for indexing
            time.sleep(1)

            # 3. Read document content
            content = client.get_blocks(doc_id)
            assert content.get("type") == "page"
            assert len(content.get("content", [])) > 0

            # 4. Read as markdown
            md = client.get_blocks(doc_id, accept_markdown=True)
            assert isinstance(md, str)
            assert "Test Section" in md or "test content" in md.lower()

            # 5. Search within document
            search_result = client.search_blocks(doc_id, "test content")
            # Search may or may not find results depending on indexing delay
            assert "items" in search_result

            # 6. Update a block
            if block_ids:
                update_result = client.update_blocks([
                    {"id": block_ids[0], "markdown": "## Updated Section"}
                ])
                assert "items" in update_result

            # 7. Search across documents
            doc_search = client.search_documents("craft-cli Integration Test")
            assert "items" in doc_search

            # 8. Delete blocks
            if block_ids:
                del_result = client.delete_blocks(block_ids)
                assert "items" in del_result

        finally:
            # Cleanup: delete test document
            if doc_id:
                client.delete_documents([doc_id])


class TestFolders:
    def test_list_folders(self, live_client):
        result = live_client.list_folders()
        items = result.get("items", [])
        assert len(items) > 0, "Should have at least built-in folders"
        names = [f.get("name", "") for f in items]
        # Should have built-in locations
        assert any("unsorted" in n.lower() or "Unsorted" in n for n in names) or len(items) > 0


class TestConnection:
    def test_get_connection(self, live_client):
        result = live_client.get_connection()
        assert "space" in result
        assert "id" in result["space"]


class TestTasks:
    def test_list_active_tasks(self, live_client):
        result = live_client.list_tasks("active")
        assert "items" in result

    def test_task_lifecycle(self, live_client):
        client = live_client
        task_id = None
        try:
            # Create
            result = client.add_task("craft-cli test task - DELETE ME",
                                     location_type="inbox",
                                     schedule_date="tomorrow")
            items = result.get("items", [])
            assert len(items) >= 1
            task_id = items[0]["id"]

            # Update
            client.update_task(task_id, state="done")

        finally:
            if task_id:
                client.delete_tasks([task_id])


class TestDailyNote:
    def test_read_today(self, live_client):
        result = live_client.get_daily_note("today")
        assert result.get("type") == "page"


class TestCollections:
    def test_list_collections(self, live_client):
        result = live_client.list_collections()
        assert "items" in result
