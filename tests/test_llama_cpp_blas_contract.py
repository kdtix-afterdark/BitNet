"""
Regression guard for the llama.cpp BLAS I2_S and Metal/Accelerate compatibility
patches applied to 3rdparty/llama.cpp.

These tests verify the *source-level contract* — that the safety patches are
present and correct — without requiring a full C/Metal compile.  They read the
patched source files directly and assert on the expected text contents.

Patch sources:
  - Metal/Accelerate: docs/patches/llama.cpp-known-good-metal.patch
                      (branch codex/metal-build-config)
  - BLAS I2_S guard:  ckreager/llama.cpp codex/blas-i2s-fix
                      (upstream: Eddie-Wang1120/llama.cpp#19)
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent
_LLAMA_CPP = _REPO_ROOT / "3rdparty" / "llama.cpp"

# Skip the whole module if the submodule is not initialised (e.g. CI that does
# not check out submodules).  Local UAT machines are expected to have it.
_SUBMODULE_PRESENT = (_LLAMA_CPP / "ggml").is_dir()


@unittest.skipUnless(_SUBMODULE_PRESENT, "3rdparty/llama.cpp submodule not initialised")
class TestBlasI2SGuard(unittest.TestCase):
    """BLAS I2_S type guard in ggml-blas.cpp."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.blas_src = (_LLAMA_CPP / "ggml" / "src" / "ggml-blas.cpp").read_text(
            encoding="utf-8"
        )

    def test_i2s_type_exclusion_present(self) -> None:
        """The guard that declines GGML_TYPE_I2_S for MUL_MAT must be present."""
        self.assertIn("GGML_TYPE_I2_S", self.blas_src)

    def test_i2s_exclusion_before_contiguous_check(self) -> None:
        """I2_S check must appear before the ggml_is_contiguous(src0) guard."""
        i2s_pos = self.blas_src.find("src0->type != GGML_TYPE_I2_S")
        contiguous_pos = self.blas_src.find("ggml_is_contiguous(src0)")
        self.assertGreater(i2s_pos, 0, "I2_S guard not found")
        self.assertGreater(contiguous_pos, 0, "contiguous guard not found")
        self.assertLess(
            i2s_pos,
            contiguous_pos,
            "I2_S check must come before ggml_is_contiguous(src0)",
        )

    def test_i2s_guard_is_negated_exclusion(self) -> None:
        """The guard must be a != comparison (exclusion, not inclusion)."""
        self.assertIn("src0->type != GGML_TYPE_I2_S", self.blas_src)

    def test_veclib_cblas_include(self) -> None:
        """ggml-blas.cpp must use vecLib/cblas.h (not Accelerate/Accelerate.h)."""
        self.assertIn("vecLib/cblas.h", self.blas_src)
        self.assertNotIn("Accelerate/Accelerate.h", self.blas_src)


@unittest.skipUnless(_SUBMODULE_PRESENT, "3rdparty/llama.cpp submodule not initialised")
class TestMetalCompatibilityPatches(unittest.TestCase):
    """Metal and Accelerate compatibility patches in ggml-metal.m and ggml.c."""

    def test_metal_device_nil_guard_present(self) -> None:
        """ggml-metal.m must guard against nil MTLDevice before dereferencing."""
        metal_src = (_LLAMA_CPP / "ggml" / "src" / "ggml-metal.m").read_text(
            encoding="utf-8"
        )
        self.assertIn("ctx->mtl_device == nil", metal_src)

    def test_ggml_c_uses_vdsp_not_accelerate(self) -> None:
        """ggml.c must include vecLib/vDSP.h instead of Accelerate/Accelerate.h."""
        ggml_c_src = (_LLAMA_CPP / "ggml" / "src" / "ggml.c").read_text(
            encoding="utf-8"
        )
        self.assertIn("vecLib/vDSP.h", ggml_c_src)
        self.assertNotIn("Accelerate/Accelerate.h", ggml_c_src)


if __name__ == "__main__":
    unittest.main()
