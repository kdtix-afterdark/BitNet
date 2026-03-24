# Known Good Metal Build Reference

This branch captures the Apple Silicon + Metal build configuration that was
validated locally on the lab station and used as the baseline for future
comparisons and rebuilds.

## Validated Host

- macOS on Apple Silicon
- GPU: Apple M4 Max
- Compiler: Homebrew clang 18.1.8
- Backend: Metal
- BLAS: Apple Accelerate (`BLAS = 1`)

## Validated Build Flags

The known-good `build-metal` configuration uses:

- `BITNET_ARM_TL1=OFF`
- `GGML_METAL=ON`
- `GGML_ACCELERATE=ON`
- `GGML_BLAS=ON`
- `GGML_BLAS_VENDOR=Apple`
- `OpenMP_ROOT=/opt/homebrew/opt/libomp`
- `CMAKE_C_COMPILER=/opt/homebrew/opt/llvm@18/bin/clang`
- `CMAKE_CXX_COMPILER=/opt/homebrew/opt/llvm@18/bin/clang++`

## Validated Runtime Settings

The lab-stable `i2_s` runtime configuration is:

- `BITNET_BROKER_MODEL=${BITNET_WORKSPACE_ROOT}/models/BitNet-b1.58-2B-4T/ggml-model-i2_s.gguf`
- `BITNET_BROKER_GPU_LAYERS=999`
- `BITNET_BROKER_THREADS=10`
- `BITNET_BROKER_CTX_SIZE=4096`
- `BITNET_BROKER_N_PREDICT=4096`
- `BITNET_BROKER_N_KEEP=-1`
- `BITNET_BROKER_TEMPERATURE=0.5`
- `BITNET_BROKER_TOP_P=0.9`

Equivalent direct server launch:

```bash
python3 setup_env.py \
  -md models/BitNet-b1.58-2B-4T \
  -q i2_s \
  --build-dir build-metal \
  --backend metal

python3 run_inference_server.py \
  --build-dir build-metal \
  --model models/BitNet-b1.58-2B-4T/ggml-model-i2_s.gguf \
  --threads 10 \
  --ctx-size 4096 \
  --n-predict 4096 \
  --keep -1 \
  --temperature 0.5 \
  --top-p 0.9 \
  --gpu-layers 999
```

## Expected Healthy Startup Signals

These log lines indicate a healthy Metal runtime:

- `build: ... with Homebrew clang version 18.1.8`
- `ggml_metal_init: found device: Apple M4 Max`
- `ggml_metal_init: picking default device: Apple M4 Max`
- `ggml_metal_init: hasUnifiedMemory = true`
- `llm_load_tensors: offloaded 31/31 layers to GPU`
- `system_info: ... BLAS = 1`

## Submodule Patch Set

The validated local build also depends on a small `llama.cpp` patch bundle that
is not represented by the pinned submodule commit alone. The patch file is
checked in here for reproducibility:

- [llama.cpp-known-good-metal.patch](/tmp/bitnet-metal-build-config/docs/patches/llama.cpp-known-good-metal.patch)

It records the local Metal compatibility fixes used during validation:

- narrow Apple Accelerate includes to `vecLib`
- nil-safe Metal device acquisition and memory querying
- Apple BLAS header lookup fallback in CMake

This branch is meant to preserve the reference state. It does not claim that
the submodule patch set has already been upstreamed.
