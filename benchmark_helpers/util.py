def time_to_str(time: float, unit: str) -> str:
    return f'{time:.2f} {unit}' if time is not None else 'N/A'