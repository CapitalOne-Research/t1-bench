import inspect
import json
import re
from typing import get_args, get_origin, get_type_hints

from pydantic import BaseModel


def pydantic_to_openai_schema(model: BaseModel) -> dict:
    """Convert a Pydantic model to OpenAI function calling schema"""
    properties = {}
    required = []

    for field_name, field_info in model.model_fields.items():
        # Get the field type
        field_type = field_info.annotation

        # Build property schema
        prop = {}

        # Handle Optional types
        origin = get_origin(field_type)
        if origin is not None:
            args = get_args(field_type)
            # For Optional (Union with None), get the actual type
            if len(args) == 2 and type(None) in args:
                field_type = args[0] if args[1] is type(None) else args[1]

        # Map Python types to JSON schema types
        if field_type == str:
            prop["type"] = "string"
        elif field_type == int:
            prop["type"] = "integer"
        elif field_type == float:
            prop["type"] = "number"
        elif field_type == bool:
            prop["type"] = "boolean"
        elif get_origin(field_type) == list:
            prop["type"] = "array"
            item_type = get_args(field_type)[0] if get_args(field_type) else str
            if item_type == str:
                prop["items"] = {"type": "string"}
            elif item_type == int:
                prop["items"] = {"type": "integer"}
        else:
            prop["type"] = "string"  # fallback

        # Add description if available
        if field_info.description:
            prop["description"] = field_info.description

        properties[field_name] = prop

        # Track required fields
        if field_info.is_required():
            required.append(field_name)

    schema = {"type": "object", "properties": properties}

    if required:
        schema["required"] = required

    return schema


def convert_tools_to_openai_format(tools: dict[str, callable]) -> list[dict]:
    """
    Convert a list of Pydantic-based tool functions into OpenAI tool calling format
    """
    openai_tools = []

    for tool_name, tool in tools.items():
        tool_name = tool.__name__

        # Extract docstring
        raw_docstring = inspect.getdoc(tool)
        description = raw_docstring if raw_docstring else f"Call {tool_name}"

        # Get function signature
        sig = inspect.signature(tool)
        input_model = None

        # Find the input Pydantic model from type annotations
        for name, param in sig.parameters.items():
            if param.annotation != inspect.Parameter.empty:
                try:
                    if issubclass(param.annotation, BaseModel):
                        input_model = param.annotation
                        break
                except TypeError:
                    continue

        # If no model found in signature (e.g. **kwargs), inspect function
        # source for ModelName.model_validate(...) pattern
        if input_model is None:
            try:
                source = inspect.getsource(tool)
                match = re.search(r'(\w+)\.model_validate\(', source)
                if match:
                    model_name = match.group(1)
                    # Look up the model class in the function's global scope
                    func_globals = tool.__globals__ if hasattr(tool, '__globals__') else {}
                    candidate = func_globals.get(model_name)
                    if candidate is not None:
                        try:
                            if issubclass(candidate, BaseModel):
                                input_model = candidate
                        except TypeError:
                            pass
            except (OSError, TypeError):
                pass

        # Build the OpenAI function schema
        if input_model:
            parameters_schema = pydantic_to_openai_schema(input_model)
        else:
            parameters_schema = {"type": "object", "properties": {}}

        openai_tool = {
            "type": "function",
            "function": {
                "name": tool_name,
                "description": description,
                "parameters": parameters_schema,
            },
        }

        openai_tools.append(openai_tool)

    return openai_tools
