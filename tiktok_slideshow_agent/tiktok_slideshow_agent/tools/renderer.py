import os
import asyncio
from pathlib import Path
import json
import sys
from pathlib import Path

class PlaywrightRendererTool:
    _lock = asyncio.Lock()

    def __init__(self):
        # Calculate Base Path: tools -> tiktok_slideshow_agent -> PROJECT_ROOT
        current_file = Path(__file__).resolve()
        self.base_path = current_file.parent.parent.parent
        self.output_dir = self.base_path / "output"
        self.image_library_path = self.base_path / "image_library"
        self.fonts_dir = self.base_path / "fonts"
        self.worker_script = self.base_path / "tiktok_slideshow_agent/tools/render_worker.py"

    async def _ensure_dir(self):
        exists = await asyncio.to_thread(os.path.exists, self.output_dir)
        if not exists:
            await asyncio.to_thread(os.makedirs, self.output_dir)

    def _resolve_path(self, path: str) -> str:
        """Resolves virtual paths to real absolute paths."""
        if path.startswith("/image_library/"):
            resolved = path.replace("/image_library/", str(self.image_library_path) + "/")
            return resolved
        elif path.startswith("image_library/"):
            resolved = path.replace("image_library/", str(self.image_library_path) + "/")
            return resolved
        return path

    async def render_slide(self, slide_data: dict, project_config: dict, output_dir: str = None) -> str:
        """
        Generates HTML for the slide and captures a screenshot using a subprocess worker.
        Returns the path to the generated image.
        """
        async with self._lock:
            try:
                # 90s timeout for the subprocess
                return await asyncio.wait_for(self._render_internal(slide_data, project_config, output_dir), timeout=90.0)
            except asyncio.TimeoutError:
                print(f"ERROR: [render_slide] Subprocess timed out after 90s for slide {slide_data.get('slide_number')}")
                return f"Error: Rendering timed out for slide {slide_data.get('slide_number')}"
            except Exception as e:
                print(f"ERROR: [render_slide] failed: {str(e)}")
                return f"Error: {str(e)}"

    async def _render_internal(self, slide_data: dict, project_config: dict, output_dir: str = None) -> str:
        print(f"DEBUG: [render_slide] Starting subprocess render for slide {slide_data.get('slide_number')}")
        
        target_dir = output_dir if output_dir else self.output_dir
        exists = await asyncio.to_thread(os.path.exists, target_dir)
        if not exists:
            await asyncio.to_thread(os.makedirs, target_dir)
        
        # Resolve paths to absolute
        raw_image_path = slide_data["image_path"]
        image_path = self._resolve_path(raw_image_path)
        
        # Prepare data for worker
        worker_data = {
            "text": slide_data["text"],
            "image_path": image_path,
            "slide_number": slide_data["slide_number"]
        }
        
        output_filename = f"slide_{slide_data['slide_number']}.png"
        output_path = os.path.join(target_dir, output_filename)
        
        # Launch subprocess
        print(f"DEBUG: [render_slide] Launching worker: {self.worker_script}")
        
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            self.worker_script,
            json.dumps(worker_data),
            output_path,
            self.fonts_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            output = stdout.decode().strip()
            if output.startswith("SUCCESS:"):
                rendered_path = output.replace("SUCCESS:", "")
                print(f"DEBUG: [render_slide] Worker success: {rendered_path}")
                return rendered_path
            else:
                print(f"ERROR: [render_slide] Worker output unexpected: {output}")
                raise Exception(f"Worker failed with output: {output}")
        else:
            error_msg = stderr.decode().strip()
            print(f"ERROR: [render_slide] Worker failed with code {process.returncode}: {error_msg}")
            raise Exception(f"Worker failed: {error_msg}")
