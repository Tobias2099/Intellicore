from intellicore_training.rewards import score_transition


def test_useful_prefetch_reward_beats_wasted_prefetch() -> None:
    useful = score_transition(hit=True, prefetch_outcome="useful", eviction_caused_miss=False)
    wasted = score_transition(hit=True, prefetch_outcome="wasted", eviction_caused_miss=False)

    assert useful > wasted
