from app import add, multiply


def test_add() -> None:
    assert add(2, 3) == 5

def test_multiply_positive() -> None:
    assert multiply(2, 3) == 6


def test_multiply_zero() -> None:
    assert multiply(0, 5) == 0
    assert multiply(7, 0) == 0


def test_multiply_negative() -> None:
    assert multiply(-3, 4) == -12
    assert multiply(6, -2) == -12
    assert multiply(-5, -2) == 10
