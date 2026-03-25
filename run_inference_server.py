import os
import sys
import signal
import platform
import argparse
import subprocess

def run_command(command, shell=False):
    """Run a system command and ensure it succeeds."""
    try:
        subprocess.run(command, shell=shell, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running command: {e}")
        sys.exit(1)

def run_server():
    build_dir = args.build_dir
    if platform.system() == "Windows":
        server_path = os.path.join(build_dir, "bin", "Release", "llama-server.exe")
        if not os.path.exists(server_path):
            server_path = os.path.join(build_dir, "bin", "llama-server")
    else:
        server_path = os.path.join(build_dir, "bin", "llama-server")

    command = [
        server_path,
        '-m', args.model,
        '-c', str(args.ctx_size),
        '-t', str(args.threads),
        '-n', str(args.n_predict),
        '-ngl', str(args.gpu_layers),
        '--keep', str(args.keep),
        '--temp', str(args.temperature),
        '--top-p', str(args.top_p),
        '--host', args.host,
        '--port', str(args.port),
        '-cb'  # Enable continuous batching
    ]

    if args.prompt:
        command.extend(['-p', args.prompt])

    print(f"Starting server on {args.host}:{args.port}")
    run_command(command)

def signal_handler(sig, frame):
    print("Ctrl+C pressed, shutting down server...")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(description='Run llama.cpp server')
    parser.add_argument("--build-dir", type=str, help="Build directory containing llama-server", default="build-metal")
    parser.add_argument("-m", "--model", type=str, help="Path to model file", default="models/BitNet-b1.58-2B-4T/ggml-model-i2_s.gguf")
    parser.add_argument("-p", "--prompt", type=str, help="System prompt for the model", required=False)
    parser.add_argument("-n", "--n-predict", type=int, help="Number of tokens to predict", default=4096)
    parser.add_argument("-t", "--threads", type=int, help="Number of threads to use", default=10)
    parser.add_argument("-c", "--ctx-size", type=int, help="Size of the context window", default=4096)
    parser.add_argument("--temperature", type=float, help="Temperature for sampling", default=0.5)
    parser.add_argument("--top-p", type=float, help="Top-p (nucleus) sampling threshold", default=0.9)
    parser.add_argument("--keep", type=int, help="Number of tokens to keep on context shift (-1 = all)", default=-1)
    parser.add_argument("--gpu-layers", type=int, help="Number of layers to offload to GPU via -ngl (999 = offload all, which is the correct setting for full Metal acceleration)", default=999)
    parser.add_argument("--host", type=str, help="IP address to listen on", default="127.0.0.1")
    parser.add_argument("--port", type=int, help="Port to listen on", default=8080)

    args = parser.parse_args()
    run_server()
