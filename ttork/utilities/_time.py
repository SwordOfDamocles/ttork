def format_age(seconds: int) -> str:
    """Format the age of a resource in seconds to a human readable string.

    Will display the largest unit of time that is greater than zero, and the
    next unit of time. For example, 1d:02h, 2h:30m, 5m:10s, 30s.
    """
    (days, remainder) = divmod(seconds, 86400)
    (hours, remainder) = divmod(remainder, 3600)
    (minutes, seconds) = divmod(remainder, 60)

    if days > 0:
        return f"{days:}d:{hours:02}h"
    elif hours > 0:
        return f"{hours:}h:{minutes:02}m"
    elif minutes > 0:
        return f"{minutes:}m:{seconds:02}s"
    else:
        return f"{seconds:02}s"
