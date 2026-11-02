from app.rate_limit import SlidingWindowLimiter


def test_allows_up_to_the_limit_then_blocks():
    limiter = SlidingWindowLimiter(limit=3, window_seconds=60)
    assert [limiter.check("ip", now=t) for t in (0, 1, 2)] == [0, 0, 0]
    assert limiter.check("ip", now=3) == 57


def test_slots_free_up_as_the_window_moves():
    limiter = SlidingWindowLimiter(limit=2, window_seconds=60)
    limiter.check("ip", now=0)
    limiter.check("ip", now=10)
    assert limiter.check("ip", now=59) > 0
    assert limiter.check("ip", now=60) == 0


def test_each_key_has_its_own_window():
    limiter = SlidingWindowLimiter(limit=1, window_seconds=60)
    assert limiter.check("a", now=0) == 0
    assert limiter.check("b", now=0) == 0
    assert limiter.check("a", now=1) > 0
