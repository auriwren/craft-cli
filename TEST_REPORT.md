# Test Report - craft-cli

**Date:** 2026-02-09
**Python:** 3.12.3
**Platform:** Linux

## Summary

| Suite | Tests | Passed | Failed |
|-------|-------|--------|--------|
| Unit (mocked) | 17 | 17 | 0 |
| CLI smoke | 6 | 6 | 0 |
| Integration (live API) | 7 | 7 | 0 |
| **Total** | **30** | **30** | **0** |

## Unit Tests (test_client.py)

All 17 tests pass using `responses` library to mock HTTP calls:

- `test_list_documents` - GET /documents
- `test_create_document` - POST /documents with array format and folder destination
- `test_add_blocks_includes_page_id` - Verifies pageId is always set (critical bug prevention)
- `test_delete_documents` - DELETE /documents
- `test_search_documents` - GET /documents/search
- `test_get_blocks` - GET /blocks
- `test_delete_blocks` - DELETE /blocks batch
- `test_update_blocks` - PUT /blocks
- `test_move_blocks` - PUT /blocks/move with pageId
- `test_list_folders` - GET /folders
- `test_create_folder` - POST /folders with parentFolderId
- `test_list_tasks` - GET /tasks
- `test_add_task` - POST /tasks with location and taskInfo
- `test_list_collections` - GET /collections
- `test_get_connection` - GET /connection
- `test_search_blocks` - GET /blocks/search
- `test_error_handling` - HTTP 404 raises exception

## CLI Tests (test_cli.py)

All 6 smoke tests pass using Click's CliRunner:

- Help text for main CLI, doc, block, folder, task, collection groups

## Integration Tests (test_integration.py)

All 7 tests pass against the live Craft API:

- **TestDocumentLifecycle::test_full_lifecycle** - Creates document in Auri folder, adds markdown blocks, reads content (JSON + markdown), searches within document, updates blocks, searches across space, deletes blocks, cleans up document
- **TestFolders::test_list_folders** - Lists folder hierarchy
- **TestConnection::test_get_connection** - Space metadata
- **TestTasks::test_list_active_tasks** - Active task listing
- **TestTasks::test_task_lifecycle** - Create, update (mark done), delete task
- **TestDailyNote::test_read_today** - Today's daily note
- **TestCollections::test_list_collections** - Collection listing

## Critical Behaviors Verified

1. Document creation uses array format `{"documents": [...]}`
2. Block operations use `id` from create response (not clickableLink documentId)
3. `pageId` always included in block position to prevent daily note contamination
4. `requests` library used throughout (not urllib)
5. Proper cleanup in integration tests (documents deleted in finally blocks)
