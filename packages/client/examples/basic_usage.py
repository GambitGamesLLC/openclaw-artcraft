#!/usr/bin/env python3
"""
Basic usage example for ArtCraft Client.

This script demonstrates how to use the ArtCraftClient to generate images.
"""

from artcraft_client import ArtCraftClient

def main():
    # Initialize client
    client = ArtCraftClient()
    
    print("ArtCraft Client - Basic Usage Example")
    print("=" * 50)
    
    # Generate an image
    print("\nGenerating image: 'futuristic cat robot in cyberpunk city'")
    result = client.generate_text_to_image(
        prompt="futuristic cat robot in cyberpunk city",
        provider="openai",
        wait=True
    )
    
    print(f"\nTask ID: {result.task_id}")
    print(f"Status: {result.status}")
    print(f"Generated files: {result.output_files}")
    
    # Check queue
    print("\nCurrent task queue:")
    tasks = client.get_task_queue()
    for task in tasks:
        print(f"  {task.id}: {task.status} ({task.type})")

if __name__ == "__main__":
    main()
