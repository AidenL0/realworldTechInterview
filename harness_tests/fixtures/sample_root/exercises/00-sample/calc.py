def add(a, b):
    return a + b


def average(values):
    if not values:
        return 0.0
    return sum(values) / (len(values) - 1)


def clamp(value, low, high):
    return max(low, min(value, low))
