"""activegraph.packs.<pack_name> — brief description.

Replace this docstring with a description of what this pack does,
what domain it covers, and what packs it requires/integrates with.

Usage:
    from activegraph import Runtime, Graph
    from packs.<pack_name> import pack, <Name>Settings

    rt = Runtime(Graph(), llm_provider=my_provider)
    rt.load_pack(pack, settings=<Name>Settings(...))
    rt.run_goal("...")
"""

from __future__ import annotations

from pathlib import Path

from activegraph.packs import Pack, PackPolicy, load_prompts_from_dir

from .behaviors import BEHAVIORS
from .object_types import OBJECT_TYPES, RELATION_TYPES
from .settings import TemplateSettings
from .tools import TOOLS

_PROMPTS_DIR = Path(__file__).parent / "prompts"

pack = Pack(
    name="template",
    version="0.1.0",
    description="Replace this with a one-sentence description of this pack.",
    object_types=OBJECT_TYPES,
    relation_types=RELATION_TYPES,
    behaviors=BEHAVIORS,
    tools=TOOLS,
    policies=[
        # Add PackPolicy objects here if needed.
        # Example:
        # PackPolicy(name="write_approval", requires_approval=("artifact",)),
    ],
    prompts=load_prompts_from_dir(_PROMPTS_DIR) if _PROMPTS_DIR.exists() else (),
    settings_schema=TemplateSettings,
    # Declare dependencies:
    # requires=["core"],
    # integrates_with=["memory_gateway", "identity_auth"],
)

__all__ = ["pack", "TemplateSettings"]
