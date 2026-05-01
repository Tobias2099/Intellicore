from intellicore_training.policy import StridePrefetchPolicy


def test_stride_policy_predicts_next_stride_address() -> None:
    policy = StridePrefetchPolicy()
    decision = policy.predict_next(current_address=0x1080, previous_address=0x1040)

    assert decision.address == 0x10C0
