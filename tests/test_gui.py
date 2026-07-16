import sys

import asin_1688_roi.gui as gui


def test_cli_output_is_captured_for_windowed_gui():
    def runner(args):
        print("stdout:" + args[0])
        print("stderr", file=sys.stderr)
        return 1

    code, output = gui.run_cli_capture(["calculate"], runner=runner)

    assert code == 1
    assert "stdout:calculate" in output
    assert "stderr" in output
