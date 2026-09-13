"""The authorized assumptions used only for the result-table boundaries."""
import numpy as np


def solve_next_cycle(solver, price, load, pv, previous_end):
    """Repeat the given PV profile and solve one more daily cycle."""
    fit, actions, stored = solver(price, load, pv)
    assert abs(stored[0] - previous_end) < 1e-6
    assert abs(stored[-1] - stored[0]) < 1e-6
    return fit, actions, stored


def extend_pv_hours(forecasts):
    """Carry hours 1..18; extend hours 19..24 by seven-day matching-hour means."""
    forecasts = np.asarray(forecasts, dtype=float)
    assert forecasts.shape == (365, 4, 24)
    carried = forecasts[-1, 3, 6:]
    estimated = forecasts[-7:, 0, 18:].mean(axis=0)
    hourly = np.r_[carried, estimated]
    assert np.isfinite(hourly).all() and (hourly >= 0).all()
    return hourly


def match_template_day(today, next_first):
    """Match 00:10..next-day 00:10 to the original 144-column template."""
    today = np.asarray(today, dtype=float)
    assert today.shape == (144,) and np.isfinite(today).all()
    # next_first must come from the next day's plan, never an implicit wrap.
    return today[1:].tolist() + [next_first]
