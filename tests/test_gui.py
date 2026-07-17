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


def test_calculate_args_include_optional_config_and_fx():
    args = gui.build_calculate_args(
        input_path="input.xlsx",
        candidate_path="candidates.xlsx",
        output_path="result.xlsx",
        fx="7.1",
        config_path="roi_profile.json",
    )

    assert args == [
        "calculate",
        "--input",
        "input.xlsx",
        "--candidates",
        "candidates.xlsx",
        "--output",
        "result.xlsx",
        "--fx",
        "7.1",
        "--config",
        "roi_profile.json",
    ]
