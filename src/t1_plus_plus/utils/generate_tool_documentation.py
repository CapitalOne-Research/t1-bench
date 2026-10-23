import inspect

from pydantic import BaseModel


def generate_tools_documentation(tools: list[callable]) -> str:
    """
    Takes a list of tool functions and generates a comprehensive string representation
    of their input schemas, output schemas, and docstrings.
    """
    documentation_blocks = []

    for tool in tools:
        tool_name = tool.__name__

        # 1. Extract the full docstring (Description, Examples, Returns)
        raw_docstring = inspect.getdoc(tool)
        docstring = raw_docstring if raw_docstring else "No description provided."

        # 2. Inspect the function signature to find the Pydantic models
        sig = inspect.signature(tool)
        input_model = None
        output_model = sig.return_annotation

        # Find the input model (looking for the **kwargs annotated with a BaseModel)
        for name, param in sig.parameters.items():
            if param.kind == inspect.Parameter.VAR_KEYWORD and issubclass(
                param.annotation, BaseModel
            ):
                input_model = param.annotation
                break
            # Fallback if it's passed directly instead of **kwargs
            elif issubclass(param.annotation, BaseModel):
                input_model = param.annotation
                break

        # 3. Build the formatted string
        doc_parts = [
            f"### Tool: `{tool_name}`\n",
            f"**Docstring / Examples:**\n```text\n{docstring}\n```\n",
        ]

        # --- 4. Process Input Schema ---
        doc_parts.append("**Input Schema:**")
        if input_model and issubclass(input_model, BaseModel):
            for field_name, field_info in input_model.model_fields.items():
                # Clean up type annotation string for readability (e.g., typing.Optional[typing.List[str]] -> Optional[List[str]])
                type_str = str(field_info.annotation).replace("typing.", "")

                # Check if the field is mandatory
                req_status = "Mandatory" if field_info.is_required() else "Optional"

                # Extract description
                desc = field_info.description or "No description provided."

                # Extract default value (if any)
                default_val = ""
                if not field_info.is_required() and field_info.default is not None:
                    default_val = f" (Default: {field_info.default})"

                doc_parts.append(
                    f"- **{field_name}** `{type_str}` [{req_status}]: {desc}{default_val}"
                )
        else:
            doc_parts.append("- No Pydantic input model found.")

        # --- 5. Process Output Schema ---
        doc_parts.append("\n**Output Schema:**")
        if (
            output_model
            and inspect.isclass(output_model)
            and issubclass(output_model, BaseModel)
        ):
            for field_name, field_info in output_model.model_fields.items():
                type_str = str(field_info.annotation).replace("typing.", "")
                desc = field_info.description or "No description provided."
                doc_parts.append(f"- **{field_name}** `{type_str}`: {desc}")
        else:
            doc_parts.append("- No Pydantic output model found.")

        # Add a separator between tools
        doc_parts.append("\n" + "=" * 60 + "\n")

        documentation_blocks.append("\n".join(doc_parts))

    return "\n".join(documentation_blocks)
