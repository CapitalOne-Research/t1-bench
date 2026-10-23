import json
import os
import random
import re
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
from pydantic import BaseModel
from model_config import get_model_config
from llm_client import get_llm_client, LLMClient

_RETRY_ATTEMPTS = 3
_RETRY_DELAY_SECONDS = 5


def _chat_with_retry(
    client, max_attempts=_RETRY_ATTEMPTS, delay=_RETRY_DELAY_SECONDS, **kwargs
):
    """Call client.chat.completions.create with retries on transient errors."""
    # Create a copy of kwargs so we can modify parameters safely during retries
    current_kwargs = dict(kwargs)

    for attempt in range(1, max_attempts + 1):
        try:
            return client.chat.completions.create(**current_kwargs)
        except Exception as exc:
            err_str = str(exc)

            # 1. Catch the specific Harmony Token Crash
            if "Unexpected token 200002" in err_str or "InternalServerError" in err_str:
                if attempt == max_attempts:
                    raise

                # Nudge the temperature up by 0.2 to break the deterministic token loop
                current_temp = current_kwargs.get("temperature", 0.0)
                new_temp = current_temp + 0.2
                current_kwargs["temperature"] = new_temp

                print(
                    f"   [WARN] Harmony parser crash hit (attempt {attempt}/{max_attempts}). Nudging temperature from {current_temp:.1f} to {new_temp:.1f}..."
                )
                time.sleep(2)
                continue

            # 2. Handle all other standard API errors
            if attempt == max_attempts:
                raise
            print(
                f"   [WARN] API call failed (attempt {attempt}/{max_attempts}): {exc}. Retrying in {delay}s..."
            )
            time.sleep(delay)


def _extract_and_parse_json(text: str) -> Tuple[Optional[dict], Optional[Exception]]:
    """
    Try to extract and parse a JSON block from model output.
    Tries fenced code block first, then bare outermost braces.
    Returns (parsed_dict, None) on success or (None, exception) on failure.
    """
    candidates = []
    # 1. Prefer content inside ```json ... ``` fences
    for m in re.finditer(r"```json\s*(.*?)\s*```", text, re.DOTALL):
        candidates.append(m.group(1).strip())
    # 2. Fall back to the outermost {...} span
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        candidates.append(m.group(0).strip())

    _VALID_ESCAPES = set('"\\bfnrtu/')

    def _fix_escapes(s: str) -> str:
        r"""Replace invalid JSON escape sequences like \e, \p with \\e, \\p."""
        result = []
        i = 0
        while i < len(s):
            ch = s[i]
            if ch == "\\" and i + 1 < len(s):
                nxt = s[i + 1]
                if nxt == "u":
                    # \uXXXX requires exactly 4 hex digits; if not, escape the backslash
                    hex_digits = s[i + 2 : i + 6]
                    if len(hex_digits) == 4 and all(
                        c in "0123456789abcdefABCDEF" for c in hex_digits
                    ):
                        result.append(ch)
                        result.append(nxt)
                        i += 2
                    else:
                        result.append("\\\\")
                        i += 1
                elif nxt in _VALID_ESCAPES:
                    result.append(ch)
                    result.append(nxt)
                    i += 2
                else:
                    # Escape the backslash so JSON can parse it
                    result.append("\\\\")
                    i += 1
            else:
                result.append(ch)
                i += 1
        return "".join(result)

    last_err = None
    for candidate in candidates:
        try:
            return json.loads(candidate), None
        except json.JSONDecodeError as e:
            last_err = e
            # Attempt repair 1: fix invalid escape sequences
            try:
                return json.loads(_fix_escapes(candidate)), None
            except Exception:
                pass
            # Attempt repair 2: truncate at the last valid position and
            # close any unclosed braces/brackets so json.loads can succeed.
            try:
                repaired = candidate[: e.pos]
                # Count unclosed structures
                depth_brace = repaired.count("{") - repaired.count("}")
                depth_bracket = repaired.count("[") - repaired.count("]")
                # Strip trailing partial token (comma, colon, partial string)
                repaired = re.sub(r"[,:\s]*$", "", repaired)
                repaired += "]" * depth_bracket + "}" * depth_brace
                return json.loads(repaired), None
            except Exception:
                pass
    return None, last_err


# ==========================================
# 1. SESSION MEMORY & CACHING EXECUTOR
# ==========================================

# Temporary buffer to map LLM string references to real data objects during a turn
session_result_memory = {}

# Tracks how many times each tool has been called this session (for indexed cache keys)
tool_call_counts: dict = {}

CACHE_TOOL_NAMES = {"save_to_cache", "get_results_from_cache"}


def execute_real_tool_with_caching(
    tool_name: str,
    tool_args: Dict[str, Any],
    tool_registry: Dict[str, Callable],
    filter_tool: str = None,
) -> str:
    global session_result_memory, tool_call_counts
    from t1_plus_plus.tools.general.cache import save_to_cache, get_results_from_cache

    print(f"\n[🔧 EXECUTING TOOL: {tool_name}]")
    sanitized_args = {k: v for k, v in tool_args.items() if v is not None}
    try:
        target_function = tool_registry[tool_name]
        result_obj = target_function(**sanitized_args)

        # STORE RESULTS & VERIFY SIZE ---
        if tool_name.startswith("search_") or tool_name.startswith("filter_"):
            count = len(
                getattr(
                    result_obj, "search_results", getattr(result_obj, "results", [])
                )
            )
            print(f"   ✅ [SUCCESS] {tool_name} returned {count} items.")

        # AUTO SAVE TO CACHE after every search/filter tool that returns results ---
        if (
            tool_name.startswith("search_") or tool_name.startswith("filter_")
        ) and result_obj is not None:
            base_key = f"{tool_name}_results"
            index = tool_call_counts.get(base_key, 0)
            tool_call_counts[base_key] = index + 1
            cache_key = f"{base_key}_{index}"
            session_result_memory[cache_key] = result_obj
            try:
                auto_summary = getattr(result_obj, "query_summary", None)
                serializable_args = {
                    k: (
                        json.loads(v.model_dump_json())
                        if isinstance(v, BaseModel)
                        else v
                    )
                    for k, v in sanitized_args.items()
                }
                prior_search_query = (
                    json.dumps(serializable_args) if serializable_args else None
                )
                save_to_cache(
                    key=cache_key,
                    value=result_obj,
                    summary=auto_summary,
                    prior_search_query=prior_search_query,
                )
            except Exception as e:
                print(f"   ⚠️ [AUTO CACHE SAVE] Could not save '{cache_key}': {e}")

        if isinstance(result_obj, BaseModel):
            return result_obj.model_dump_json()
        return json.dumps(result_obj)

    except Exception as e:
        print(f"   ❌ Tool execution failed: {str(e)}")
        return json.dumps({"error": str(e)})


# ==========================================
# 2. SIMULATION LOOP
# ==========================================
def _check_conversation_end(
    conversation: list, user_policy: str, llm_client: LLMClient
) -> bool:
    """
    LLM-as-judge: returns True if the user has completed their goal and the
    conversation should end.
    """
    history_text = ""
    for msg in conversation:
        role = msg.get("role", "unknown")
        content = msg.get("content") or ""
        if role == "tool":
            continue  # skip raw tool payloads to keep the prompt concise
        if msg.get("tool_calls"):
            tool_names = ", ".join(tc["name"] for tc in msg["tool_calls"])
            history_text += f"[ASSISTANT called tools: {tool_names}]\n"
        elif content.strip():
            history_text += f"[{role.upper()}] {content.strip()}\n"

    prompt = f"""You are evaluating whether a simulated customer-service conversation should end.

USER GOAL (from user policy):
{user_policy}

CONVERSATION SO FAR:
{history_text.strip()}

Has the user fully completed their stated goal AND naturally concluded the conversation (e.g. said thanks/bye, or confirmed the booking/order/reservation is done)? If they still asked questions, don't end the conversation.

Reply with a JSON object ONLY — no other text:
{{"should_end": true or false, "reason": "one-sentence explanation"}}"""

    try:
        resp = llm_client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        raw = resp.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        result = json.loads(raw)
        should_end = bool(result.get("should_end", False))
        reason = result.get("reason", "")
        if should_end:
            print(f"   [JUDGE] Conversation should end: {reason}")
        return should_end
    except Exception as e:
        print(f"   [JUDGE] Error checking conversation end: {e}")
        return False


def run_simulation(
    user_policy: str,
    assistant_policy: str,
    assistant_initial_greeting: str,
    openai_format_tools: List[dict],
    tool_registry: Dict[str, Callable],
    domain_name: str,
    conversation_id: int,
    max_turns: int = 12,
    filter_tool: str = None,
    policy_loader: Optional[Callable] = None,
    user_model_name: str = "google/gemma-4-31B-it",
    assistant_model_name: str = "openai/gpt-oss-120b",
    save: bool = False,
    output_dir: Optional[str] = None,
    domain_log: Optional[list] = None,
    domains: Optional[list] = None,
):
    from t1_plus_plus.tools.general.cache import reset_cache

    reset_cache()

    user_client = get_llm_client(user_model_name)
    assistant_client = get_llm_client(assistant_model_name)

    _mcfg = get_model_config(assistant_model_name)
    print(f"MODEL CONFIGURATION: {_mcfg}")
    print(
        f"USER PROVIDER: {user_client.provider} | ASSISTANT PROVIDER: {assistant_client.provider}"
    )

    user_history = []
    assistant_history = []

    user_total_tokens = 0
    assistant_total_tokens = 0

    tools = []
    cache_log = []
    dataset_record = {
        "conversation_id": conversation_id,
        "domain": domains if domains is not None else [],
        "user_policy": user_policy,
        "assistant_policy": assistant_policy,
        "conversation": [],
        "tools": tools,
        "cache": cache_log,
        "domains": domain_log if domain_log is not None else [],
    }

    # KICKOFF
    dataset_record["conversation"].append(
        {"role": "assistant", "content": assistant_initial_greeting}
    )
    assistant_history.append(
        {"role": "assistant", "content": assistant_initial_greeting}
    )
    user_history.append({"role": "user", "content": assistant_initial_greeting})

    print(f"👤 USER POLICY:\n{user_policy}\n")
    print(f"🤖 AGENT POLICY:\n{assistant_policy}\n")
    print(f"🤖 ASSISTANT:\n{assistant_initial_greeting}\n")

    temperature = _mcfg["temperature"]
    extra_kwargs = _mcfg["extra_kwargs"]

    def _strip_special_tokens(text: str) -> str:
        """Remove special/control tokens that cause server-side tokenizer errors."""
        # <|...|> style tokens (e.g. <|begin_of_text|>, <|im_start|>, <|eot_id|>)
        text = re.sub(r"<\|[^|]*\|>", "", text)
        # Numeric token IDs in angle brackets (e.g. <200002>, <|200006|>)
        text = re.sub(r"<\|?\d+\|?>", "", text)
        # <im_start>, <im_end> and similar angle-bracket special tokens
        text = re.sub(r"</?im_(start|end|sep)>", "", text)
        # Llama/Mistral-style instruction tokens
        text = re.sub(r"\[/?INST\]", "", text)
        text = re.sub(r"<</?SYS>>", "", text)
        # BOS/EOS tokens
        text = re.sub(r"</?s>", "", text)
        # Gemma-style turn tokens
        text = re.sub(r"<start_of_turn>", "", text)
        text = re.sub(r"<end_of_turn>", "", text)
        text = re.sub(r"<bos>", "", text)
        text = re.sub(r"<eos>", "", text)
        return text

    def _clean_unicode(text: str) -> str:
        """Replace unusual Unicode spaces and invisible characters with ASCII equivalents."""
        # Narrow no-break space (U+202F) and non-breaking space (U+00A0) → regular space
        text = text.replace("\u202f", " ").replace("\u00a0", " ")
        # Zero-width spaces / joiners / non-joiners
        text = text.replace("\u200b", "").replace("\u200c", "").replace("\u200d", "")
        # Left-to-right / right-to-left marks
        text = text.replace("\u200e", "").replace("\u200f", "")
        # Soft hyphen
        text = text.replace("\u00ad", "")
        # BOM
        text = text.replace("\ufeff", "")
        return text

    def _safe_history_str(history):
        lines = []
        for msg in history:
            content = msg.get("content", "")
            # Strip JSON code blocks (tool calls / structured responses) so the
            # user-simulator model never sees raw JSON that can confuse the tokenizer.
            content = re.sub(r"```json.*?```", "", content, flags=re.DOTALL).strip()
            # Remove special token delimiter patterns that cause server-side
            # InternalServerError 500 with "Unexpected token" messages.
            content = _strip_special_tokens(content)
            if content:
                role = msg["role"].upper()
                lines.append(f"{role}: {content}")
        return "\n\n".join(lines)

    safe_user_policy = _strip_special_tokens(user_policy)
    safe_assistant_policy = _strip_special_tokens(assistant_policy)

    turn_count = 0
    while turn_count < max_turns:
        turn_count += 1
        print(f"\n--- Turn {turn_count} of {max_turns} ---")

        user_prompt = [
            {"role": "system", "content": safe_user_policy},
            {
                "role": "user",
                "content": f"CHAT HISTORY\n{_safe_history_str(user_history)}\n\nGenerate your response based on the context above as a customer.",
            },
        ]

        # A. USER TURN
        user_resp = user_client.chat(
            messages=user_prompt,
            temperature=temperature,
            **extra_kwargs,
        )
        user_total_tokens += user_resp.usage.total_tokens if user_resp.usage else 0
        user_text = _clean_unicode(
            _strip_special_tokens(user_resp.choices[0].message.content)
        )
        print(f"👤 USER:\n{user_text}")
        print("=== END OF USER TURN ===")
        user_history.append({"role": "assistant", "content": user_text})
        assistant_history.append({"role": "user", "content": user_text})
        dataset_record["conversation"].append({"role": "user", "content": user_text})

        # B. ASSISTANT TURN
        # Phase 1: tool loop — keep calling tools until no more tool calls are emitted
        # Phase 2: generate final response to the user

        global session_result_memory, tool_call_counts
        session_result_memory = {}
        tool_call_counts = {}

        tools_context = json.dumps(openai_format_tools, indent=2)
        any_tools_called = False
        tools_called_this_turn_list = []
        response_text = None

        # Re-classify domains using the latest user message + full chat history
        if policy_loader is not None:
            loader_result = policy_loader(user_text, assistant_history)
            if isinstance(loader_result, tuple):
                effective_policy = _strip_special_tokens(loader_result[0])
                tools_context = json.dumps(loader_result[1], indent=2)
            else:
                effective_policy = _strip_special_tokens(loader_result)
        else:
            effective_policy = safe_assistant_policy

        tool_loop_count = 0

        while tool_loop_count < 5:
            tool_loop_count += 1

            from t1_plus_plus.tools.general.cache import get_cache_for_current_turn

            cache_summary = get_cache_for_current_turn()
            cache_section = (
                f"\nCURRENT CACHE SUMMARY\n{json.dumps(cache_summary, indent=2, default=str)}\n"
                if cache_summary
                else "\nCURRENT CACHE SUMMARY\n(empty)\n"
            )
            tools_called_section = (
                f"\nTOOLS ALREADY CALLED THIS TURN: {', '.join(tools_called_this_turn_list)}\n"
                if tools_called_this_turn_list
                else "\nTOOLS ALREADY CALLED THIS TURN: (none)\n"
            )

            assistant_prompt = [
                {"role": "system", "content": effective_policy},
                {
                    "role": "user",
                    "content": f"""AVAILABLE TOOLS (ONLY call the tools below)
{tools_context}
{cache_section}{tools_called_section}
CHAT HISTORY
{_safe_history_str(assistant_history)}

Generate your response based on the context above as a customer service agent.
Review the tools already called this turn and their results in the cache before deciding whether another tool call is needed.
Only call a tool if it is genuinely required and has not already produced the needed information.
If you have all the information needed to respond to the user, output a response directly.
If you need to call a tool, output ONLY a JSON block in this exact format and nothing else:
```json
{{"tool_calls": [{{"name": "<tool_name>", "arguments": {{...}}}}]}}
```
If no tool call is needed, output:
```json
{{"response": "<response>"}}
```""",
                },
            ]
            asst_resp = assistant_client.chat(
                messages=assistant_prompt,
                temperature=temperature,
                **extra_kwargs,
            )
            assistant_total_tokens += (
                asst_resp.usage.total_tokens if asst_resp.usage else 0
            )
            assistant_text = asst_resp.choices[0].message.content or ""

            # Parse tool calls from JSON output
            tool_calls = []

            def _apply_parsed(parsed_dict):
                nonlocal response_text
                if "tool_calls" in parsed_dict:
                    for i, tc in enumerate(parsed_dict["tool_calls"]):
                        tool_calls.append(
                            {
                                "id": f"call_{turn_count}_{tool_loop_count}_{i}",
                                "name": tc["name"],
                                "args": tc.get("arguments", {}),
                            }
                        )
                elif "response" in parsed_dict:
                    response_text = parsed_dict["response"]

            parsed, parse_err = _extract_and_parse_json(assistant_text)
            if parsed is not None:
                _apply_parsed(parsed)
            elif parse_err is not None:
                print(f"   [WARN] Failed to parse tool call JSON: {parse_err}")

            # Strip any cache-related tool calls the LLM may have generated —
            # cache operations are handled automatically by the executor.
            tool_calls = [tc for tc in tool_calls if tc["name"] not in CACHE_TOOL_NAMES]

            if not tool_calls:
                break

            print(f"🤖 ASSISTANT (TOOLS):\n{assistant_text}")
            any_tools_called = True

            for tc in tool_calls:
                print(
                    f"[TOOL CALL] turn={turn_count} tool={tc['name']} args={tc['args']}"
                )
                tools.append(
                    {
                        "turn": turn_count,
                        "tool_name": tc["name"],
                        "parameters": tc["args"],
                    }
                )

            msg_record = {"role": "assistant", "content": ""}
            msg_record["tool_calls"] = tool_calls
            dataset_record["conversation"].append(msg_record)

            for tc in tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]
                tools_called_this_turn_list.append(tool_name)
                tool_result_content = execute_real_tool_with_caching(
                    tool_name, tool_args, tool_registry, filter_tool=filter_tool
                )
                tool_result_content = _clean_unicode(tool_result_content)
                assistant_history.append(
                    {
                        "role": "user",
                        "content": f"[Tool result for {tool_name}]\n{tool_result_content}",
                    }
                )
                dataset_record["conversation"].append(
                    {
                        "role": "tool",
                        "tool_name": tool_name,
                        "tool_call_id": tc["id"],
                        "content": tool_result_content,
                    }
                )

        # Phase 2: generate the assistant's final response to the user
        from t1_plus_plus.tools.general.cache import get_cache_for_current_turn

        cache_summary = get_cache_for_current_turn()
        cache_section = (
            f"\nCURRENT CACHE SUMMARY\n{json.dumps(cache_summary, indent=2, default=str)}\n"
            if cache_summary
            else "\nCURRENT CACHE SUMMARY\n(empty)\n"
        )
        if cache_summary:
            cache_log.append({"turn": turn_count, "cache_object": cache_summary})

        if any_tools_called:
            post_tool_prompt = [
                {"role": "system", "content": effective_policy},
                {
                    "role": "user",
                    "content": f"""CHAT HISTORY
{_safe_history_str(assistant_history)}
{cache_section}
Now respond to the user based on those results as a customer service agent. Do not generate any tool calls.
Output your response as:
```json
{{"response": "<response>"}}
```""",
                },
            ]
            post_tool_resp = assistant_client.chat(
                messages=post_tool_prompt,
                temperature=temperature,
                **extra_kwargs,
            )
            assistant_total_tokens += (
                post_tool_resp.usage.total_tokens if post_tool_resp.usage else 0
            )
            post_tool_text = post_tool_resp.choices[0].message.content or ""
            post_parsed, _ = _extract_and_parse_json(post_tool_text)
            final_response = _clean_unicode(
                post_parsed.get("response", post_tool_text)
                if post_parsed is not None
                else post_tool_text
            )
            print(f"🤖 ASSISTANT (POST-TOOLS):\n{final_response}")
        else:
            final_response = _clean_unicode(
                response_text if response_text is not None else assistant_text
            )
            print(f"🤖 ASSISTANT (RESPONSE):\n{final_response}")

        print("=== END OF ASSISTANT TURN ===")
        assistant_history.append({"role": "assistant", "content": final_response})
        dataset_record["conversation"].append(
            {"role": "assistant", "content": final_response}
        )

        # LLM-as-judge: check whether the user has completed their goal
        if _check_conversation_end(
            dataset_record["conversation"], user_policy, user_client
        ):
            break

        user_history.append(
            {
                "role": "user",
                "content": f"[History from previous turn]\n{_strip_special_tokens(final_response)}\n\nGenerate your response based on the context above as a customer.",
            }
        )

    if turn_count >= max_turns:
        print(f"\n[🛑 Simulation reached the {max_turns}-turn limit.]")

    print("\n=== SIMULATION COMPLETE ===")

    session_total_tokens = user_total_tokens + assistant_total_tokens
    print(f"\n📊 SESSION TOKEN USAGE:")
    print(f"   - User Agent: {user_total_tokens} tokens")
    print(f"   - Assistant Agent: {assistant_total_tokens} tokens")
    print(f"   - TOTAL: {session_total_tokens} tokens")

    dataset_record["metadata"] = {
        "total_tokens_used": session_total_tokens,
        "user_agent_tokens": user_total_tokens,
        "assistant_agent_tokens": assistant_total_tokens,
        "turns_completed": turn_count,
    }

    def pydantic_safe_serializer(obj):
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    if save:
        target_dir = (
            output_dir or f"simulated_conversation/{assistant_model_name}/{domain_name}"
        )
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, f"{domain_name}_{conversation_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(
                dataset_record,
                f,
                indent=4,
                ensure_ascii=False,
                default=pydantic_safe_serializer,
            )
        print(f"\n💾 Dataset successfully saved to: {file_path}")
    else:
        print("\n[SAVE SKIPPED] Conversation not written to disk.")
