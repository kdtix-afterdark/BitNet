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
- `POST /sessions`
- `POST /tools/run`
- `POST /chat`
- `POST /artifacts/draft`

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

The intended rollout order is:

1. Memory
2. Sequential Thinking
3. Context7
4. Reference servers
5. Major platform servers
6. QA / browser / delivery tooling

## Run

```bash
python run_broker.py \
  --model models/bitnet-b1.58-2B-4T-bf16/ggml-model-i2s-bitnet.gguf \
  --broker-port 8091 \
  --llama-port 8080 \
  --threads 2 \
  --ctx-size 2048
```

## Test Right Now

Use the old `run_inference.py` command only if you want a raw model sanity
check. Use the broker flow below if you want to test the new local broker
contract.

You can run these commands in a plain `zsh` terminal or in the VS Code
integrated terminal. For this MVP, they are equivalent.

### 1. Raw model sanity check

```bash
python run_inference.py \
  -m models/bitnet-b1.58-2B-4T-bf16/ggml-model-i2s-bitnet.gguf \
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
python run_broker.py \
  --model models/bitnet-b1.58-2B-4T-bf16/ggml-model-i2s-bitnet.gguf \
  --broker-port 8091 \
  --llama-port 8081 \
  --threads 1 \
  --ctx-size 512 \
  --n-predict 128
```

Open terminal 2 and run the broker checks.

Health before first model request:

```bash
curl -s http://127.0.0.1:8091/health
```

Deterministic tool execution:

```bash
curl -s http://127.0.0.1:8091/tools/run \
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
curl -s http://127.0.0.1:8091/chat \
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
BITNET_MCP_CONFIG=broker/mcp_servers.mock.json \
python run_broker.py \
  --model models/bitnet-b1.58-2B-4T-bf16/ggml-model-i2s-bitnet.gguf \
  --broker-port 8092 \
  --llama-port 8082 \
  --threads 1 \
  --ctx-size 512 \
  --n-predict 96
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
