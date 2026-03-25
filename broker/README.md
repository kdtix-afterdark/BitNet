# BitNet Local Broker MVP

This broker adds a stable localhost JSON contract in front of a persistent
`llama-server` process. The intent is to keep model inference, deterministic
tooling, and IDE integration separate.

## Design

- `llama-server` stays the long-lived model runtime.
- The broker manages runtime startup and readiness checks.
- The broker exposes a small local HTTP API for sessions, deterministic tools,
  grounded chat, and artifact drafting.
- The model does not directly choose arbitrary tools in this MVP.

## Endpoints

- `GET /health`
- `GET /recovery/last`
- `POST /sessions`
- `POST /tools/run`
- `POST /chat`
- `POST /artifacts/draft`

## Session System Prompts

New sessions now load their chat system prompt from a markdown file instead of
defaulting to an inline code constant.

Default location:

- [default.system.prompt.md](/Users/ckreager/repos/kdtix/LLMs/BitNet/broker/system_prompts/default.system.prompt.md)

Default behavior:

- if `BITNET_BROKER_SYSTEM_PROMPT` is set, the broker loads that file
- otherwise it falls back to `default.system.prompt.md`
- if a `POST /sessions` request includes `system_prompt_path`, that file is used for that session
- if a `POST /sessions` request includes `system_prompt`, that inline text wins over any file path

`system_prompt_path` accepts either:

- a filename inside `BITNET_BROKER_SYSTEM_PROMPTS_DIR`, such as `kdtix.system.prompt.md`
- or a workspace-local relative or absolute path

Prompt files are restricted to the current workspace root for safety. The broker
loads the file once at session creation time and stores the resolved prompt text
inside the session, so later edits to the markdown file do not silently change
an existing live session.

## Supported deterministic tools

- `list_directory`
- `read_text_file`
- `search_text`
- `mcp_list_servers`
- `mcp_list_server_tools`
- `mcp_call_tool`
- `mcp_memory_call`
- `mcp_sequential_thinking`
- `mcp_context7_call`

All tool paths are restricted to the current workspace root.

## MCP Adapter Config

The broker now supports stdio MCP servers through a local config file.

- Default config path: `broker/mcp_servers.json`
- Example real-server template: [broker/mcp_servers.example.json](/Users/ckreager/repos/kdtix/LLMs/BitNet/broker/mcp_servers.example.json)
- Local smoke-test config: [broker/mcp_servers.mock.json](/Users/ckreager/repos/kdtix/LLMs/BitNet/broker/mcp_servers.mock.json)
- Real Memory wrapper: [broker/run_memory_mcp.sh](/Users/ckreager/repos/kdtix/LLMs/BitNet/broker/run_memory_mcp.sh)
- Local Node package manifest: [broker/package.json](/Users/ckreager/repos/kdtix/LLMs/BitNet/broker/package.json)

The intended rollout order is:

1. Memory
2. Sequential Thinking
3. Context7
4. Reference servers
5. Major platform servers
6. QA / browser / delivery tooling

## Install The Real Memory Server

Install the upstream Memory MCP package into the repo-local `broker/` runtime:

```bash
npm install --prefix broker
```

The broker can then launch the real Memory server through the local wrapper in
`broker/run_memory_mcp.sh`. The default local config file
`broker/mcp_servers.json` already points at that wrapper.
The configured persistent store path is `broker_memory/memory.jsonl`.

## Durable Session Lifecycle

The broker now keeps a 3-layer local lifecycle in front of the model and MCP memory:

- Hot state: synchronous append-only journal at `broker_state/broker_events.jsonl`
- Warm state: periodic compact snapshots under `broker_state/snapshots/`
- Cold state: async Memory MCP sink for completed turns and artifact drafts

Warm snapshots now retain:

- the last `BITNET_BROKER_SNAPSHOT_HISTORY_TURNS` turns verbatim
- a compact recovered summary of older turns that fell out of the warm window
- the pending async memory sync queue and model settings hash

The durable manifest lives at `broker_state/manifest.json`. It tracks:

- monotonic event sequence
- clean vs dirty shutdown
- latest snapshot path / sequence
- pending async memory sync count
- last successful memory sync
- last recovery report

The journal records lifecycle markers such as:

- `session_open`
- `turn_started`
- `tool_called`
- `turn_completed`
- `memory_sync_queued`
- `memory_sync_attempted`
- `memory_sync_completed`
- `memory_sync_failed`
- `snapshot_created`
- `heartbeat`
- `shutdown_clean`

If the broker exits uncleanly, the next startup marks a dirty recovery and rebuilds
active sessions from the latest snapshot plus any journaled events recorded after it.
On a clean restart, restored chat prompts include both the compact recovered summary
and the retained verbatim turns, so older session context is not lost just because
it rolled out of the warm snapshot window.

## Recommended Environment Profile

The broker is now intended to run from environment defaults first, with CLI
flags reserved for one-off overrides.

The checked-in example profile is [/.env.example](/Users/ckreager/repos/kdtix/LLMs/BitNet/.env.example).

Load it into your shell:

```bash
cd /Users/ckreager/repos/kdtix/LLMs/BitNet

set -a
source ./.env.example
set +a
```

Start the broker with the recommended `f32 + build-metal + ctx=8192` profile:

```bash
python3 run_broker.py
```

Create a session with the default markdown prompt:

```bash
curl -sS http://127.0.0.1:8091/sessions \
  -H 'Content-Type: application/json' \
  -d '{"metadata":{"uat":"default-prompt"}}'
```

Create a session with a different prompt file from the prompts directory:

```bash
curl -sS http://127.0.0.1:8091/sessions \
  -H 'Content-Type: application/json' \
  -d '{"system_prompt_path":"kdtix.system.prompt.md","metadata":{"uat":"kdtix-prompt"}}'
```

## Interactive Conversation UAT

For repeatable chat-memory tests, you can drive the broker from a JSON conversation
file instead of copy/pasting prompts manually.

The sample conversation file is [conversation.test01.json](/Users/ckreager/repos/kdtix/LLMs/BitNet/conversations/conversation.test01.json), and the runner is [run_conversation_uat.py](/Users/ckreager/repos/kdtix/LLMs/BitNet/run_conversation_uat.py).

Run it like this:

```bash
cd /Users/ckreager/repos/kdtix/LLMs/BitNet

python3 run_conversation_uat.py \
  --conversation conversations/conversation.test01.json \
  --broker-url http://127.0.0.1:8091
```

What it does:

- creates one broker session and saves the `session_id`
- sends one turn at a time only when you press Enter
- pauses between turns so you can stop and restart the broker whenever you want
- keeps progress in a sidecar file such as `conversations/conversation.test01.state.json`
- resumes from that state file on the next run unless you pass `--reset`
- syncs the sidecar with `/recovery/last` so you can see whether extra out-of-band turns were added from another shell

While paused between turns:

- `Enter` sends the next turn
- `h` shows `/health`
- `r` shows `/recovery/last`
- `b` shows broker session counts and any detected out-of-band turns
- `s` prints the active `session_id`
- `i` opens insert mode and prompts for one inserted ad hoc message on the next line
- `x` skips the current scripted prompt and records that it was skipped by the UAT tester
- `q` quits without losing progress

Inserted turns are recorded in the sidecar state as `kind="inserted"`, so they
count toward broker-session reconciliation but do not consume the next scripted turn.
Skipped turns are recorded as `kind="skipped"`, so they advance the scripted test
flow locally without being counted as broker-managed turns. Each skipped entry
also keeps the original scripted prompt text in `original_scripted_prompt` and
adds a short `skip_note` for easier sidecar review later.
While the broker is processing a request, the runner now prints explicit send/wait
status and discards any extra keystrokes typed during that request so they do not
get replayed accidentally when the next prompt appears.

## Root-Cause Debug Tracing

For real prompt / raw model / repair / persistence debugging, enable per-turn
broker traces:

```bash
set -a
source ./.env.example
set +a

python3 run_broker.py
```

With `BITNET_BROKER_TRACE_TURNS=1`, the broker writes:

- append-only live trace stream: `broker_traces/turn-trace.jsonl`
- per-turn trace files: `broker_traces/turns/<correlation_id>.json`

Each traced chat turn captures:

- turn start metadata
- exact assembled `messages`
- exact llama request payload
- raw llama response
- pre/post repair content
- final session append snapshot

To live-tail the broker trace and the UAT sidecar together:

```bash
python3 monitor_broker_debug.py \
  --state-file conversations/conversation.test02.state.json
```

This monitor follows the active conversation sidecar and filters the broker trace
stream to the matching `session_id`, so you can watch turn-by-turn state changes
and trace phases in one place while the local Metal runtime is running elsewhere.

To start a fresh run against the same conversation file:

```bash
python3 run_conversation_uat.py \
  --conversation conversations/conversation.test01.json \
  --broker-url http://127.0.0.1:8091 \
  --reset
```

With the example profile loaded, the broker listens on `127.0.0.1:8091` and
the managed `llama-server` listens on `127.0.0.1:8080` unless you override
those values.

The example profile also enables broker request logging with
`BITNET_BROKER_LOG_LEVEL=1` and `BITNET_BROKER_VERBOSE=1`. Console and file logs
are written to `broker_logs/broker.log`.

Recovery report from the CLI:

```bash
python3 run_broker.py --recover-last-session
```

The CLI command inspects the persisted on-disk state without starting the broker.
For a running broker, the last startup recovery outcome is also exposed over HTTP:

```bash
curl -sS http://127.0.0.1:8091/recovery/last
```

CLI flags still work, but they are now override mode on top of the current
environment profile.

Example override:

```bash
python3 run_broker.py \
  --model models/bitnet-b1.58-2B-4T-bf16/ggml-model-f32-bitnet.gguf \
  --llama-build-dir build-metal \
  --gpu-layers 999 \
  --broker-port 8091 \
  --llama-port 8080 \
  --threads 10 \
  --ctx-size 8192 \
  --n-predict 4096 \
  --keep -1 \
  --temperature 0.5 \
  --top-p 0.9
```

## Environment Reference

All supported broker environment variables are listed below. The same list is
also included in `python3 run_broker.py --help`.

| Variable | Default | Purpose |
| --- | --- | --- |
| `BITNET_WORKSPACE_ROOT` | current working directory | Workspace root used to resolve default relative paths. |
| `BITNET_BROKER_MODEL` | `${workspace_root}/models/bitnet-b1.58-2B-4T-bf16/ggml-model-f32-bitnet.gguf` | GGUF model path for the broker-managed llama-server. |
| `BITNET_BROKER_HOST` | `127.0.0.1` | Broker bind host. |
| `BITNET_BROKER_PORT` | `8091` | Broker bind port. |
| `BITNET_LLAMA_HOST` | `127.0.0.1` | llama-server bind host. |
| `BITNET_LLAMA_PORT` | `8080` | llama-server bind port. |
| `BITNET_LLAMA_BUILD_DIR` | `${workspace_root}/build-metal` | Build directory that contains `llama-server`. |
| `BITNET_LLAMA_SERVER_PATH` | `${BITNET_LLAMA_BUILD_DIR}/bin/llama-server` | Explicit `llama-server` binary path override. |
| `BITNET_BROKER_GPU_LAYERS` | `999` | Number of model layers to offload to the GPU backend. |
| `BITNET_BROKER_THREADS` | `10` | Generation thread count. |
| `BITNET_BROKER_CTX_SIZE` | `8192` | Context window size used by the broker-managed model runtime. |
| `BITNET_BROKER_N_PREDICT` | `4096` | Default max completion tokens per request. |
| `BITNET_BROKER_N_KEEP` | `-1` | Prompt tokens to keep when context shifting occurs. |
| `BITNET_BROKER_TEMPERATURE` | `0.5` | Default sampling temperature. |
| `BITNET_BROKER_TOP_P` | `0.9` | Default top-p sampling value. |
| `BITNET_BROKER_STARTUP_TIMEOUT` | `120` | Seconds to wait for `llama-server` to become ready. |
| `BITNET_BROKER_REQUEST_TIMEOUT` | `180` | Seconds to wait for a model completion response. |
| `BITNET_BROKER_LOG_LEVEL` | `1` | Broker log level: `0=errors`, `1=info`, `2=debug`, `3=trace`. |
| `BITNET_BROKER_VERBOSE` | `0` | Broker request detail level: `0=quiet`, `1=requests`, `2=summaries`, `3=payload excerpts`. |
| `BITNET_BROKER_LOG_DIR` | `${workspace_root}/broker_logs` | Directory for broker and MCP log files. |
| `BITNET_BROKER_STATE_DIR` | `${workspace_root}/broker_state` | Directory for the durable journal, manifest, and snapshots. |
| `BITNET_BROKER_SYSTEM_PROMPTS_DIR` | `${workspace_root}/broker/system_prompts` | Directory that contains reusable markdown system prompt files. |
| `BITNET_BROKER_SYSTEM_PROMPT` | `${BITNET_BROKER_SYSTEM_PROMPTS_DIR}/default.system.prompt.md` | Default chat system prompt file. Accepts either a workspace-local path or a filename inside `BITNET_BROKER_SYSTEM_PROMPTS_DIR`. |
| `BITNET_MCP_CONFIG` | `${workspace_root}/broker/mcp_servers.json` | Path to the MCP server configuration file. |
| `BITNET_MCP_STARTUP_TIMEOUT` | `30` | Seconds to wait for MCP server startup. |
| `BITNET_MCP_REQUEST_TIMEOUT` | `60` | Seconds to wait for an MCP tool response. |
| `BITNET_MCP_PROTOCOL_VERSION` | `2025-03-26` | Protocol version passed during MCP initialize handshake. |
| `BITNET_BROKER_SNAPSHOT_TURN_INTERVAL` | `3` | Create a warm-state snapshot after this many completed turns. |
| `BITNET_BROKER_SNAPSHOT_HISTORY_TURNS` | `8` | Turns retained verbatim in warm snapshots; older turns are compacted into a recovered session summary. |
| `BITNET_BROKER_HEARTBEAT_INTERVAL_SECONDS` | `30` | Heartbeat cadence for liveness and audit events; set `0` to disable. |
| `BITNET_BROKER_MEMORY_SYNC_ENABLED` | `1` | Enable async cold-memory sync to the Memory MCP server. |
| `BITNET_BROKER_MEMORY_SYNC_RETRY_SECONDS` | `15` | Retry delay for failed async memory sync items. |

## CPU And Metal Switching

The broker can now target either the CPU build in `build/` or a Metal-enabled
build in `build-metal/`.

CPU broker:

```bash
python run_broker.py \
  --model models/bitnet-b1.58-2B-4T-bf16/ggml-model-f32-bitnet.gguf \
  --llama-build-dir build \
  --gpu-layers 0 \
  --broker-port 8091 \
  --llama-port 8081
```

Metal broker:

```bash
python run_broker.py \
  --model models/bitnet-b1.58-2B-4T-bf16/ggml-model-f32-bitnet.gguf \
  --llama-build-dir build-metal \
  --gpu-layers 999 \
  --broker-port 8091 \
  --llama-port 8081
```

The same switching model applies to the direct server entrypoint:

```bash
python run_inference_server.py --build-dir build --gpu-layers 0
python run_inference_server.py --build-dir build-metal --gpu-layers 999
```

## Recommended Local Chat Profile

The current default broker and `run_inference_server.py` profile is aligned to
the strongest host-side BitNet chat path validated so far on Apple Silicon:

- `build-metal/`
- `ggml-model-f32-bitnet.gguf`
- `--ctx-size 8192`
- `--n-predict 4096`
- `--keep -1`
- `--temperature 0.5`
- `--top-p 0.9`
- `--gpu-layers 999`

This does not make the broker stateful by itself. The raw model still only sees
what the broker sends per request. The broker now replays prior `/chat` turns
for calls that include `session_id`, and Memory MCP remains the durable recall
path for long-running workflows.

The Metal build now compiles cleanly on Apple Silicon with Homebrew
`clang 18.1.8`, `GGML_METAL=ON`, `GGML_ACCELERATE=ON`, and `GGML_BLAS=ON` /
`GGML_BLAS_VENDOR=Apple`.

Host-side validation on Apple M4 Max confirmed:
- `ggml_metal_init: found device: Apple M4 Max`
- `llm_load_tensors: offloaded 31/31 layers to GPU`
- `BLAS = 1`
- successful generation without a crash

Inside the Codex desktop runtime used for validation here, `MTLCreateSystemDefaultDevice()`
still returns `nil`, but that is specific to the Codex app runtime and does not
block using `build-metal/` on the host machine. The broker can target
`build-metal/` for normal host-side use.

## Test Right Now

Use the old `run_inference.py` command only if you want a raw model sanity
check. Use the broker flow below if you want to test the new local broker
contract.

You can run these commands in a plain `zsh` terminal or in the VS Code
integrated terminal. For this MVP, they are equivalent.

### 1. Raw model sanity check

```bash
python run_inference.py \
  -m models/bitnet-b1.58-2B-4T-bf16/ggml-model-f32-bitnet.gguf \
  -p "You are a helpful assistant" \
  -cnv \
  -t 1 \
  -c 512
```

This validates the GGUF and the direct CLI inference path only. It does not
exercise the broker.

### 2. Broker smoke test

Open terminal 1 and start the broker:

```bash
set -a
source ./.env.example
set +a

BITNET_BROKER_PORT=8091 \
BITNET_LLAMA_PORT=8081 \
python3 run_broker.py
```

Open terminal 2 and run the broker checks.

Health before first model request:

```bash
curl -sS http://127.0.0.1:8091/health
```

Deterministic tool execution:

```bash
curl -sS http://127.0.0.1:8091/tools/run \
  -H "Content-Type: application/json" \
  -d '{
    "tool_calls": [
      {
        "tool": "read_text_file",
        "args": {
          "path": "broker/README.md",
          "max_chars": 600
        }
      },
      {
        "tool": "search_text",
        "args": {
          "pattern": "artifact",
          "path": "broker",
          "glob": "*.py",
          "max_matches": 5
        }
      }
    ]
  }'
```

Grounded chat through the broker:

```bash
curl -sS http://127.0.0.1:8091/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Using the provided evidence, answer in one short sentence with the document title only.",
    "tool_calls": [
      {
        "tool": "read_text_file",
        "args": {
          "path": "broker/README.md",
          "max_chars": 220
        }
      }
    ],
    "max_tokens": 32,
    "temperature": 0.0
  }'
```

For simple extractive prompts, the broker applies deterministic repairs from
evidence when possible. Current supported patterns include document title,
first heading, file path, tool names used, directory entries, search match
count, and truncation checks. In those cases, the response includes
`repair_applied: true`, `repair_reason`, and `original_response`.

The default broker prompt policy also instructs the model to respond in
English unless the user explicitly requests another language. Broker JSON
responses now emit UTF-8 directly instead of ASCII-escaped `\uXXXX` sequences.

The broker also supports a small memory-aware routing layer before the model is
invoked. Current routed prompt forms are:

- `Remember <Entity>: <Observation>`
- `What do you remember about <Entity>?`
- `Show memory graph`

For those prompts, the broker talks to the Memory MCP server directly and
returns `route_applied: true`, `route_reason`, `route_operations`, and
`model_invoked: false`.

For non-routed chat, you can also inject Memory results as evidence by passing
`memory_query`. In that path:

- `memory_evidence_applied` reports whether Memory evidence was injected
- `memory_evidence_reason` describes the injection path
- `include_tool_manifest` defaults to `true`
- `broker_controls_tools` defaults to `false`, and can be switched on per call

When `broker_controls_tools` is `true`, the broker may answer directly from
Memory evidence for supported prompts such as short summaries and observation
lists. In that case, `model_invoked` becomes `false` and `route_reason`
describes the broker-controlled answer path.

Artifact draft plus deterministic heading checks:

```bash
curl -s http://127.0.0.1:8091/artifacts/draft \
  -H "Content-Type: application/json" \
  -d '{
    "artifact_id": "MVP-01",
    "task": "Create a short markdown artifact with headings Executive Summary and Metadata. Put one brief sentence under each heading.",
    "required_sections": ["Executive Summary", "Metadata"],
    "max_tokens": 96,
    "temperature": 0.0
  }'
```

### Expected behavior

- `/health` should return broker metadata immediately.
- Before the first `/chat` or `/artifacts/draft`, `llama_server` may show as
  unavailable. That is expected because startup is lazy.
- The first model-backed request should start or attach to `llama-server`.
- `/tools/run` should succeed even before the model starts.
- `/artifacts/draft` now applies a deterministic heading repair when the model
  skips required sections.
- In that case, the response includes `repair_applied: true`,
  `original_draft`, and `missing_sections_before_repair`.

## MCP Smoke Test

Start the broker with the mock MCP config:

```bash
set -a
source ./.env.example
set +a

BITNET_MCP_CONFIG=broker/mcp_servers.mock.json \
BITNET_BROKER_PORT=8092 \
BITNET_LLAMA_PORT=8082 \
python3 run_broker.py
```

List configured MCP servers:

```bash
curl -s http://127.0.0.1:8092/tools/run \
  -H "Content-Type: application/json" \
  -d '{
    "tool_calls": [
      {
        "tool": "mcp_list_servers",
        "args": {}
      }
    ]
  }'
```

## Real Memory Smoke Test

After `npm install --prefix broker`, start the broker with the default local
config:

```bash
set -a
source ./.env.example
set +a

BITNET_BROKER_PORT=8093 \
BITNET_LLAMA_PORT=8083 \
python3 run_broker.py
```

Then verify the real Memory server through the broker:

```bash
curl -s http://127.0.0.1:8093/tools/run \
  -H "Content-Type: application/json" \
  -d '{
    "tool_calls": [
      {
        "tool": "mcp_list_servers",
        "args": {}
      },
      {
        "tool": "mcp_list_server_tools",
        "args": {
          "server": "memory"
        }
      }
    ]
  }'
```

List tools on the Memory adapter:

```bash
curl -s http://127.0.0.1:8092/tools/run \
  -H "Content-Type: application/json" \
  -d '{
    "tool_calls": [
      {
        "tool": "mcp_list_server_tools",
        "args": {
          "server": "memory"
        }
      }
    ]
  }'
```

Store and recall one fact through the MCP adapter:

```bash
curl -s http://127.0.0.1:8092/tools/run \
  -H "Content-Type: application/json" \
  -d '{
    "tool_calls": [
      {
        "tool": "mcp_memory_call",
        "args": {
          "tool": "remember_fact",
          "arguments": {
            "key": "project",
            "value": "BitNet broker"
          }
        }
      },
      {
        "tool": "mcp_memory_call",
        "args": {
          "tool": "recall_fact",
          "arguments": {
            "key": "project"
          }
        }
      }
    ]
  }'
```
