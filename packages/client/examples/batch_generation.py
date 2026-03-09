#!/usr/bin/env python3
"""
Batch generation example for ArtCraft Client.

This script demonstrates how to submit multiple generation tasks
and wait for all of them to complete.
"""

from artcraft_client import ArtCraftClient

def main():
    # Initialize client
    client = ArtCraftClient()
    
    print("ArtCraft Client - Batch Generation Example")
    print("=" * 50)
    
    prompts = [
        "cyberpunk city at night",
        "fantasy castle in mountains",
        "sci-fi spaceship interior"
    ]
    
    # Submit all tasks
    print("\nSubmitting batch generation tasks...")
    task_ids = []
    for prompt in prompts:
        print(f"  Submitting: {prompt}")
        result = client.generate_text_to_image(prompt, wait=False)
        task_ids.append(result.task_id)
        print(f"    Task ID: {result.task_id}")
    
    print(f"\nSubmitted {len(task_ids)} tasks")
    
    # Wait for all to complete
    print("\nWaiting for all tasks to complete...")
    for task_id in task_ids:
        print(f"  Waiting for {task_id}...")
        try:
            result = client.wait_for_completion(task_id, timeout=300)
            print(f"    Completed: {task_id} -> {result.status}")
        except Exception as e:
            print(f"    Error: {e}")
    
    # Show final queue status
    print("\nFinal queue status:")
    tasks = client.get_task_queue()
    for task in tasks:
        print(f"  {task.id}: {task.status}")

if __name__ == "__main__":
    main()
