from concurrent.futures import ThreadPoolExecutor
from threading import Event
from app.services.record_lock import record_write_lock


def test_same_record_writes_wait_and_nested_index_lock_does_not_deadlock():
    first_entered, release_first, second_entered = Event(), Event(), Event()
    def first():
        with record_write_lock("same-record"):
            with record_write_lock("same-record"):
                first_entered.set()
                assert release_first.wait(3)
    def second():
        assert first_entered.wait(3)
        with record_write_lock("same-record"):
            second_entered.set()
    with ThreadPoolExecutor(2) as pool:
        left, right = pool.submit(first), pool.submit(second)
        assert first_entered.wait(3)
        try:
            assert not second_entered.wait(0.05)
        finally:
            release_first.set()
        left.result(); right.result()
    assert second_entered.is_set()
