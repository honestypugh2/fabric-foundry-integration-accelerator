import pytest

from fabric_foundry_accelerator.api.app import openapi_document
from fabric_foundry_accelerator.api.typescript import (
    UnsupportedSchemaError,
    render_type,
    render_typescript,
    type_name,
)


@pytest.mark.parametrize(
    ("schema", "expected"),
    [
        ({"$ref": "#/components/schemas/ExecutionEnvelope_object_"}, "ExecutionEnvelope_object_"),
        ({"const": "LIVE"}, '"LIVE"'),
        ({"const": None}, "null"),
        ({"const": True}, "true"),
        ({"enum": ["a", 1, False]}, '"a" | 1 | false'),
        ({"anyOf": [{"type": "string"}, {"type": "null"}]}, "string | null"),
        ({"oneOf": [{"type": "integer"}, {"type": "number"}]}, "number"),
        (
            {"allOf": [{"$ref": "#/x/A"}, {"anyOf": [{"$ref": "#/x/B"}, {"type": "null"}]}]},
            "A & (B | null)",
        ),
        ({"type": ["string", "null"]}, "string | null"),
        ({"type": "boolean"}, "boolean"),
        ({}, "unknown"),
        ({"type": "array"}, "readonly unknown[]"),
        (
            {"type": "array", "items": {"anyOf": [{"type": "string"}, {"type": "null"}]}},
            "readonly (string | null)[]",
        ),
        (
            {"type": "array", "prefixItems": [{"type": "string"}, {"type": "integer"}]},
            "readonly [string, number]",
        ),
        ({"type": "object"}, "Readonly<Record<string, unknown>>"),
        ({"type": "object", "additionalProperties": True}, "Readonly<Record<string, unknown>>"),
        (
            {"type": "object", "additionalProperties": {"type": "integer"}},
            "Readonly<Record<string, number>>",
        ),
    ],
)
def test_render_type(schema: dict[str, object], expected: str) -> None:
    assert render_type(schema) == expected


def test_object_properties_and_quoted_keys() -> None:
    rendered = render_type(
        {
            "type": "object",
            "properties": {"a": {"type": "string"}, "b-c": {"type": "integer"}},
            "required": ["a"],
        }
    )
    assert "readonly a: string;" in rendered and 'readonly "b-c"?: number;' in rendered


@pytest.mark.parametrize(
    "schema",
    [
        {"type": "decimal"},
        {"enum": [{"x": 1}]},
        {"anyOf": "nope"},
        {"anyOf": ["nope"]},
    ],
)
def test_unsupported_schemas_fail_loudly(schema: dict[str, object]) -> None:
    with pytest.raises(UnsupportedSchemaError):
        render_type(schema)


def test_type_names_are_valid_identifiers() -> None:
    assert type_name("ExecutionEnvelope[list[TableInfo]]") == "ExecutionEnvelope_list_TableInfo__"
    assert type_name("1abc") == "_1abc"


def test_document_renders_every_component() -> None:
    document = openapi_document()
    text = render_typescript(document)
    assert text.startswith("// GENERATED")
    assert "export interface LessonView {" in text and "export interface TablePreview {" in text
    assert "export type ExecutionLabel =" in text
    assert "*/\n" in text
    rendered = render_typescript(
        {"components": {"schemas": {"Doc": {"type": "string", "description": "Ends */ early"}}}}
    )
    assert "/** Ends * / early */" in rendered
