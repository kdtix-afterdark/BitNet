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

def run_command(command, shell=False):
    """Run a system command and ensure it succeeds."""
    try:
        subprocess.run(command, shell=shell, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running command: {e}")
        sys.exit(1)

def run_inference():
    build_dir = "build"
    if platform.system() == "Windows":
        main_path = os.path.join(build_dir, "bin", "Release", "llama-cli.exe")
        if not os.path.exists(main_path):
            main_path = os.path.join(build_dir, "bin", "llama-cli")
    else:
        main_path = os.path.join(build_dir, "bin", "llama-cli")
    effective_prompt = build_effective_prompt(
        args.prompt,
        conversation=args.conversation,
        inject_date_guard=args.inject_date_guard,
    )
    command = [
        f'{main_path}',
        '-m', args.model,
        '-n', str(args.n_predict),
        '-t', str(args.threads),
        '-p', effective_prompt,
        '-ngl', '0',
        '-c', str(args.ctx_size),
        '--temp', str(args.temperature),
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
    parser.add_argument("-cnv", "--conversation", action='store_true', help="Whether to enable chat mode or not (for instruct models.)")
    parser.add_argument(
        "--no-date-guard",
        dest="inject_date_guard",
        action="store_false",
        help="Disable the default current-date and time-sensitivity guard that is added to the prompt.",
    )
    parser.set_defaults(inject_date_guard=True)

    args = parser.parse_args()
    run_inference()
