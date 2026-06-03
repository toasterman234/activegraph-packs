"""Object and relation types for the template pack.

Replace with your pack's actual types.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from activegraph.packs import ObjectType, RelationType


# ---------------------------------------------------- Pydantic schemas


class ExampleObject(BaseModel):
    """Replace with your actual object schema."""

    name: str
    description: str = ""
    metadata: dict = Field(default_factory=dict)


# ---------------------------------------------------- ObjectType list

OBJECT_TYPES = [
    ObjectType(
        name="example_object",
        schema=ExampleObject,
        description="Replace with a description of this object type.",
    ),
]


# ---------------------------------------------------- RelationType list

RELATION_TYPES = [
    # RelationType(
    #     name="relates_to",
    #     source_types=("example_object",),
    #     target_types=("example_object",),
    #     description="One example object relates to another.",
    # ),
]
