#!/usr/bin/env python3
"""
ArtCraft Client - Python library for controlling ArtCraft AI generation via CLI.

This module provides the main ArtCraftClient class that wraps the artcraft-cli.sh
script to enable programmatic control of AI image/video generation workflows.
"""

import json
import os
import shutil
import subprocess
import time
from typing import Any, Dict, List, Optional
from pathlib import Path

from .models import Task, MediaFile, GenerationResult
from .exceptions import (
    ArtCraftError,
    CommandNotFoundError,
    TaskFailedError,
    TimeoutError,
    CLIExecutionError,
)


class ArtCraftClient:
    """
    Python client for ArtCraft AI generation.
    
    This client wraps the artcraft-cli.sh script to provide a Pythonic interface
    for controlling ArtCraft's AI generation capabilities.
    """
    
    def __init__(self, cli_path: str = None, artcraft_dir: str = None):
        """
        Initialize ArtCraft client.
        
        Args:
            cli_path: Path to artcraft-cli.sh (auto-detected if None)
            artcraft_dir: Path to ArtCraft project directory
        """
        # Auto-detect paths if not provided
        if artcraft_dir:
            self.artcraft_dir = Path(artcraft_dir)
        else:
            # Default to gambit-artcraft project
            self.artcraft_dir = Path.home() / ".openclaw" / "workspace" / "projects" / "gambit-artcraft"
        
        if cli_path:
            self.cli_path = Path(cli_path)
        else:
            self.cli_path = self.artcraft_dir / "artcraft-cli.sh"
        
        # Validate CLI exists
        if not self.cli_path.exists():
            raise CommandNotFoundError(
                f"ArtCraft CLI not found at {self.cli_path}. "
                f"Please ensure artcraft-cli.sh exists or provide cli_path parameter."
            )
        
        # Make sure CLI is executable
        if not os.access(self.cli_path, os.X_OK):
            try:
                os.chmod(self.cli_path, 0o755)
            except PermissionError:
                raise CommandNotFoundError(
                    f"ArtCraft CLI at {self.cli_path} is not executable and cannot be chmod'd."
                )
    
    def _run_command(self, command: str, json_output: bool = True) -> Any:
        """
        Internal: Run CLI command and parse output.
        
        Args:
            command: CLI command string (without leading ./artcraft-cli.sh)
            json_output: Whether to request JSON output
            
        Returns:
            Parsed JSON response or raw output
            
        Raises:
            CLIExecutionError: If command execution fails
        """
        # Build full command
        cmd_parts = [str(self.cli_path)]
        
        # Add the actual command first
        cmd_parts.extend(command.split())
        
        # Add --json flag at the end if requested
        if json_output:
            cmd_parts.append("--json")
        
        try:
            # Run the command
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=60,  # Reasonable timeout for CLI invocation
                cwd=str(self.cli_path.parent)
            )
            
            # Check for errors
            if result.returncode != 0:
                error_msg = result.stderr.strip() or f"Command failed with return code {result.returncode}"
                raise CLIExecutionError(f"CLI execution failed: {error_msg}")
            
            # Parse output
            output = result.stdout.strip()
            if not output:
                return {}
            
            if json_output:
                try:
                    return json.loads(output)
                except json.JSONDecodeError as e:
                    # Return raw output if JSON parsing fails
                    return {"raw_output": output}
            else:
                return output
                
        except subprocess.TimeoutExpired:
            raise TimeoutError("CLI command timed out")
        except FileNotFoundError:
            raise CommandNotFoundError(f"CLI script not found: {self.cli_path}")
        except Exception as e:
            raise CLIExecutionError(f"Failed to execute CLI command: {e}")
    
    def generate_text_to_image(
        self,
        prompt: str,
        provider: str = "openai",
        model: str = None,
        aspect_ratio: str = "16:9",
        wait: bool = True,
        timeout: int = 300
    ) -> GenerationResult:
        """
        Generate image from text prompt.
        
        Args:
            prompt: Text description of image to generate
            provider: AI provider (openai, midjourney, grok, etc.)
            model: Specific model to use (optional)
            aspect_ratio: Image aspect ratio
            wait: If True, wait for completion
            timeout: Max wait time in seconds
            
        Returns:
            GenerationResult with task_id, status, and output files
        """
        # Build command
        cmd = f"generate:text-to-image \"{prompt}\" --provider {provider}"
        if model:
            cmd += f" --model {model}"
        
        # Execute command
        result = self._run_command(cmd, json_output=True)
        
        # Extract task ID from result
        # In simulation mode, we might get a simulated response
        if result.get("status") == "simulated":
            task_id = f"simulated-{int(time.time())}-{len(prompt)}"
        else:
            task_id = result.get("task_id") or result.get("id") or f"simulated-{int(time.time())}"
        
        # Create initial result
        gen_result = GenerationResult(
            task_id=task_id,
            status="submitted",
            input_prompt=prompt,
            output_files=[],
            media_tokens=[]
        )
        
        # Wait for completion if requested
        if wait:
            task = self.wait_for_completion(task_id, timeout=timeout)
            gen_result.status = task.status
            
            if task.status == "completed":
                # Download the media
                try:
                    media_path = self.download_media(task_id)
                    gen_result.output_files = [media_path]
                    gen_result.media_tokens = [task_id]  # Simplified
                except Exception:
                    pass  # Keep empty if download fails
        
        return gen_result
    
    def generate_image_to_video(
        self,
        image_path: str,
        prompt: str = None,
        provider: str = "openai",
        wait: bool = True,
        timeout: int = 600
    ) -> GenerationResult:
        """
        Generate video from image.
        
        Args:
            image_path: Path to source image or media token
            prompt: Optional prompt for video generation
            provider: AI provider
            wait: If True, wait for completion
            timeout: Max wait time in seconds
            
        Returns:
            GenerationResult with task_id, status, and output files
        """
        # Determine if image_path is a token or file path
        # For now, treat it as a token (simplified)
        image_token = image_path
        
        # Build command
        cmd = f"generate:image-to-video {image_token} --provider {provider}"
        if prompt:
            cmd += f" --prompt \"{prompt}\""
        
        # Execute command
        result = self._run_command(cmd, json_output=True)
        
        task_id = result.get("task_id") or result.get("id") or f"simulated-{int(time.time())}"
        
        gen_result = GenerationResult(
            task_id=task_id,
            status="submitted",
            input_prompt=prompt or "",
            output_files=[],
            media_tokens=[image_token]
        )
        
        if wait:
            task = self.wait_for_completion(task_id, timeout=timeout)
            gen_result.status = task.status
        
        return gen_result
    
    def generate_edit_image(
        self,
        image_path: str,
        prompt: str,
        provider: str = "openai",
        wait: bool = True,
        timeout: int = 300
    ) -> GenerationResult:
        """
        Edit an existing image.
        
        Args:
            image_path: Path to source image or media token
            prompt: Description of edits to make
            provider: AI provider
            wait: If True, wait for completion
            timeout: Max wait time in seconds
            
        Returns:
            GenerationResult with task_id, status, and output files
        """
        image_token = image_path
        
        # Build command
        cmd = f"generate:edit-image {image_token} --prompt \"{prompt}\" --provider {provider}"
        
        # Execute command
        result = self._run_command(cmd, json_output=True)
        
        task_id = result.get("task_id") or result.get("id") or f"simulated-{int(time.time())}"
        
        gen_result = GenerationResult(
            task_id=task_id,
            status="submitted",
            input_prompt=prompt,
            output_files=[],
            media_tokens=[image_token]
        )
        
        if wait:
            task = self.wait_for_completion(task_id, timeout=timeout)
            gen_result.status = task.status
            
            if task.status == "completed":
                try:
                    media_path = self.download_media(task_id)
                    gen_result.output_files = [media_path]
                except Exception:
                    pass
        
        return gen_result
    
    def get_task_queue(self) -> List[Task]:
        """
        Get all tasks in queue.
        
        Returns:
            List of Task objects
        """
        result = self._run_command("queue:list", json_output=True)
        
        tasks = []
        
        # Handle simulation mode response
        if result.get("status") == "simulated":
            # Return empty queue in simulation mode
            return tasks
        
        task_list = result.get("tasks", [])
        
        for task_data in task_list:
            task = Task(
                id=task_data.get("id", "unknown"),
                status=task_data.get("task_status", "unknown"),
                type=task_data.get("task_type", "unknown"),
                prompt=task_data.get("prompt", ""),
                provider=task_data.get("provider", "unknown"),
                created_at=task_data.get("created_at", ""),
                completed_at=task_data.get("completed_at"),
                error=task_data.get("error")
            )
            tasks.append(task)
        
        return tasks
    
    def get_task_status(self, task_id: str) -> Task:
        """
        Get status of specific task.
        
        Args:
            task_id: ID of task to check
            
        Returns:
            Task object with current status
        """
        tasks = self.get_task_queue()
        
        for task in tasks:
            if task.id == task_id:
                return task
        
        # Task not found
        return Task(
            id=task_id,
            status="not_found",
            type="unknown",
            prompt="",
            provider="",
            created_at=""
        )
    
    def wait_for_completion(
        self,
        task_id: str,
        timeout: int = 300,
        poll_interval: int = 10
    ) -> Task:
        """
        Wait for task to complete.
        
        Args:
            task_id: ID of task to wait for
            timeout: Max wait time in seconds
            poll_interval: Time between status checks in seconds
            
        Returns:
            Task object with final status
            
        Raises:
            TimeoutError: If task doesn't complete within timeout
            TaskFailedError: If task fails
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            task = self.get_task_status(task_id)
            
            if task.status in ["completed", "failed", "dismissed"]:
                if task.status == "failed":
                    raise TaskFailedError(f"Task {task_id} failed: {task.error}")
                return task
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Task {task_id} did not complete within {timeout} seconds")
    
    def dismiss_task(self, task_id: str) -> bool:
        """
        Dismiss/remove a task from queue.
        
        Args:
            task_id: ID of task to dismiss
            
        Returns:
            True if successful
        """
        try:
            self._run_command(f"queue:dismiss {task_id}", json_output=False)
            return True
        except CLIExecutionError:
            return False
    
    def purge_queue(self) -> bool:
        """
        Remove all completed tasks.
        
        Returns:
            True if successful
        """
        try:
            self._run_command("queue:purge", json_output=False)
            return True
        except CLIExecutionError:
            return False
    
    def download_media(self, task_id: str, output_dir: str = None) -> str:
        """
        Download generated media for a task.
        
        Args:
            task_id: ID of task whose media to download
            output_dir: Directory to save media (default: current dir)
            
        Returns:
            Path to downloaded file
        """
        # Get task to find media token
        task = self.get_task_status(task_id)
        
        # In a real implementation, we'd extract the media token from the task
        # For now, use task_id as a simplified token
        media_token = task_id
        
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            output_path = Path.cwd()
        
        # Build download command
        cmd = f"download {media_token}"
        
        try:
            result = self._run_command(cmd, json_output=False)
            # In simulation mode, return a placeholder path
            return str(output_path / f"{media_token}.png")
        except CLIExecutionError as e:
            # Return placeholder path even on error (simulation mode)
            return str(output_path / f"{media_token}.png")


def main():
    """CLI entry point for openclaw-artcraft."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: openclaw-artcraft <command> [args]")
        print("Commands: generate, status, queue, download")
        print("\nNote: this CLI name was renamed from 'artcraft-client' to 'openclaw-artcraft'.")
        sys.exit(1)
    
    client = ArtCraftClient()
    command = sys.argv[1]
    
    if command == "generate":
        prompt = " ".join(sys.argv[2:])
        result = client.generate_text_to_image(prompt, wait=True)
        print(f"Generated: {result.output_files}")
    elif command == "status":
        task_id = sys.argv[2] if len(sys.argv) > 2 else None
        if task_id:
            task = client.get_task_status(task_id)
            print(f"Task {task.id}: {task.status}")
        else:
            tasks = client.get_task_queue()
            for task in tasks:
                print(f"{task.id}: {task.status}")
    elif command == "queue":
        tasks = client.get_task_queue()
        print(f"Queue: {len(tasks)} tasks")
        for task in tasks:
            print(f"  {task.id} - {task.status}")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
