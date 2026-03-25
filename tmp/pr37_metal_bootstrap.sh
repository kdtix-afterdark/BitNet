#!/bin/zsh

set -euo pipefail

# Local lab bootstrap for testing PR 37 in a clean git worktree.
# This script prepares the older worktree for Apple Silicon + Metal without
# changing the main repository checkout.

SCRIPT_DIR="${0:A:h}"
PR37_ROOT="${PR37_ROOT:-/tmp/bitnet-pr37}"
SHARED_MODELS_ROOT="${SHARED_MODELS_ROOT:-/Users/ckreager/repos/kdtix/LLMs/BitNet/models}"
SHARED_MODEL_DIR="${SHARED_MODEL_DIR:-${SHARED_MODELS_ROOT}/BitNet-b1.58-2B-4T}"
BROKER_MODEL="${BROKER_MODEL:-${SHARED_MODEL_DIR}/ggml-model-i2_s.gguf}"
LLVM_ROOT="${LLVM_ROOT:-/opt/homebrew/opt/llvm@18}"
LIBOMP_ROOT="${LIBOMP_ROOT:-/opt/homebrew/opt/libomp}"
C_COMPILER="${C_COMPILER:-${LLVM_ROOT}/bin/clang}"
CXX_COMPILER="${CXX_COMPILER:-${LLVM_ROOT}/bin/clang++}"
LOG_DIR="${LOG_DIR:-${SCRIPT_DIR}}"
TIMESTAMP="${TIMESTAMP:-$(date +%Y%m%d-%H%M%S)}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/pr37_metal_bootstrap.${TIMESTAMP}.log}"
LOG_LATEST="${LOG_LATEST:-${SCRIPT_DIR}/pr37_metal_bootstrap.latest.log}"
CODEGEN_MODEL="${CODEGEN_MODEL:-bitnet_b1_58-3B}"
CODEGEN_BM="${CODEGEN_BM:-160,320,320}"
CODEGEN_BK="${CODEGEN_BK:-64,128,64}"
CODEGEN_BM_SIMD="${CODEGEN_BM_SIMD:-32,64,32}"
THREADS="${THREADS:-10}"
CTX_SIZE="${CTX_SIZE:-4096}"
N_PREDICT="${N_PREDICT:-4096}"
N_KEEP="${N_KEEP:--1}"
TEMPERATURE="${TEMPERATURE:-0.5}"
TOP_P="${TOP_P:-0.9}"
GPU_LAYERS="${GPU_LAYERS:-999}"
HOST="${HOST:-127.0.0.1}"
LLAMA_PORT="${LLAMA_PORT:-8080}"
BROKER_PORT="${BROKER_PORT:-8091}"

fail() {
  echo "error: $*" >&2
  exit 1
}

on_exit() {
  local exit_code=$?
  if [[ $exit_code -eq 0 ]]; then
    echo "==> Bootstrap succeeded"
  else
    echo "==> Bootstrap failed with exit code ${exit_code}"
  fi
  echo "==> Log saved to ${LOG_FILE}"
  if [[ "${LOG_LATEST}" != "${LOG_FILE}" ]]; then
    echo "==> Latest log link: ${LOG_LATEST}"
  fi
  exit $exit_code
}

trap on_exit EXIT

mkdir -p "$(dirname "${LOG_FILE}")" "$(dirname "${LOG_LATEST}")"
: > "${LOG_FILE}"
if [[ "${LOG_LATEST}" != "${LOG_FILE}" ]]; then
  ln -sfn "${LOG_FILE}" "${LOG_LATEST}"
fi
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "==> Logging bootstrap output to ${LOG_FILE}"
if [[ "${LOG_LATEST}" != "${LOG_FILE}" ]]; then
  echo "==> Updating latest bootstrap log link at ${LOG_LATEST}"
fi

[[ -d "${PR37_ROOT}" ]] || fail "worktree not found at ${PR37_ROOT}"
[[ -x "${C_COMPILER}" ]] || fail "clang not found at ${C_COMPILER}"
[[ -x "${CXX_COMPILER}" ]] || fail "clang++ not found at ${CXX_COMPILER}"
[[ -d "${LIBOMP_ROOT}" ]] || fail "libomp not found at ${LIBOMP_ROOT}"
[[ -d "${SHARED_MODEL_DIR}" ]] || fail "shared model directory not found at ${SHARED_MODEL_DIR}"

cd "${PR37_ROOT}"

echo "==> Initializing submodules"
git submodule update --init --recursive

echo "==> Clearing stale build directories"
rm -rf build build-metal logs

echo "==> Generating BitNet kernel headers"
export PATH="${LLVM_ROOT}/bin:${PATH}"

codegen_cmd=(
  python3
  utils/codegen_tl1.py
  --model "${CODEGEN_MODEL}"
  --BM "${CODEGEN_BM}"
  --BK "${CODEGEN_BK}"
  --bm "${CODEGEN_BM_SIMD}"
)

"${codegen_cmd[@]}"

echo "==> Creating Metal build"
cmake -S . -B build-metal \
  -DCMAKE_C_COMPILER="${C_COMPILER}" \
  -DCMAKE_CXX_COMPILER="${CXX_COMPILER}" \
  -DBITNET_ARM_TL1=OFF \
  -DGGML_METAL=ON \
  -DGGML_ACCELERATE=ON \
  -DGGML_BLAS=ON \
  -DGGML_BLAS_VENDOR=Apple \
  -DOpenMP_ROOT="${LIBOMP_ROOT}"

cmake --build build-metal --config Release -j"$(sysctl -n hw.logicalcpu)"

cat <<EOF

Bootstrap complete.

Terminal 1: start llama-server manually with Metal
  cd ${PR37_ROOT}
  ./build-metal/bin/llama-server \\
    -m ${BROKER_MODEL} \\
    -c ${CTX_SIZE} \\
    -t ${THREADS} \\
    -n ${N_PREDICT} \\
    --keep ${N_KEEP} \\
    --temp ${TEMPERATURE} \\
    --top-p ${TOP_P} \\
    -ngl ${GPU_LAYERS} \\
    --host ${HOST} \\
    --port ${LLAMA_PORT} \\
    -cb

Terminal 2: start the PR 37 broker and let it attach to the running server
  cd ${PR37_ROOT}
  export BITNET_WORKSPACE_ROOT=${PR37_ROOT}
  export BITNET_LLAMA_HOST=${HOST}
  export BITNET_LLAMA_PORT=${LLAMA_PORT}
  export BITNET_BROKER_HOST=${HOST}
  export BITNET_BROKER_PORT=${BROKER_PORT}
  export BITNET_LLAMA_SERVER_PATH=${PR37_ROOT}/build-metal/bin/llama-server
  export BITNET_BROKER_MODEL=${BROKER_MODEL}
  export BITNET_BROKER_THREADS=${THREADS}
  export BITNET_BROKER_CTX_SIZE=${CTX_SIZE}
  export BITNET_BROKER_N_PREDICT=${N_PREDICT}
  export BITNET_BROKER_TEMPERATURE=${TEMPERATURE}
  python3 run_broker.py

Health checks
  curl -sS http://${HOST}:${LLAMA_PORT}/health
  curl -sS http://${HOST}:${BROKER_PORT}/health

Notes
  - This helper skips PR 37's older setup_env.py because that path tries to
    install gguf-py and build sentencepiece, which fails on this lab's Python
    3.13 toolchain and is not needed when you already have the GGUF model.
  - If you hit Accelerate / visionOS errors in ggml-blas.cpp, retry with:
      C_COMPILER=/usr/bin/clang CXX_COMPILER=/usr/bin/clang++ ./tmp/pr37_metal_bootstrap.sh
  - The kernel headers are generated directly with utils/codegen_tl1.py using
    the same 2B/4T-compatible parameters that the newer lab branch validated.
  - PR 37's broker still launches a managed llama-server with -ngl 0, so keep
    using the manually started Metal server for GPU testing.
  - PR 37 does not yet wire TOP_P or N_KEEP through the broker env, so those
    stay on the manual llama-server command.

EOF
