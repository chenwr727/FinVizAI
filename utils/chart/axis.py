import math


def scale_nice_val(val_max: float, val_min: float, split_number: int = 5):
    span = val_max - val_min
    interval = nice(span / split_number)
    interval_precision = get_interval_precision(interval)

    nice_val_max = round_number(math.ceil(val_max / interval) * interval, interval_precision)
    nice_val_min = round_number(math.floor(val_min / interval) * interval, interval_precision)

    return max(nice_val_max, val_max), min(nice_val_min, val_min)


def nice(val: float):
    exponent = math.floor(math.log10(abs(val)))
    exp10 = 10**exponent
    f = val / exp10

    if f < 1.5:
        nf = 1
    elif f < 2.5:
        nf = 2
    elif f < 4:
        nf = 3
    elif f < 7:
        nf = 5
    else:
        nf = 10

    result = nf * exp10
    return result


def get_interval_precision(interval):
    s = "{0:.10f}".format(interval).rstrip("0").split(".")
    return len(s[1]) if len(s) > 1 else 0 + 2


def round_number(value, precision):
    if precision == 0:
        return int(round(value))
    scale = 10**precision
    return round(value * scale) / scale
