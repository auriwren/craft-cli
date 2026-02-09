# craft-cli

A Python CLI tool for managing Craft.do documents, blocks, folders, tasks, and collections via the Craft Space API.

## Installation

```bash
git clone https://github.com/auriwren/craft-cli.git
cd craft-cli
pip install -e ".[dev]"
```

## Configuration

Set environment variables or create `~/.openclaw/credentials/craft.env`:

```env
CRAFT_API_BASE=https://connect.craft.do/links/YOUR_LINK/api/v1
CRAFT_API_KEY=pdk_your_api_key_here
```

## Usage

### Documents

```bash
# List all documents
craft-cli doc list

# List documents in a folder
craft-cli doc list --folder 3ee338c6-fc27-cbd6-e324-584c60ddfc86

# List documents by location
craft-cli doc list --location unsorted

# Create a document (defaults to Auri folder)
craft-cli doc create "My New Document"

# Create with content
craft-cli doc create "My Doc" --content "## Hello\n\nWorld"

# Create with content from file
craft-cli doc create "My Doc" --content @content.md

# Read a document (JSON block tree)
craft-cli doc read <doc_id>

# Read as markdown
craft-cli doc read <doc_id> --format markdown

# Search documents
craft-cli doc search "meeting notes"

# Move a document
craft-cli doc move <doc_id> --to-folder <folder_id>

# Delete a document (moves to trash)
craft-cli doc delete <doc_id>
```

### Blocks

```bash
# List blocks in a document
craft-cli block list <doc_id>

# Add content to a document
craft-cli block add <doc_id> -m "## New Section\n\nSome content"

# Add from file
craft-cli block add <doc_id> -m @notes.md

# Add to beginning
craft-cli block add <doc_id> -m "First!" --position start

# Update a block
craft-cli block update <block_id> -m "Updated content"

# Delete blocks
craft-cli block delete <block_id1> <block_id2>

# Move a block to another document
craft-cli block move <block_id> --to-doc <doc_id>

# Search within a document
craft-cli block search <doc_id> "pattern"
```

### Folders

```bash
# List all folders (tree view)
craft-cli folder list

# Create a folder
craft-cli folder create "New Folder"

# Create nested folder
craft-cli folder create "Subfolder" --parent <folder_id>

# Move a folder
craft-cli folder move <folder_id> --parent <new_parent_id>

# Delete a folder
craft-cli folder delete <folder_id>
```

### Tasks

```bash
# List active tasks
craft-cli task list --scope active

# List inbox tasks
craft-cli task list --scope inbox

# List tasks in a document
craft-cli task list --scope document --doc <doc_id>

# Add a task to inbox
craft-cli task add "Review PR" --schedule tomorrow

# Add task to daily note
craft-cli task add "Stand-up" --location daily --date today

# Add task to document
craft-cli task add "Research" --location document --doc <doc_id>

# Mark task done
craft-cli task update <task_id> --state done

# Delete a task
craft-cli task delete <task_id>
```

### Collections

```bash
# List all collections
craft-cli collection list

# List collections in a document
craft-cli collection list --doc <doc_id>

# Get collection schema
craft-cli collection schema <collection_id>

# List collection items
craft-cli collection items <collection_id>

# Add item
craft-cli collection add-item <collection_id> --title "New Item" --props status=Active --props priority=High

# Update item
craft-cli collection update-item <collection_id> <item_id> --props status=Done

# Delete item
craft-cli collection delete-item <collection_id> <item_id>
```

### Utility

```bash
# View space connection info
craft-cli connection

# Read today's daily note
craft-cli daily

# Read yesterday's daily note as markdown
craft-cli daily --date yesterday --format markdown

# Upload a file
craft-cli upload photo.jpg --to-doc <doc_id>
```

### Global Options

```bash
# JSON output for any command
craft-cli --json-output doc list

# Help
craft-cli --help
craft-cli doc --help
```

## Key Design Decisions

- Uses `requests` library (not urllib) to avoid Cloudflare 403 errors
- Document creation uses the `id` field from response (not `documentId` from clickableLink)
- Block insertion always includes `pageId` to prevent content going to the daily note
- Documents array format for POST /documents as required by the API

## Development

```bash
# Run unit tests
python3 -m pytest tests/test_client.py tests/test_cli.py -v

# Run integration tests (requires valid API credentials)
python3 -m pytest tests/test_integration.py -v

# Run all tests
python3 -m pytest -v
```

## License

MIT
