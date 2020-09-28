import numpy as np
from scipy.stats import ttest_ind, mannwhitneyu


def deviation(data):
    if data["mean"] == 0 or data["max"] == 0:
        return 0

    diff = 1 - data["min"] / data["mean"]
    d = data["max"] / data["mean"] - 1
    if d > diff:
        diff = d

    # return "± %.2f%%" % (diff * 100)
    return diff


def compute_stats(values):
    q1 = np.percentile(values, 25)
    q3 = np.percentile(values, 75)
    lo = q1 - 1.5 * (q3 - q1)
    hi = q3 + 1.5 * (q3 - q1)

    r_values = []
    outliers = []

    for v in values:
        if lo <= v <= hi:
            r_values.append(v)
        else:
            outliers.append(v)

    data = {
        "min": float(np.min(r_values)),
        "max": float(np.max(r_values)),
        "mean": float(np.mean(r_values)),
        "var": float(np.var(r_values)),
        "std": float(np.std(r_values)),
        "median": float(np.median(r_values)),
        "x_outliers_data": outliers,
        "x_origin_data": values,
    }

    data["deviation"] = float(deviation(data))
    data["value"] = data["mean"]

    return data


def u_test(x, y):
    try:
        return mannwhitneyu(x=x, y=y,
                            alternative="two-sided")
    except:
        return None, None


def t_test(a, b):
    try:
        return ttest_ind(a=a, b=b, equal_var=False)
    except:
        return None, -0.0


def compute_stats_select_median_value(values):
    stats = compute_stats(values=values)
    return {
        **stats,
        "value": stats["median"]
    }


def compute_stats_select_min_value(values):
    stats = compute_stats(values=values)
    return {
        **stats,
        "value": stats["min"]
    }


def compute_system_performance_stats(values):
    return {
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "mean": float(np.mean(values)),
    }


def delta(current, previous):
    if current is None or previous is None or previous == 0:
        return 0.0
    return round(float((current - previous) / previous * 100), 2)
