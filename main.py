import importlib.util
from pathlib import Path
from dotenv import load_dotenv
from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse
from kirak import create_kirak_app

load_dotenv()

# Every setting (modules, CORS, routes, assets_path, ...) is in kirak.json, which Kirak
# reads from the directory the app is started in: this one.


def on_kirak_ready(kirak):
    """
    Called after Kirak initialises but before routers are mounted.

    hooks/ -- CRUD lifecycle callbacks. Each file must expose register(kirak):

      def register(kirak):
          @kirak.on("orders").hook("after_create")
          async def on_order_created(result):
              ...
              return result

    custom/ -- custom HTTP endpoints. Each file must expose register(kirak):

      from fastapi import APIRouter

      router = APIRouter()

      @router.post("/custom-endpoint")
      async def custom_endpoint(): ...

      def register(kirak):
          kirak.app.include_router(router)
    """
    hooks_dir = Path(__file__).parent / "hooks"
    if hooks_dir.exists():
        for hook_file in sorted(hooks_dir.glob("*.py")):
            if hook_file.name.startswith("_"):
                continue
            spec = importlib.util.spec_from_file_location(hook_file.stem, hook_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "register") and callable(module.register):
                module.register(kirak)

    api_dir = Path(__file__).parent / "custom"
    if api_dir.exists():
        for api_file in sorted(api_dir.glob("*.py")):
            if api_file.name.startswith("_"):
                continue
            spec = importlib.util.spec_from_file_location(api_file.stem, api_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "register") and callable(module.register):
                module.register(kirak)

    # Task files self-register via @kirak.scheduler.task() / @kirak.scheduler.cron()
    # at import time. kirak is injected as a module-level global so decorators resolve.
    tasks_dir = Path(__file__).parent / "tasks"
    if tasks_dir.exists():
        for task_file in sorted(tasks_dir.glob("*.py")):
            if task_file.name.startswith("_"):
                continue
            spec = importlib.util.spec_from_file_location(task_file.stem, task_file)
            module = importlib.util.module_from_spec(spec)
            module.kirak = kirak
            spec.loader.exec_module(module)

    # Serve assets so email template overrides and other static files are reachable.
    # Root follows assets_path from kirak.json; defaults to assets/ in project root.
    assets_dir = Path(kirak.manifest.assets_path or "assets").resolve()
    asset_router = APIRouter()

    @asset_router.get("/assets/{file_path:path}")
    async def serve_assets(file_path: str):
        file = (assets_dir / file_path).resolve()
        # ".." or an absolute path must not reach files outside the assets directory (.env, kirak.json)
        if file.is_relative_to(assets_dir) and file.is_file():
            return FileResponse(file)
        return JSONResponse({"error": "File not found"}, status_code=404)

    kirak.app.include_router(asset_router)


app = create_kirak_app(
    models_path="./models/",
    on_kirak_ready=on_kirak_ready,
)
