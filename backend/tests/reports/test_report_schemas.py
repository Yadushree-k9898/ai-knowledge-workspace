import pytest
from pydantic import ValidationError

from app.modules.reports.schemas import CreateReportRequest


def test_report_request_strips_title_and_instructions():
    request = CreateReportRequest(
        title="  Project brief  ",
        report_type="RESEARCH_BRIEF",
        instructions="  Highlight unanswered questions.  ",
    )

    assert request.title == "Project brief"
    assert request.instructions == "Highlight unanswered questions."


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "x", "report_type": "SUMMARY"},
        {"title": "Valid title", "report_type": "CUSTOM"},
        {"title": "   ", "report_type": "SUMMARY"},
        {"title": "Valid title", "report_type": "SUMMARY", "instructions": "x" * 5001},
    ],
)
def test_report_request_rejects_invalid_values(payload):
    with pytest.raises(ValidationError):
        CreateReportRequest(**payload)
