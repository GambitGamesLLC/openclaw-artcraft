#!/usr/bin/env python3
"""
Example: Using ArtCraft client within OpenClaw workflow.

This shows how to integrate ArtCraft generation into an OpenClaw
orchestration workflow.
"""

from artcraft_client import ArtCraftClient

def generate_concept_art(concept_description: str):
    """
    Generate concept art for a game idea.
    
    Args:
        concept_description: Description of the concept to visualize
        
    Returns:
        Dictionary with main concept, variations, and task IDs
    """
    client = ArtCraftClient()
    
    print(f"Generating concept art for: {concept_description}")
    
    # Generate main concept
    print("  Generating main concept...")
    result = client.generate_text_to_image(
        prompt=f"professional concept art: {concept_description}",
        provider="openai",
        aspect_ratio="16:9"
    )
    
    # Generate variations
    variations = []
    for angle in ["front view", "side view", "top-down view"]:
        print(f"  Generating {angle}...")
        var = client.generate_text_to_image(
            prompt=f"{concept_description}, {angle}, concept art",
            provider="openai",
            wait=True
        )
        if var.output_files:
            variations.append(var.output_files[0])
    
    return {
        "main_concept": result.output_files[0] if result.output_files else None,
        "variations": variations,
        "task_ids": [result.task_id] + [v.task_id for v in variations] if hasattr(v, 'task_id') else []
    }

def main():
    print("ArtCraft Client - OpenClaw Integration Example")
    print("=" * 50)
    
    # Generate concept art for a steampunk airship
    result = generate_concept_art("steampunk airship with brass details")
    
    print("\nResults:")
    print(f"  Main concept: {result['main_concept']}")
    print(f"  Variations: {result['variations']}")
    print(f"  Task IDs: {result['task_ids']}")

if __name__ == "__main__":
    main()
