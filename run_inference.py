import os
import sys
import signal
import platform
import argparse
import subprocess
from datetime import datetime

DATE_GUARD_TEMPLATE = """Current local date: {current_date}

Operating rules:
- Never claim a specific knowledge cutoff month or year from memory.
- If the user asks about your knowledge cutoff or how recent your knowledge is, answer: "I do not have a reliable built-in cutoff date in this local runtime. For current facts, I need retrieval or fresh sources."
- Treat questions about current, recent, latest, today, this week, this month, this year, or ongoing events as time-sensitive.
- If a question depends on up-to-date facts, say your built-in knowledge may be stale and ask for retrieval or fresh sources.
- Distinguish stable background knowledge from time-sensitive facts.
- If you are unsure, say so briefly instead of guessing.
"""


def get_current_date_string():
    """Return the local date used in the runtime prompt guard."""
    return datetime.now().astimezone().strftime("%B %-d, %Y")


def build_effective_prompt(prompt, conversation, inject_date_guard):
    """Build the prompt passed to llama-cli."""
    if not inject_date_guard:
        return prompt

    policy = DATE_GUARD_TEMPLATE.format(current_date=get_current_date_string())
    if conversation:
        return f"{prompt.strip()}\n\n{policy}"

    return f"{policy}\nUser request: {prompt.strip()}"


def detect_model_variant(model_path):
    """Return a coarse model variant hint from the GGUF filename."""
    model_name = os.path.basename(model_path).lower()
    if "f32" in model_name:
        return "f32"
    if "i2_s" in model_name or "i2s" in model_name:
        return "i2_s"
    return "unknown"


def find_quality_chat_model(model_path):
    """Return a sibling F32 GGUF when the selected model is a compact chat-unfriendly quant."""
    model_dir = os.path.dirname(model_path)
    candidates = [
        os.path.join(model_dir, "ggml-model-f32-bitnet.gguf"),
        os.path.join(model_dir, "ggml-model-f32.gguf"),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return None


def run_command(command, shell=False):
    """Run a system command and ensure it succeeds."""
    try:
        subprocess.run(command, shell=shell, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running command: {e}")
        sys.exit(1)


def resolve_llama_cli_path(build_dir):
    """Resolve the llama-cli binary from the selected build directory."""
    if platform.system() == "Windows":
        main_path = os.path.join(build_dir, "bin", "Release", "llama-cli.exe")
        if not os.path.exists(main_path):
            main_path = os.path.join(build_dir, "bin", "llama-cli")
    else:
        main_path = os.path.join(build_dir, "bin", "llama-cli")
    return main_path


def run_inference():
    main_path = resolve_llama_cli_path(args.build_dir)
    model_path = args.model
    model_variant = detect_model_variant(model_path)

    if args.conversation:
        quality_model = find_quality_chat_model(model_path)
        if args.chat_model == "quality":
            if quality_model and quality_model != model_path:
                print(
                    "Interactive chat quality mode: using sibling F32 model %s"
                    % quality_model
                )
                model_path = quality_model
                model_variant = detect_model_variant(model_path)
            elif model_variant != "f32":
                print(
                    "Interactive chat quality mode requested, but no sibling F32 GGUF was found."
                )
        elif model_variant == "i2_s" and quality_model:
            print(
                "Warning: %s is a compact quant that performs poorly for interactive chat. "
                "For higher quality, use %s or pass --chat-model quality."
                % (model_path, quality_model)
            )

    effective_prompt = build_effective_prompt(
        args.prompt,
        conversation=args.conversation,
        inject_date_guard=args.inject_date_guard,
    )
    command = [
        f'{main_path}',
        '-m', model_path,
        '-n', str(args.n_predict),
        '-t', str(args.threads),
        '-p', effective_prompt,
        '-ngl', str(args.gpu_layers),
        '-c', str(args.ctx_size),
        '--temp', str(args.temperature),
        '--top-p', str(args.top_p),
        "-b", "1",
    ]
    if args.conversation:
        command.append("-cnv")
    run_command(command)

def signal_handler(sig, frame):
    print("Ctrl+C pressed, exiting...")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    # Usage: python run_inference.py -p "Microsoft Corporation is an American multinational corporation and technology company headquartered in Redmond, Washington."
    parser = argparse.ArgumentParser(description='Run inference')
    parser.add_argument("-m", "--model", type=str, help="Path to model file", required=False, default="models/bitnet_b1_58-3B/ggml-model-i2_s.gguf")
    parser.add_argument("-n", "--n-predict", type=int, help="Number of tokens to predict when generating text", required=False, default=128)
    parser.add_argument("-p", "--prompt", type=str, help="Prompt to generate text from", required=True)
    parser.add_argument("-t", "--threads", type=int, help="Number of threads to use", required=False, default=2)
    parser.add_argument("-c", "--ctx-size", type=int, help="Size of the prompt context", required=False, default=2048)
    parser.add_argument("-temp", "--temperature", type=float, help="Temperature, a hyperparameter that controls the randomness of the generated text", required=False, default=0.8)
    parser.add_argument("--top-p", type=float, help="Top-p nucleus sampling parameter", required=False, default=0.95)
    parser.add_argument("-cnv", "--conversation", action='store_true', help="Whether to enable chat mode or not (for instruct models.)")
    parser.add_argument(
        "--chat-model",
        choices=["current", "quality"],
        default="current",
        help="When running in conversation mode, keep the selected model or switch to a sibling F32 GGUF for higher quality if available.",
    )
    parser.add_argument("--build-dir", type=str, help="Build directory containing llama-cli", required=False, default="build")
    parser.add_argument("--gpu-layers", type=int, help="Number of layers to offload to the GPU backend", required=False, default=0)
    parser.add_argument(
        "--no-date-guard",
        dest="inject_date_guard",
        action="store_false",
        help="Disable the default current-date and time-sensitivity guard that is added to the prompt.",
    )
    parser.set_defaults(inject_date_guard=True)

    args = parser.parse_args()
    run_inference()
