"""Unit tests with mocked HTTP responses."""

import pytest
import responses

BASE = "https://example.com/api/v1"


@responses.activate
def test_list_documents(mock_client):
    responses.add(responses.GET, f"{BASE}/documents",
                  json={"items": [{"id": "d1", "title": "Test"}]})
    result = mock_client.list_documents()
    assert result["items"][0]["id"] == "d1"


@responses.activate
def test_create_document(mock_client):
    responses.add(responses.POST, f"{BASE}/documents",
                  json={"items": [{"id": "new-id", "title": "New Doc",
                                   "clickableLink": "craftdocs://open?documentId=different-id"}]})
    result = mock_client.create_document("New Doc", folder_id="folder-1")
    assert result["items"][0]["id"] == "new-id"
    body = responses.calls[0].request.body
    import json
    data = json.loads(body)
    assert data["documents"][0]["title"] == "New Doc"
    assert data["destination"]["folderId"] == "folder-1"


@responses.activate
def test_add_blocks_includes_page_id(mock_client):
    """Verify pageId is always included to avoid daily note insertion."""
    responses.add(responses.POST, f"{BASE}/blocks",
                  json={"items": [{"id": "b1"}]})
    mock_client.add_blocks("doc-123", "# Hello")
    import json
    body = json.loads(responses.calls[0].request.body)
    assert body["position"]["pageId"] == "doc-123"
    assert body["position"]["position"] == "end"


@responses.activate
def test_delete_documents(mock_client):
    responses.add(responses.DELETE, f"{BASE}/documents",
                  json={"items": ["d1"]})
    result = mock_client.delete_documents(["d1"])
    assert "d1" in result["items"]


@responses.activate
def test_search_documents(mock_client):
    responses.add(responses.GET, f"{BASE}/documents/search",
                  json={"items": [{"documentId": "d1", "markdown": "found"}]})
    result = mock_client.search_documents("test query")
    assert len(result["items"]) == 1


@responses.activate
def test_get_blocks(mock_client):
    responses.add(responses.GET, f"{BASE}/blocks",
                  json={"id": "0", "type": "page", "content": []})
    result = mock_client.get_blocks("doc-1")
    assert result["type"] == "page"


@responses.activate
def test_delete_blocks(mock_client):
    responses.add(responses.DELETE, f"{BASE}/blocks",
                  json={"items": [{"id": "b1"}, {"id": "b2"}]})
    result = mock_client.delete_blocks(["b1", "b2"])
    assert len(result["items"]) == 2


@responses.activate
def test_update_blocks(mock_client):
    responses.add(responses.PUT, f"{BASE}/blocks",
                  json={"items": [{"id": "b1", "markdown": "updated"}]})
    result = mock_client.update_blocks([{"id": "b1", "markdown": "updated"}])
    assert result["items"][0]["markdown"] == "updated"


@responses.activate
def test_move_blocks(mock_client):
    responses.add(responses.PUT, f"{BASE}/blocks/move",
                  json={"items": [{"id": "b1"}]})
    result = mock_client.move_blocks(["b1"], "doc-2")
    import json
    body = json.loads(responses.calls[0].request.body)
    assert body["position"]["pageId"] == "doc-2"


@responses.activate
def test_list_folders(mock_client):
    responses.add(responses.GET, f"{BASE}/folders",
                  json={"items": [{"id": "f1", "name": "Test", "documentCount": 5}]})
    result = mock_client.list_folders()
    assert result["items"][0]["name"] == "Test"


@responses.activate
def test_create_folder(mock_client):
    responses.add(responses.POST, f"{BASE}/folders",
                  json={"items": [{"id": "f-new", "name": "New"}]})
    result = mock_client.create_folder("New", parent_id="f1")
    import json
    body = json.loads(responses.calls[0].request.body)
    assert body["folders"][0]["parentFolderId"] == "f1"


@responses.activate
def test_list_tasks(mock_client):
    responses.add(responses.GET, f"{BASE}/tasks",
                  json={"items": [{"id": "t1", "markdown": "Do thing"}]})
    result = mock_client.list_tasks("active")
    assert len(result["items"]) == 1


@responses.activate
def test_add_task(mock_client):
    responses.add(responses.POST, f"{BASE}/tasks",
                  json={"items": [{"id": "t-new"}]})
    result = mock_client.add_task("New task", schedule_date="tomorrow")
    import json
    body = json.loads(responses.calls[0].request.body)
    assert body["tasks"][0]["location"]["type"] == "inbox"
    assert body["tasks"][0]["taskInfo"]["scheduleDate"] == "tomorrow"


@responses.activate
def test_list_collections(mock_client):
    responses.add(responses.GET, f"{BASE}/collections",
                  json={"items": [{"id": "c1", "name": "Tasks"}]})
    result = mock_client.list_collections()
    assert result["items"][0]["name"] == "Tasks"


@responses.activate
def test_get_connection(mock_client):
    responses.add(responses.GET, f"{BASE}/connection",
                  json={"space": {"id": "s1"}})
    result = mock_client.get_connection()
    assert "space" in result


@responses.activate
def test_search_blocks(mock_client):
    responses.add(responses.GET, f"{BASE}/blocks/search",
                  json={"items": [{"blockId": "b1", "markdown": "match"}]})
    result = mock_client.search_blocks("doc-1", "match")
    assert len(result["items"]) == 1


@responses.activate
def test_error_handling(mock_client):
    responses.add(responses.GET, f"{BASE}/documents", status=404)
    with pytest.raises(Exception):
        mock_client.list_documents()
