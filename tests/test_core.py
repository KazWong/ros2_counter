from ros2_counter import add_integers


def test_add_integers() -> None:
    assert add_integers(2, 3) == 5
