from openpyxl import load_workbook

from asin_1688_roi.exporter import write_workbook
from asin_1688_roi.models import CandidateProduct


def test_exported_untrusted_text_is_not_written_as_excel_formula(tmp_path):
    output = tmp_path / "result.xlsx"
    candidate = CandidateProduct(
        asin="B000000001",
        search_keyword="测试",
        title="=1+1",
    )

    write_workbook(output, targets=[], candidates=[candidate], results=[])

    workbook = load_workbook(output, read_only=True, data_only=False)
    try:
        assert workbook.properties.creator == "asin-1688-roi-tool"
        cell = workbook["1688候选"]["D2"]
        assert cell.value == "=1+1"
        assert cell.data_type == "s"
    finally:
        workbook.close()
