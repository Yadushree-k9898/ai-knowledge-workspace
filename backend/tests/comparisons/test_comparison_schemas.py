import pytest
from pydantic import ValidationError

from app.modules.comparisons.schemas import CreateComparisonRequest


def test_comparison_instructions_are_trimmed():
    request = CreateComparisonRequest(
        document_ids=[1, 2],
        instructions="  Compare the conclusions.  ",
    )

    assert request.instructions == "Compare the conclusions."


def test_comparison_allows_two_to_five_distinct_documents():
    assert CreateComparisonRequest(document_ids=[1, 2]).document_ids == [1, 2]
    assert len(CreateComparisonRequest(document_ids=[1, 2, 3, 4, 5]).document_ids) == 5


@pytest.mark.parametrize("document_ids", [[1], [1, 2, 3, 4, 5, 6], [1, 1]])
def test_comparison_rejects_invalid_document_selections(document_ids):
    with pytest.raises(ValidationError):
        CreateComparisonRequest(document_ids=document_ids)
