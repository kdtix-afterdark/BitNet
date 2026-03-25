"""Interactive UAT runner for broker chat conversations loaded from JSON."""

from __future__ import annotations

import argparse
import json
import re
import sys
import termios
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib import error, request


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


STOPWORDS = {
    "about",
    "after",
    "again",
    "also",
    "been",
    "before",
    "being",
    "both",
    "could",
    "from",
    "have",
    "just",
    "into",
    "just",
    "me",
    "my",
    "just",
    "like",
    "more",
    "most",
    "need",
    "onto",
    "only",
    "other",
    "part",
    "please",
    "same",
    "some",
    "than",
    "that",
    "them",
    "then",
    "they",
    "this",
    "those",
    "through",
    "our",
    "ours",
    "their",
    "there",
    "very",
    "what",
    "when",
    "with",
    "would",
    "you",
    "your",
    "yours",
    "can",
    "for",
    "its",
    "it's",
    "the",
    "and",
    "are",
    "was",
    "were",
    "who",
    "why",
    "how",
    "use",
    "using",
    "used",
    "one",
    "two",
    "three",
    "four",
    "five",
    "office",
    "just",
    "have",
    "has",
    "had",
    "will",
    "shall",
    "into",
    "from",
    "where",
    "which",
    "while",
    "turn",
    "word",
    "simple",
    "your",
}

CONTINUATION_MARKERS = (
    "add to",
    "continue",
    "earlier",
    "extend",
    "pick up",
    "previous",
    "remember",
    "same",
)


def derive_state_path(conversation_path: Path) -> Path:
    return conversation_path.with_suffix(".state.json")


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def post_json(base_url: str, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        f"{base_url.rstrip('/')}{path}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=300) as response:
        return json.loads(response.read().decode("utf-8"))


def get_json(base_url: str, path: str) -> Dict[str, Any]:
    req = request.Request(
        f"{base_url.rstrip('/')}{path}",
        headers={"Content-Type": "application/json"},
        method="GET",
    )
    with request.urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def create_session(
    base_url: str,
    conversation: Dict[str, Any],
) -> Dict[str, Any]:
    session_payload = dict(conversation.get("session", {}))
    return post_json(base_url, "/sessions", session_payload)


def print_block(title: str, body: str) -> None:
    print(f"\n=== {title} ===")
    print(body.rstrip())
    print("=" * (len(title) + 8))


def build_state(
    conversation_path: Path,
    base_url: str,
    session_response: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "conversation_file": str(conversation_path),
        "broker_url": base_url,
        "session_id": session_response["session_id"],
        "created_at": utc_now(),
        "next_turn_index": 0,
        "completed": False,
        "broker_turn_count": 0,
        "broker_message_count": 0,
        "broker_summary_char_count": 0,
        "broker_summarized_turn_count": 0,
        "external_turns_detected": 0,
        "last_broker_sync_at": None,
        "results": [],
    }


def managed_turn_count(state: Dict[str, Any]) -> int:
    return len(
        [
            item
            for item in state.get("results", [])
            if str(item.get("kind", "")).strip().lower() in {"scripted", "inserted"}
        ]
    )


def scripted_turn_count(state: Dict[str, Any]) -> int:
    return len(
        [
            item
            for item in state.get("results", [])
            if str(item.get("kind", "scripted")).strip().lower() == "scripted"
        ]
    )


def inserted_turn_count(state: Dict[str, Any]) -> int:
    return len(
        [
            item
            for item in state.get("results", [])
            if str(item.get("kind", "")).strip().lower() == "inserted"
        ]
    )


def skipped_turn_count(state: Dict[str, Any]) -> int:
    return len(
        [
            item
            for item in state.get("results", [])
            if str(item.get("kind", "")).strip().lower() == "skipped"
        ]
    )


def find_session_in_recovery(recovery_payload: Dict[str, Any], session_id: str) -> Dict[str, Any] | None:
    sessions = recovery_payload.get("sessions", [])
    for session in sessions:
        if session.get("session_id") == session_id:
            return dict(session)
    active_session = recovery_payload.get("active_session")
    if isinstance(active_session, dict) and active_session.get("session_id") == session_id:
        return dict(active_session)
    return None


def sync_state_with_broker(base_url: str, state: Dict[str, Any]) -> str | None:
    recovery = get_json(base_url, "/recovery/last")
    session = find_session_in_recovery(recovery, state["session_id"])
    if session is None:
        return "Session %s was not found in /recovery/last" % state["session_id"]

    broker_turn_count = int(session.get("turn_count", 0))
    broker_message_count = int(session.get("message_count", 0))
    broker_summary_char_count = int(session.get("summary_char_count", 0))
    broker_summarized_turn_count = int(session.get("summarized_turn_count", 0))
    external_turns = max(broker_turn_count - managed_turn_count(state), 0)

    state["broker_turn_count"] = broker_turn_count
    state["broker_message_count"] = broker_message_count
    state["broker_summary_char_count"] = broker_summary_char_count
    state["broker_summarized_turn_count"] = broker_summarized_turn_count
    state["external_turns_detected"] = external_turns
    state["last_broker_sync_at"] = utc_now()

    if external_turns > 0:
        return (
            "Detected %d out-of-band turn(s) in broker session %s. "
            "The sidecar tracks broker-managed scripted and inserted turns, while skipped turns stay local."
            % (external_turns, state["session_id"])
        )
    return None


def print_status(state: Dict[str, Any], conversation: Dict[str, Any]) -> None:
    turns = conversation.get("turns", [])
    print(
        "Session %s | next turn %d of %d | scripted turns=%d | inserted turns=%d | skipped turns=%d | broker turns=%d | external turns=%d | state file: %s"
        % (
            state["session_id"],
            state["next_turn_index"] + 1 if state["next_turn_index"] < len(turns) else len(turns),
            len(turns),
            scripted_turn_count(state),
            inserted_turn_count(state),
            skipped_turn_count(state),
            int(state.get("broker_turn_count", 0)),
            int(state.get("external_turns_detected", 0)),
            derive_state_path(Path(conversation["__path__"])),
        )
    )


def print_menu() -> None:
    print(
        "\nPress Enter to send the next turn, or choose: "
        "[h]=health [r]=recovery [b]=broker-session [s]=session [i]=insert turn [x]=skip turn [q]=quit"
    )


def discard_buffered_input() -> None:
    if not sys.stdin.isatty():
        return
    try:
        termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
    except termios.error:
        return


def record_turn_result(
    state: Dict[str, Any],
    *,
    kind: str,
    turn_index: int | None,
    prompt: str,
    response: Dict[str, Any],
    started_at: str,
) -> None:
    response_text = str(response.get("response", "")).strip()
    state["results"].append(
        {
            "kind": kind,
            "turn_index": turn_index,
            "prompt": prompt,
            "started_at": started_at,
            "completed_at": utc_now(),
            "response": response_text,
            "correlation_id": response.get("correlation_id"),
            "route_applied": response.get("route_applied"),
            "route_reason": response.get("route_reason"),
            "model_invoked": response.get("model_invoked"),
        }
    )


def record_skipped_turn(
    state: Dict[str, Any],
    *,
    turn_index: int,
    prompt: str,
) -> None:
    recorded_at = utc_now()
    state["results"].append(
        {
            "kind": "skipped",
            "turn_index": turn_index,
            "prompt": prompt,
            "original_scripted_prompt": prompt,
            "skip_note": "Skipped by UAT tester. Original scripted prompt preserved for review.",
            "started_at": recorded_at,
            "completed_at": recorded_at,
            "response": "",
            "correlation_id": None,
            "route_applied": False,
            "route_reason": "skipped_by_uat_tester",
            "model_invoked": False,
        }
    )


def topic_tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[A-Za-z0-9']+", text.lower())
        if len(token) >= 3 and token not in STOPWORDS
    }


def collect_result_tokens(results: List[Dict[str, Any]]) -> set[str]:
    tokens: set[str] = set()
    for result in results:
        tokens.update(topic_tokens(str(result.get("prompt", ""))))
        tokens.update(topic_tokens(str(result.get("response", ""))))
    return tokens


def format_token_sample(tokens: set[str]) -> str:
    if not tokens:
        return "none"
    return ", ".join(sorted(tokens)[:6])


def assess_inserted_prompt_risk(state: Dict[str, Any], prompt: str) -> str | None:
    lowered = prompt.strip().lower()
    referential = any(marker in lowered for marker in CONTINUATION_MARKERS)
    if not referential:
        return None

    results = list(state.get("results", []))
    if not results:
        return None

    prompt_tokens = topic_tokens(prompt)
    if not prompt_tokens:
        return None

    recent_results = results[-3:]
    older_results = results[:-3]
    recent_tokens = collect_result_tokens(recent_results)
    older_tokens = collect_result_tokens(older_results)

    recent_overlap = prompt_tokens & recent_tokens
    older_overlap = prompt_tokens & older_tokens

    if older_overlap and not recent_overlap:
        return (
            "This inserted prompt looks like it is continuing an older topic that is not present "
            "in the last few turns. Prompt anchors=%s | older anchors=%s | recent anchors=%s"
            % (
                format_token_sample(prompt_tokens),
                format_token_sample(older_overlap),
                format_token_sample(recent_tokens),
            )
        )
    if not recent_overlap:
        return (
            "This inserted prompt is continuity-dependent, but its topic words do not appear in "
            "the recent turns. Prompt anchors=%s | recent anchors=%s"
            % (
                format_token_sample(prompt_tokens),
                format_token_sample(recent_tokens),
            )
        )
    return None


def run_inserted_turn(
    base_url: str,
    state: Dict[str, Any],
    prompt: str,
) -> None:
    inserted_prompt = prompt.strip()
    if not inserted_prompt:
        print("Insert prompt is empty. Use: i <prompt>")
        return
    warning = assess_inserted_prompt_risk(state, inserted_prompt)
    if warning:
        print("\nWarning: %s" % warning)
        confirm = input("Press Enter to send anyway, or type c to cancel> ").strip().lower()
        if confirm == "c":
            print("Insert canceled.")
            return

    try:
        started_at = utc_now()
        print("\nSending inserted turn to broker...")
        print("Waiting for broker response. Keystrokes typed during the request will be ignored.")
        response = run_turn(base_url, state["session_id"], {"prompt": inserted_prompt})
        response_text = str(response.get("response", "")).strip()
        discard_buffered_input()
        print_block("Inserted Assistant Response", response_text or json.dumps(response, indent=2))
        record_turn_result(
            state,
            kind="inserted",
            turn_index=None,
            prompt=inserted_prompt,
            response=response,
            started_at=started_at,
        )
        warning = sync_state_with_broker(base_url, state)
        if warning:
            print("Warning: %s" % warning)
        print(
            "Inserted turn complete. Returning to scripted turn %d."
            % (state["next_turn_index"] + 1)
        )
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        print("Inserted turn failed with HTTP %s: %s" % (exc.code, details))
    except Exception as exc:  # noqa: BLE001
        print("Inserted turn failed: %s" % exc)


def handle_aux_command(command: str, base_url: str, state: Dict[str, Any]) -> bool:
    normalized = command.strip().lower()
    if normalized == "q":
        print("Stopping UAT runner without advancing the conversation.")
        return True
    if normalized == "i":
        print("\n=== Inserted User Prompt ===")
        prompt = input("insert prompt> ").strip()
        if prompt:
            run_inserted_turn(base_url, state, prompt)
        else:
            print("Insert canceled.")
        return False
    if normalized.startswith("i "):
        print("Use `i`, then type the inserted message at the `insert prompt>` line.")
        return False
    if normalized == "s":
        print("Current session_id: %s" % state["session_id"])
        return False
    if normalized == "b":
        try:
            warning = sync_state_with_broker(base_url, state)
            print(
                json.dumps(
                    {
                        "session_id": state["session_id"],
                        "scripted_turn_count": scripted_turn_count(state),
                        "inserted_turn_count": inserted_turn_count(state),
                        "skipped_turn_count": skipped_turn_count(state),
                        "managed_turn_count": managed_turn_count(state),
                        "broker_turn_count": state.get("broker_turn_count", 0),
                        "broker_message_count": state.get("broker_message_count", 0),
                        "broker_summary_char_count": state.get("broker_summary_char_count", 0),
                        "broker_summarized_turn_count": state.get(
                            "broker_summarized_turn_count", 0
                        ),
                        "external_turns_detected": state.get("external_turns_detected", 0),
                        "last_broker_sync_at": state.get("last_broker_sync_at"),
                    },
                    indent=2,
                )
            )
            if warning:
                print("Warning: %s" % warning)
        except Exception as exc:  # noqa: BLE001
            print("Broker session check failed: %s" % exc)
        return False
    if normalized == "h":
        try:
            payload = get_json(base_url, "/health")
            print(json.dumps(payload, indent=2))
        except Exception as exc:  # noqa: BLE001
            print("Health check failed: %s" % exc)
        return False
    if normalized == "r":
        try:
            payload = get_json(base_url, "/recovery/last")
            print(json.dumps(payload, indent=2))
        except Exception as exc:  # noqa: BLE001
            print("Recovery check failed: %s" % exc)
        return False
    print("Unknown command: %s" % command)
    return False


def run_turn(
    base_url: str,
    session_id: str,
    turn: Dict[str, Any],
) -> Dict[str, Any]:
    payload = dict(turn)
    payload["session_id"] = session_id
    return post_json(base_url, "/chat", payload)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run interactive broker UAT conversations from JSON")
    parser.add_argument(
        "--conversation",
        type=Path,
        default=Path("conversations/conversation.test01.json"),
        help="Path to the conversation JSON file.",
    )
    parser.add_argument(
        "--broker-url",
        type=str,
        default="http://127.0.0.1:8091",
        help="Broker base URL.",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=None,
        help="Optional state/results sidecar path. Defaults to <conversation>.state.json.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Discard any existing sidecar state and start a fresh broker session.",
    )
    args = parser.parse_args()

    conversation_path = args.conversation.resolve()
    conversation = load_json(conversation_path)
    conversation["__path__"] = str(conversation_path)
    turns: List[Dict[str, Any]] = list(conversation.get("turns", []))
    if not turns:
        raise SystemExit("conversation file must contain a non-empty 'turns' array")

    state_path = (args.state_file or derive_state_path(conversation_path)).resolve()
    if state_path.exists() and not args.reset:
        state = load_json(state_path)
        for result in state.get("results", []):
            if "kind" not in result:
                result["kind"] = "scripted"
        print("Resuming existing UAT state from %s" % state_path)
    else:
        if args.reset and state_path.exists():
            state_path.unlink()
        session_response = create_session(args.broker_url, conversation)
        state = build_state(conversation_path, args.broker_url, session_response)
        save_json(state_path, state)
        print("Created session %s" % state["session_id"])
        print("State saved to %s" % state_path)

    try:
        warning = sync_state_with_broker(args.broker_url, state)
        save_json(state_path, state)
        if warning:
            print("Warning: %s" % warning)
    except Exception as exc:  # noqa: BLE001
        print("Broker sync warning: %s" % exc)

    while state["next_turn_index"] < len(turns):
        turn_index = state["next_turn_index"]
        turn = turns[turn_index]
        prompt = str(turn.get("prompt", "")).strip()
        print_status(state, conversation)
        print_block("Next User Prompt", prompt or "<empty prompt>")
        print_menu()
        command = input("> ")
        if command.strip():
            if command.strip().lower() == "x":
                record_skipped_turn(state, turn_index=turn_index, prompt=prompt)
                state["next_turn_index"] = turn_index + 1
                state["completed"] = state["next_turn_index"] >= len(turns)
                save_json(state_path, state)
                print(
                    "Skipped scripted turn %d of %d. This prompt was marked as skipped by the UAT tester."
                    % (turn_index + 1, len(turns))
                )
                if not state["completed"]:
                    print(
                        "Press Enter to send scripted turn %d, or choose another command."
                        % (state["next_turn_index"] + 1)
                    )
                continue
            should_stop = handle_aux_command(command, args.broker_url, state)
            save_json(state_path, state)
            if should_stop:
                return
            continue

        try:
            started_at = utc_now()
            print("\nSending scripted turn %d of %d..." % (turn_index + 1, len(turns)))
            print("Waiting for broker response. Keystrokes typed during the request will be ignored.")
            response = run_turn(args.broker_url, state["session_id"], turn)
            response_text = str(response.get("response", "")).strip()
            discard_buffered_input()
            print_block("Assistant Response", response_text or json.dumps(response, indent=2))
            record_turn_result(
                state,
                kind="scripted",
                turn_index=turn_index,
                prompt=prompt,
                response=response,
                started_at=started_at,
            )
            state["next_turn_index"] = turn_index + 1
            state["completed"] = state["next_turn_index"] >= len(turns)
            try:
                warning = sync_state_with_broker(args.broker_url, state)
                if warning:
                    print("Warning: %s" % warning)
            except Exception as exc:  # noqa: BLE001
                print("Broker sync warning: %s" % exc)
            save_json(state_path, state)
            print("Scripted turn complete. Press Enter for the next scripted turn or choose a command.")
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            print("Request failed with HTTP %s: %s" % (exc.code, details))
            print("Turn was not advanced. Restart the broker if needed and press Enter to retry.")
        except Exception as exc:  # noqa: BLE001
            print("Request failed: %s" % exc)
            print("Turn was not advanced. Restart the broker if needed and press Enter to retry.")

    print("\nConversation complete for session %s" % state["session_id"])
    print("Results saved to %s" % state_path)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted. Existing session/state were preserved.")
        sys.exit(130)
