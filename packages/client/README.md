# OpenClaw ArtCraft (Client)

Python client library for controlling ArtCraft AI generation programmatically via the CLI wrapper.

## Overview

`openclaw-artcraft` provides a Python interface to the ArtCraft CLI (`artcraft-cli.sh`), enabling seamless integration of AI image and video generation into Python applications and OpenClaw workflows.

## Features

- 🎨 **Text-to-Image Generation** - Generate images from text prompts
- 🎬 **Image-to-Video Generation** - Create videos from images
- ✏️ **Image Editing** - Edit existing images with text prompts
- 📋 **Queue Management** - List, dismiss, and purge tasks
- ⏳ **Wait for Completion** - Poll for task completion with timeout
- 📥 **Media Download** - Download generated media files
- 🔄 **Batch Operations** - Submit and manage multiple tasks

## Installation

### From Source

```bash
cd /path/to/openclaw-artcraft/packages/client
pip install -e .
```

### Requirements

- Python 3.8+
- ArtCraft CLI (`artcraft-cli.sh`) - see [gambit-artcraft](../gambit-artcraft/)
- No external Python dependencies (uses subprocess for CLI calls)

## Quick Start

```python
from artcraft_client import ArtCraftClient

# Initialize client
client = ArtCraftClient()

# Generate an image
result = client.generate_text_to_image(
    prompt="futuristic cat robot in cyberpunk city",
    provider="openai",
    wait=True
)

print(f"Generated: {result.output_files}")
```

## API Reference

### ArtCraftClient

#### Initialization

```python
client = ArtCraftClient(
    cli_path="/path/to/artcraft-cli.sh",  # Auto-detected if None
    artcraft_dir="/path/to/gambit-artcraft"  # Auto-detected if None
)
```

#### Generation Methods

##### `generate_text_to_image(prompt, provider="openai", model=None, aspect_ratio="16:9", wait=True, timeout=300)`

Generate an image from a text prompt.

**Parameters:**
- `prompt` (str): Text description of the image
- `provider` (str): AI provider (openai, grok, midjourney, etc.)
- `model` (str, optional): Specific model to use
- `aspect_ratio` (str): Image aspect ratio (default: "16:9")
- `wait` (bool): Wait for completion (default: True)
- `timeout` (int): Max wait time in seconds (default: 300)

**Returns:** `GenerationResult`

##### `generate_image_to_video(image_path, prompt=None, provider="openai", wait=True, timeout=600)`

Generate a video from an image.

**Parameters:**
- `image_path` (str): Path to source image or media token
- `prompt` (str, optional): Optional prompt for video
- `provider` (str): AI provider
- `wait` (bool): Wait for completion
- `timeout` (int): Max wait time (default: 600s for video)

**Returns:** `GenerationResult`

##### `generate_edit_image(image_path, prompt, provider="openai", wait=True, timeout=300)`

Edit an existing image.

**Parameters:**
- `image_path` (str): Path to source image or media token
- `prompt` (str): Description of edits to make
- `provider` (str): AI provider
- `wait` (bool): Wait for completion
- `timeout` (int): Max wait time

**Returns:** `GenerationResult`

#### Queue Management

##### `get_task_queue() -> List[Task]`

Get all tasks in the queue.

**Returns:** List of `Task` objects

##### `get_task_status(task_id: str) -> Task`

Get status of a specific task.

**Parameters:**
- `task_id` (str): ID of task to check

**Returns:** `Task` object

##### `wait_for_completion(task_id, timeout=300, poll_interval=10) -> Task`

Wait for a task to complete.

**Parameters:**
- `task_id` (str): ID of task to wait for
- `timeout` (int): Max wait time in seconds
- `poll_interval` (int): Time between status checks

**Returns:** `Task` object with final status

**Raises:** `TimeoutError` if task doesn't complete, `TaskFailedError` if task fails

##### `dismiss_task(task_id: str) -> bool`

Dismiss a task from the queue.

**Returns:** True if successful

##### `purge_queue() -> bool`

Remove all completed tasks.

**Returns:** True if successful

#### Media Operations

##### `download_media(task_id, output_dir=None) -> str`

Download generated media for a task.

**Parameters:**
- `task_id` (str): ID of task
- `output_dir` (str, optional): Output directory

**Returns:** Path to downloaded file

### Data Models

#### Task

```python
@dataclass
class Task:
    id: str
    status: str  # pending, processing, completed, failed, dismissed
    type: str    # text_to_image, image_to_video, etc.
    prompt: str
    provider: str
    created_at: str
    completed_at: str = None
    error: str = None
```

#### GenerationResult

```python
@dataclass
class GenerationResult:
    task_id: str
    status: str
    input_prompt: str
    output_files: List[str]  # Paths to generated files
    media_tokens: List[str]
    duration_seconds: float = None
```

#### MediaFile

```python
@dataclass
class MediaFile:
    token: str
    type: str  # image, video
    url: str = None
    path: str = None
```

### Exceptions

- `ArtCraftError` - Base exception
- `CommandNotFoundError` - CLI not found or not executable
- `TaskFailedError` - Task failed during generation
- `TimeoutError` - Task didn't complete within timeout
- `CLIExecutionError` - CLI command execution failed

## Examples

### Basic Usage

```python
from artcraft_client import ArtCraftClient

client = ArtCraftClient()

# Generate an image
result = client.generate_text_to_image(
    prompt="cyberpunk city at night",
    provider="openai"
)

print(f"Generated: {result.output_files}")
```

### Batch Generation

```python
from artcraft_client import ArtCraftClient

client = ArtCraftClient()

prompts = [
    "cyberpunk city at night",
    "fantasy castle in mountains",
    "sci-fi spaceship interior"
]

# Submit all tasks
task_ids = []
for prompt in prompts:
    result = client.generate_text_to_image(prompt, wait=False)
    task_ids.append(result.task_id)

# Wait for all to complete
for task_id in task_ids:
    result = client.wait_for_completion(task_id, timeout=300)
    print(f"Completed: {task_id} -> {result.output_files}")
```

### OpenClaw Integration

```python
from artcraft_client import ArtCraftClient

def generate_concept_art(concept_description: str):
    """Generate concept art for a game idea."""
    client = ArtCraftClient()
    
    # Generate main concept
    result = client.generate_text_to_image(
        prompt=f"professional concept art: {concept_description}",
        provider="openai",
        aspect_ratio="16:9"
    )
    
    # Generate variations
    variations = []
    for angle in ["front view", "side view", "top-down view"]:
        var = client.generate_text_to_image(
            prompt=f"{concept_description}, {angle}, concept art",
            provider="openai"
        )
        variations.append(var.output_files[0])
    
    return {
        "main_concept": result.output_files[0],
        "variations": variations
    }
```

### Queue Management

```python
from artcraft_client import ArtCraftClient

client = ArtCraftClient()

# List all tasks
tasks = client.get_task_queue()
for task in tasks:
    print(f"{task.id}: {task.status}")

# Wait for specific task
task = client.wait_for_completion("task-123", timeout=300)

# Dismiss a task
client.dismiss_task("task-456")

# Purge completed tasks
client.purge_queue()
```

## Supported Providers

- `artcraft` (default, uses Storyteller/OpenAI)
- `openai` (alias for artcraft)
- `grok`
- `midjourney`
- `sora` (for video)

## Supported Models

### Text-to-Image
- `flux_1_dev`, `flux_1_schnell`, `flux_pro_11`, `flux_pro_11_ultra`
- `grok_image`, `recraft_3`, `gpt_image_1`, `gpt_image_1p5`
- `gemini_25_flash`, `nano_banana`, `nano_banana_2`, `nano_banana_pro`
- `seedream_4`, `seedream_4p5`, `seedream_5_lite`, `midjourney`

### Image-to-Video
- `grok_video`, `kling_*`, `seedance_*`, `sora_2`, `sora_2_pro`
- `veo_2`, `veo_3`, `veo_3_fast`, `veo_3p1`, `veo_3p1_fast`

### Image Edit
- `flux_pro_kontext_max`, `gemini_25_flash`
- `nano_banana*`, `gpt_image_*`, `seedream_*`

## CLI Usage

The package includes a CLI entry point:

```bash
# Generate an image
openclaw-artcraft generate "futuristic city"

# Check task status
openclaw-artcraft status [task_id]

# View queue
openclaw-artcraft queue
```

## Testing

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/test_client.py -v
```

## Troubleshooting

### CLI Not Found

**Error:** `CommandNotFoundError: ArtCraft CLI not found at ...`

**Solution:** Ensure `artcraft-cli.sh` exists at the expected location or provide the path:

```python
client = ArtCraftClient(cli_path="/custom/path/artcraft-cli.sh")
```

### Permission Denied

**Error:** `PermissionError` when trying to make CLI executable

**Solution:** Manually make the CLI executable:

```bash
chmod +x /path/to/artcraft-cli.sh
```

### Task Timeout

**Error:** `TimeoutError: Task did not complete within 300 seconds`

**Solution:** Increase the timeout parameter:

```python
result = client.wait_for_completion(task_id, timeout=600)
```

### Task Failed

**Error:** `TaskFailedError: Task failed: <error message>`

**Solution:** Check the error message for details. Common causes:
- Invalid prompt
- Provider unavailable
- Rate limiting

## Development

### Project Structure

```
openclaw-artcraft/packages/client/
├── artcraft_client/
│   ├── __init__.py
│   ├── client.py      # Main client class
│   ├── models.py      # Data classes
│   └── exceptions.py  # Custom exceptions
├── examples/
│   ├── basic_usage.py
│   ├── batch_generation.py
│   └── openclaw_integration.py
├── tests/
│   └── test_client.py
├── requirements.txt
├── setup.py
└── README.md
```

### Running Examples

```bash
cd /path/to/openclaw-artcraft/packages/client
pip install -e .

# Run basic usage example
python examples/basic_usage.py

# Run batch generation example
python examples/batch_generation.py

# Run OpenClaw integration example
python examples/openclaw_integration.py
```

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions welcome! Please open an issue or submit a PR.

---

*Version: 0.1.0*  
*Created: 2026-03-07*
