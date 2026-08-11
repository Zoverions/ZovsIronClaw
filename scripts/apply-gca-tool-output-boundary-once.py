from pathlib import Path


API_PATH = Path("apps/gca-service/api_server.py")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


def main() -> None:
    api = API_PATH.read_text()

    api = replace_once(
        api,
        'EXPERIMENTAL_RUNTIME_ENABLED = env_flag("GCA_ENABLE_EXPERIMENTAL_RUNTIME")\n',
        'EXPERIMENTAL_RUNTIME_ENABLED = env_flag("GCA_ENABLE_EXPERIMENTAL_RUNTIME")\n'
        'EXPERIMENTAL_TOOL_CALLS_ENABLED = env_flag("GCA_ENABLE_EXPERIMENTAL_TOOL_CALLS")\n',
        "tool-call runtime flag",
    )

    chat_old = '''            if not approved:\n                return _openai_response_text(\n                    f"🛡️ [MORAL INTERVENTION] I cannot execute {tool_call_data['name']}. Reason: {reason}",\n                    req.model\n                )\n\n            # Approved - Format as OpenAI Tool Call\n            return _openai_response_tool_call(\n'''
    chat_new = '''            if not approved:\n                return _openai_response_text(\n                    f"🛡️ [MORAL INTERVENTION] I cannot execute {tool_call_data['name']}. Reason: {reason}",\n                    req.model\n                )\n\n            if not EXPERIMENTAL_TOOL_CALLS_ENABLED:\n                return _openai_response_text(\n                    f"[GCA ADVISORY] Suggested tool call '{tool_call_data['name']}' was suppressed. "\n                    "Set GCA_ENABLE_EXPERIMENTAL_TOOL_CALLS=1 only for isolated evaluation; "\n                    "GCA policy scores are not execution authorization.",\n                    req.model\n                )\n\n            # Explicit experimental opt-in only; caller policy remains authoritative.\n            return _openai_response_tool_call(\n'''
    api = replace_once(api, chat_old, chat_new, "chat tool-call suppression")

    reason_old = '''            if not approved:\n                reflective_logger.log("warn", f"MORAL VETO: {reason}")\n                return ReasoningResponse(\n                    status="BLOCKED",\n                    content=f"🛡️ [ETHICAL INTERVENTION] Action blocked: {reason}",\n                    meta={"entropy_score": risk_score, "reason": reason}\n                )\n            \n            # Approved\n            signature = _generate_signature(detected_tool, req.user_id)\n            return ReasoningResponse(\n'''
    reason_new = '''            if not approved:\n                reflective_logger.log("warn", f"MORAL VETO: {reason}")\n                return ReasoningResponse(\n                    status="BLOCKED",\n                    content=f"🛡️ [ETHICAL INTERVENTION] Action blocked: {reason}",\n                    meta={"entropy_score": risk_score, "reason": reason}\n                )\n\n            if not EXPERIMENTAL_TOOL_CALLS_ENABLED:\n                tool_name = str(detected_tool.get("name", "unknown"))\n                return ReasoningResponse(\n                    status="SUCCESS",\n                    content=(\n                        f"{response_text}\\n\\n[GCA ADVISORY] Suggested tool call '{tool_name}' was suppressed. "\n                        "Set GCA_ENABLE_EXPERIMENTAL_TOOL_CALLS=1 only for isolated evaluation; "\n                        "GCA policy scores are not execution authorization."\n                    ),\n                    meta={\n                        "intent": intent,\n                        "risk_score": risk_score,\n                        "causal_flow": causal_metrics,\n                        "response_causal_flow": response_metrics,\n                        "tool_suggestion_suppressed": tool_name,\n                    }\n                )\n\n            # Explicit experimental opt-in only. The signature is an experiment, not authorization.\n            signature = _generate_signature(detected_tool, req.user_id)\n            return ReasoningResponse(\n'''
    api = replace_once(api, reason_old, reason_new, "reason tool-call suppression")

    API_PATH.write_text(api)


if __name__ == "__main__":
    main()
