"""Persistent llama-server management for the local broker."""

from __future__ import annotations

import json
import subprocess
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import BrokerConfig


class LlamaServerRuntime:
    """Manage a persistent local llama-server process."""

    def __init__(self, config: BrokerConfig) -> None:
        self.config = config
        self._process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._log_handle = None

    @property
    def base_url(self) -> str:
        return "http://%s:%d" % (self.config.llama_host, self.config.llama_port)

    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def ensure_started(self) -> None:
        """Start llama-server if it is not already running."""
        with self._lock:
            if self.is_running():
                return
            if self._attach_to_existing_server():
                return
            self.start()

    def start(self) -> None:
        """Start the managed llama-server process."""
        if not self.config.llama_server_path.exists():
            raise FileNotFoundError(
                "llama-server binary not found at %s" % self.config.llama_server_path
            )
        if not self.config.model_path.exists():
            raise FileNotFoundError("model file not found at %s" % self.config.model_path)

        self.config.log_dir.mkdir(parents=True, exist_ok=True)
        log_path = self.config.log_dir / "llama-server.log"
        self._log_handle = log_path.open("a", encoding="utf-8")

        command = [
            str(self.config.llama_server_path),
            "-m",
            str(self.config.model_path),
            "-c",
            str(self.config.ctx_size),
            "-t",
            str(self.config.threads),
            "-n",
            str(self.config.n_predict),
            "--keep",
            str(self.config.n_keep),
            "-ngl",
            str(self.config.gpu_layers),
            "--temp",
            str(self.config.temperature),
            "--top-p",
            str(self.config.top_p),
            "--host",
            self.config.llama_host,
            "--port",
            str(self.config.llama_port),
            "--slots",
            "-cb",
        ]

        self._process = subprocess.Popen(
            command,
            cwd=str(self.config.workspace_root),
            stdout=self._log_handle,
            stderr=subprocess.STDOUT,
        )
        self._wait_until_ready(require_managed_process=True)

    def stop(self) -> None:
        """Terminate the managed llama-server if it is running."""
        with self._lock:
            if self._process is None:
                return
            if self.is_running():
                self._process.terminate()
                try:
                    self._process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                    self._process.wait(timeout=5)
            self._process = None
            if self._log_handle is not None:
                self._log_handle.close()
                self._log_handle = None

    def _attach_to_existing_server(self) -> bool:
        """Use an already-running llama-server if one answers on the target port."""
        try:
            self.health()
        except Exception:  # noqa: BLE001
            return False

        self._wait_until_ready(require_managed_process=False)
        return True

    def _wait_until_ready(self, require_managed_process: bool) -> None:
        deadline = time.time() + self.config.startup_timeout
        last_error = "llama-server did not answer /health"

        while time.time() < deadline:
            if require_managed_process and self._process is not None and self._process.poll() is not None:
                raise RuntimeError("llama-server exited before becoming ready")
            try:
                status = self.health()
                if status.get("status") == "ok":
                    return
                last_error = json.dumps(status)
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)
            time.sleep(1)

        raise TimeoutError("Timed out waiting for llama-server: %s" % last_error)

    def health(self) -> Dict[str, Any]:
        """Return the local llama-server health response."""
        request = urllib.request.Request(self.base_url + "/health", method="GET")
        try:
            with urllib.request.urlopen(request, timeout=2) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            payload = exc.read().decode("utf-8")
            if payload:
                return json.loads(payload)
            raise

    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Send one chat completion request to the managed llama-server."""
        self.ensure_started()

        payload = self.build_chat_payload(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )
        return self.chat_payload(payload)

    def build_chat_payload(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Build one llama-server chat completion payload."""
        return {
            "model": "bitnet-local",
            "messages": messages,
            "max_tokens": max_tokens or self.config.n_predict,
            "temperature": self.config.temperature if temperature is None else temperature,
            "top_p": self.config.top_p if top_p is None else top_p,
            "stream": False,
        }

    def chat_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send a prebuilt chat completion payload to the managed llama-server."""
        self.ensure_started()
        data = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            self.base_url + "/v1/chat/completions",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.config.request_timeout) as response:
            return json.loads(response.read().decode("utf-8"))
