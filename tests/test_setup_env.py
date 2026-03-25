import unittest
from unittest.mock import patch

import setup_env


class SetupEnvMainTests(unittest.TestCase):
    def test_main_skips_setup_gguf_install_and_runs_remaining_steps(self):
        with patch.object(setup_env, "setup_gguf") as setup_gguf, \
             patch.object(setup_env, "gen_code") as gen_code, \
             patch.object(setup_env, "compile") as compile_code, \
             patch.object(setup_env, "prepare_model") as prepare_model:
            setup_env.main()

        setup_gguf.assert_not_called()
        gen_code.assert_called_once_with()
        compile_code.assert_called_once_with()
        prepare_model.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
