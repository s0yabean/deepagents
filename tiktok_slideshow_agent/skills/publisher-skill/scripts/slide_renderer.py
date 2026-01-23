"""
Slide Renderer - Non-blocking slide rendering with URL download support.
Handles Playwright subprocess management with timeout and cleanup.
"""

import asyncio
import os
import sys
import json
import tempfile
from typing import Optional, Dict, Any
from pathlib import Path


class SlideRenderer:
    """Handles slide rendering with async subprocess management."""

    def __init__(self, fonts_dir: Optional[str] = None, timeout_seconds: int = 90):
        self.fonts_dir = fonts_dir or "fonts"
        self.timeout_seconds = timeout_seconds
        self.worker_script = self._find_worker_script()

    def _find_worker_script(self) -> Optional[str]:
        """Find the render_worker.py script."""
        # Try relative paths from common locations
        possible_paths = [
            "tiktok_slideshow_agent/tools/render_worker.py",
            "tools/render_worker.py",
            "../tools/render_worker.py",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # Fallback - assume it's in the same directory as this script
        return "render_worker.py"

    async def render_slide(
        self,
        text: str,
        image_path: str,
        slide_number: int,
        output_dir: Optional[str] = None,
    ) -> str:
        """
        Render a single slide with timeout and error handling.
        Returns the path to the rendered image.
        """
        try:
            return await asyncio.wait_for(
                self._render_slide_internal(text, image_path, slide_number, output_dir),
                timeout=self.timeout_seconds,
            )
        except asyncio.TimeoutError:
            raise Exception(
                f"Slide rendering timed out after {self.timeout_seconds}s for slide {slide_number}"
            )
        except Exception as e:
            raise Exception(
                f"Slide rendering failed for slide {slide_number}: {str(e)}"
            )

    async def _render_slide_internal(
        self,
        text: str,
        image_path: str,
        slide_number: int,
        output_dir: Optional[str] = None,
    ) -> str:
        """Internal rendering implementation."""
        # Prepare slide data
        slide_data = {
            "text": text,
            "image_path": image_path,
            "slide_number": slide_number,
        }

        # Determine output path
        target_dir = output_dir or "output"
        os.makedirs(target_dir, exist_ok=True)
        output_filename = f"slide_{slide_number}.png"
        output_path = os.path.join(target_dir, output_filename)

        # Launch subprocess
        if not self.worker_script:
            raise Exception("Worker script not found")

        process = await asyncio.create_subprocess_exec(
            sys.executable,
            self.worker_script,
            json.dumps(slide_data),
            output_path,
            self.fonts_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Wait for completion
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            output = stdout.decode().strip()
            if output.startswith("SUCCESS:"):
                rendered_path = output.replace("SUCCESS:", "")
                if os.path.exists(rendered_path):
                    return rendered_path
                else:
                    raise Exception(f"Rendered file not found: {rendered_path}")
            else:
                raise Exception(f"Worker output unexpected: {output}")
        else:
            error_msg = stderr.decode().strip()
            raise Exception(
                f"Worker failed with code {process.returncode}: {error_msg}"
            )

    async def render_slides_batch(
        self, slides: list, output_dir: Optional[str] = None, max_concurrent: int = 3
    ) -> list:
        """
        Render multiple slides concurrently with limited parallelism.
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []

        async def render_with_semaphore(slide_data):
            async with semaphore:
                return await self.render_slide(
                    slide_data["text"],
                    slide_data["image_path"],
                    slide_data["slide_number"],
                    output_dir,
                )

        tasks = [render_with_semaphore(slide) for slide in slides]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Return error placeholder instead of failing entire batch
                final_results.append(
                    f"ERROR: Slide {slides[i]['slide_number']} - {str(result)}"
                )
            else:
                final_results.append(result)

        return final_results


async def render_slide_non_blocking(
    text: str,
    image_path: str,
    slide_number: int,
    output_dir: Optional[str] = None,
    fonts_dir: Optional[str] = None,
    timeout_seconds: int = 90,
) -> str:
    """
    Main entry point for non-blocking slide rendering.
    Compatible with existing tool interface.
    """
    renderer = SlideRenderer(fonts_dir, timeout_seconds)
    return await renderer.render_slide(text, image_path, slide_number, output_dir)


async def render_slides_batch_non_blocking(
    slides: list,
    output_dir: Optional[str] = None,
    max_concurrent: int = 3,
    timeout_seconds: int = 90,
) -> list:
    """
    Render multiple slides concurrently.
    """
    renderer = SlideRenderer(timeout_seconds=timeout_seconds)
    return await renderer.render_slides_batch(slides, output_dir, max_concurrent)
