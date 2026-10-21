from calc import average, clamp


def test_average_empty_list():
    assert average([]) == 0.0


def test_average_single():
    assert average([5]) == 5


def test_clamp_inside_range():
    assert clamp(5, 0, 10) == 5
