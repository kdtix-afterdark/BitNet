import argparse
import os
import platform
import signal
import subprocess
import sys

def run_command(command, shell=False):
    """Run a system command and ensure it succeeds."""
    try:
        subprocess.run(command, shell=shell, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running command: {e}")
        sys.exit(1)

def resolve_llama_server_path(build_dir):
    """Resolve the llama-server binary from the selected build directory."""
    if platform.system() == "Windows":
        server_path = os.path.join(build_dir, "bin", "Release", "llama-server.exe")
        if not os.path.exists(server_path):
            server_path = os.path.join(build_dir, "bin", "llama-server")
    else:
        server_path = os.path.join(build_dir, "bin", "llama-server")
    return server_path


def run_server():
    server_path = resolve_llama_server_path(args.build_dir)

    command = [
        server_path,
        '-m', args.model,
        '-c', str(args.ctx_size),
        '-t', str(args.threads),
        '-n', str(args.n_predict),
        '--keep', str(args.keep),
        '-ngl', str(args.gpu_layers),
        '--temp', str(args.temperature),
        '--top-p', str(args.top_p),
        '--host', args.host,
        '--port', str(args.port),
        '-cb'  # Enable continuous batching
    ]
    
    if args.prompt:
        command.extend(['-p', args.prompt])
    
    # Note: -cnv flag is removed as it's not supported by the server
    
    print(f"Starting server on {args.host}:{args.port}")
    run_command(command)

def signal_handler(sig, frame):
    print("Ctrl+C pressed, shutting down server...")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    
    parser = argparse.ArgumentParser(description='Run llama.cpp server')
    parser.add_argument("-m", "--model", type=str, help="Path to model file", required=False, default="models/BitNet-b1.58-2B-4T/ggml-model-i2_s.gguf")
    parser.add_argument("-p", "--prompt", type=str, help="System prompt for the model", required=False)
    parser.add_argument("-n", "--n-predict", type=int, help="Number of tokens to predict", required=False, default=4096)
    parser.add_argument("-t", "--threads", type=int, help="Number of threads to use", required=False, default=10)
    parser.add_argument("-c", "--ctx-size", type=int, help="Size of the context window", required=False, default=4096)
    parser.add_argument("--keep", type=int, help="Number of prompt tokens to keep on context shift", required=False, default=-1)
    parser.add_argument("--temperature", type=float, help="Temperature for sampling", required=False, default=0.5)
    parser.add_argument("--top-p", type=float, help="Top-p sampling value", required=False, default=0.9)
    parser.add_argument("--build-dir", type=str, help="Build directory containing llama-server", required=False, default="build-metal")
    parser.add_argument("--gpu-layers", type=int, help="Number of layers to offload to the GPU backend", required=False, default=999)
    parser.add_argument("--host", type=str, help="IP address to listen on", required=False, default="127.0.0.1")
    parser.add_argument("--port", type=int, help="Port to listen on", required=False, default=8080)
    
    args = parser.parse_args()
    run_server()
