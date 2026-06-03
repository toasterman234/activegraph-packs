"""Behaviors for the template pack.

Replace with your actual behaviors.

Behavior rules:
- @behavior signature: (name, on, where, view, creates, budget, priority)
  Put descriptions in the function docstring, NOT in @behavior.
- @llm_behavior additionally accepts: description, output_schema, tools, etc.
- Behaviors should NOT directly call other packs' functions — emit events instead.
"""

from __future__ import annotations

from activegraph.packs import behavior

from .object_types import ExampleObject
from .settings import TemplateSettings


@behavior(
    name="example_behavior",
    on=["goal.created"],
    creates=["example_object"],
)
def example_behavior(event, graph, ctx, *, settings: TemplateSettings):
    """Replace with a one-sentence description of what this behavior does and why.

    On: goal.created
    Creates: example_object
    """
    goal_text = event.payload.get("goal", "")
    if not goal_text:
        return

    graph.add_object(
        "example_object",
        ExampleObject(
            name="Example",
            description=f"Created from goal: {goal_text}",
        ).model_dump(),
    )


BEHAVIORS = [example_behavior]
