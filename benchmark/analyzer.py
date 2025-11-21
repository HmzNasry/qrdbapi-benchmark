import numpy as np


def calculate_stats(durations: list[float], remove_outliers: bool = True) -> dict | None:
    if not durations:
        return None

    data = np.array(durations)
    original_count = len(data)

    if remove_outliers and original_count > 4:
        # Calculate IQR (Interquartile Range)
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1
        
        upper_bound = q3 + (1.5 * iqr)
        lower_bound = q1 - (1.5 * iqr)
        
        clean_data = data[(data >= lower_bound) & (data <= upper_bound)]
    else:
        clean_data = data

    if len(clean_data) == 0:
        return None

    return {
        "count": len(clean_data),
        "outliers_removed": original_count - len(clean_data),
        "min": float(np.min(clean_data)),
        "max": float(np.max(clean_data)),
        "mean": float(np.mean(clean_data)),
        "median": float(np.median(clean_data)),
        "p95": float(np.percentile(clean_data, 95)),
        "p99": float(np.percentile(clean_data, 99)),
        "std_dev": float(np.std(clean_data))
    }
