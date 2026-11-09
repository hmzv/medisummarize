from metrics import score


def test_corpus_cer_weights_by_reference_length():
    result = score([("a", "b"), ("longword", "longword")])
    assert result["cer"] == 1 / 9
    assert result["exact_match"] == 0.5


def test_empty_prediction_counts_as_error_and_digit_change_is_visible():
    result = score([("Napa 500", ""), ("dose 5", "dose 6")])
    assert result["samples"] == 2
    assert result["cer"] > 0
    assert result["digit_sequence_match"] == 0


def test_cer_can_exceed_one():
    assert score([("a", "abcdef")])["cer"] == 5
