from functools import wraps
from datetime import datetime

def filter_by_time_decorator(filter_func):
    @wraps(filter_func)
    def wrapper(events, *args, **kwargs):
        filtered_events = filter_func(events, *args, **kwargs)
        if "show_all_events" not in kwargs or not kwargs["show_all_events"]:
            current_time = datetime.now()
            filtered_events = [event for event in filtered_events if datetime.strptime(event["event_datetime"], "%Y-%m-%d %H:%M") > current_time]
        return filtered_events
    return wrapper