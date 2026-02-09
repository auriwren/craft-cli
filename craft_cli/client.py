"""Craft.do API client using requests (not urllib -- Cloudflare 403s)."""

from __future__ import annotations

from typing import Any

import requests

from .config import get_api_base, get_api_key


class CraftClient:
    """Low-level wrapper around the Craft.do REST API."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = (base_url or get_api_base()).rstrip("/")
        self.api_key = api_key or get_api_key()
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "craft-cli/0.1.0",
        })

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def _request(self, method: str, path: str, **kwargs) -> Any:
        resp = self.session.request(method, self._url(path), **kwargs)
        resp.raise_for_status()
        if resp.headers.get("content-type", "").startswith("text/markdown"):
            return resp.text
        if not resp.content:
            return {}
        return resp.json()

    # --- Documents ---

    def list_documents(self, *, folder_id: str | None = None,
                       location: str | None = None,
                       fetch_metadata: bool = False,
                       **date_filters) -> dict:
        params: dict[str, Any] = {}
        if folder_id:
            params["folderId"] = folder_id
        if location:
            params["location"] = location
        if fetch_metadata:
            params["fetchMetadata"] = "true"
        for k, v in date_filters.items():
            if v is not None:
                params[k] = v
        return self._request("GET", "/documents", params=params)

    def create_document(self, title: str, *, folder_id: str | None = None,
                        destination: str | None = None) -> dict:
        """Create a document. Returns response with items[].id (correct ID for blocks)."""
        body: dict[str, Any] = {"documents": [{"title": title}]}
        if folder_id:
            body["destination"] = {"folderId": folder_id}
        elif destination:
            body["destination"] = {"destination": destination}
        return self._request("POST", "/documents", json=body)

    def delete_documents(self, doc_ids: list[str]) -> dict:
        return self._request("DELETE", "/documents", json={"documentIds": doc_ids})

    def move_documents(self, doc_ids: list[str], *,
                       folder_id: str | None = None,
                       destination: str | None = None) -> dict:
        body: dict[str, Any] = {"documentIds": doc_ids}
        if folder_id:
            body["destination"] = {"folderId": folder_id}
        elif destination:
            body["destination"] = {"destination": destination}
        return self._request("PUT", "/documents/move", json=body)

    def search_documents(self, query: str, **kwargs) -> dict:
        params: dict[str, Any] = {"include": query}
        for k, v in kwargs.items():
            if v is not None:
                params[k] = v
        return self._request("GET", "/documents/search", params=params)

    # --- Blocks ---

    def get_blocks(self, doc_id: str, *, max_depth: int = -1,
                   fetch_metadata: bool = False,
                   accept_markdown: bool = False) -> Any:
        params: dict[str, Any] = {"id": doc_id}
        if max_depth != -1:
            params["maxDepth"] = max_depth
        if fetch_metadata:
            params["fetchMetadata"] = "true"
        headers = {}
        if accept_markdown:
            headers["Accept"] = "text/markdown"
        return self._request("GET", "/blocks", params=params, headers=headers)

    def get_daily_note(self, date: str = "today") -> Any:
        return self._request("GET", "/blocks", params={"date": date})

    def add_blocks(self, doc_id: str, markdown: str, *,
                   position: str = "end") -> dict:
        """Add markdown content to a document.
        CRITICAL: pageId MUST be specified or content goes to daily note."""
        body = {
            "markdown": markdown,
            "position": {"position": position, "pageId": doc_id},
        }
        return self._request("POST", "/blocks", json=body)

    def delete_blocks(self, block_ids: list[str]) -> dict:
        return self._request("DELETE", "/blocks", json={"blockIds": block_ids})

    def update_blocks(self, blocks: list[dict]) -> dict:
        return self._request("PUT", "/blocks", json={"blocks": blocks})

    def move_blocks(self, block_ids: list[str], doc_id: str, *,
                    position: str = "end") -> dict:
        body = {
            "blockIds": block_ids,
            "position": {"position": position, "pageId": doc_id},
        }
        return self._request("PUT", "/blocks/move", json=body)

    def search_blocks(self, block_id: str, pattern: str, *,
                      case_sensitive: bool = False,
                      before_count: int = 0, after_count: int = 0) -> dict:
        params: dict[str, Any] = {"blockId": block_id, "pattern": pattern}
        if case_sensitive:
            params["caseSensitive"] = "true"
        if before_count:
            params["beforeBlockCount"] = before_count
        if after_count:
            params["afterBlockCount"] = after_count
        return self._request("GET", "/blocks/search", params=params)

    # --- Folders ---

    def list_folders(self) -> dict:
        return self._request("GET", "/folders")

    def create_folder(self, name: str, *, parent_id: str | None = None) -> dict:
        folder: dict[str, Any] = {"name": name}
        if parent_id:
            folder["parentFolderId"] = parent_id
        return self._request("POST", "/folders", json={"folders": [folder]})

    def delete_folders(self, folder_ids: list[str]) -> dict:
        return self._request("DELETE", "/folders", json={"folderIds": folder_ids})

    def move_folders(self, folder_ids: list[str], *,
                     parent_id: str | None = None) -> dict:
        dest: Any = {"parentFolderId": parent_id} if parent_id else "root"
        return self._request("PUT", "/folders/move",
                             json={"folderIds": folder_ids, "destination": dest})

    # --- Tasks ---

    def list_tasks(self, scope: str, *, document_id: str | None = None) -> dict:
        params: dict[str, Any] = {"scope": scope}
        if document_id:
            params["documentId"] = document_id
        return self._request("GET", "/tasks", params=params)

    def add_task(self, markdown: str, *,
                 location_type: str = "inbox",
                 date: str | None = None,
                 document_id: str | None = None,
                 schedule_date: str | None = None,
                 deadline_date: str | None = None) -> dict:
        task: dict[str, Any] = {"markdown": markdown}
        loc: dict[str, Any] = {"type": location_type}
        if location_type == "dailyNote" and date:
            loc["date"] = date
        elif location_type == "document" and document_id:
            loc["documentId"] = document_id
        task["location"] = loc
        task_info: dict[str, str] = {}
        if schedule_date:
            task_info["scheduleDate"] = schedule_date
        if deadline_date:
            task_info["deadlineDate"] = deadline_date
        if task_info:
            task["taskInfo"] = task_info
        return self._request("POST", "/tasks", json={"tasks": [task]})

    def update_task(self, task_id: str, *,
                    state: str | None = None,
                    markdown: str | None = None,
                    schedule_date: str | None = None,
                    deadline_date: str | None = None) -> dict:
        update: dict[str, Any] = {"id": task_id}
        if markdown:
            update["markdown"] = markdown
        task_info: dict[str, Any] = {}
        if state:
            task_info["state"] = state
        if schedule_date:
            task_info["scheduleDate"] = schedule_date
        if deadline_date:
            task_info["deadlineDate"] = deadline_date
        if task_info:
            update["taskInfo"] = task_info
        return self._request("PUT", "/tasks", json={"tasksToUpdate": [update]})

    def delete_tasks(self, task_ids: list[str]) -> dict:
        return self._request("DELETE", "/tasks", json={"idsToDelete": task_ids})

    # --- Collections ---

    def list_collections(self, *, document_ids: list[str] | None = None) -> dict:
        params = {}
        if document_ids:
            params["documentIds"] = ",".join(document_ids)
        return self._request("GET", "/collections", params=params)

    def get_collection_schema(self, collection_id: str,
                              fmt: str = "json-schema-items") -> dict:
        return self._request("GET", f"/collections/{collection_id}/schema",
                             params={"format": fmt})

    def get_collection_items(self, collection_id: str,
                             max_depth: int = -1) -> dict:
        params: dict[str, Any] = {}
        if max_depth != -1:
            params["maxDepth"] = max_depth
        return self._request("GET", f"/collections/{collection_id}/items",
                             params=params)

    def add_collection_items(self, collection_id: str,
                             items: list[dict]) -> dict:
        return self._request("POST", f"/collections/{collection_id}/items",
                             json={"items": items})

    def update_collection_items(self, collection_id: str,
                                items: list[dict]) -> dict:
        return self._request("PUT", f"/collections/{collection_id}/items",
                             json={"itemsToUpdate": items})

    def delete_collection_items(self, collection_id: str,
                                item_ids: list[str]) -> dict:
        return self._request("DELETE", f"/collections/{collection_id}/items",
                             json={"idsToDelete": item_ids})

    # --- Utility ---

    def get_connection(self) -> dict:
        return self._request("GET", "/connection")

    def upload_file(self, file_path: str, page_id: str,
                    position: str = "end") -> dict:
        import mimetypes
        ct = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        with open(file_path, "rb") as f:
            data = f.read()
        headers = {"Content-Type": ct}
        params = {"position": position, "pageId": page_id}
        return self._request("POST", "/upload", data=data,
                             params=params, headers=headers)

    def add_comment(self, block_id: str, content: str) -> dict:
        return self._request("POST", "/comments",
                             json={"comments": [{"blockId": block_id, "content": content}]})
