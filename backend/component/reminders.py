"""Meal-time estimates in the app's existing Asia/Manila (UTC+8) time basis."""
from datetime import datetime, timedelta
from statistics import median

DEFAULTS = {'Breakfast': 480, 'Lunch': 750, 'Dinner': 1140}

def learn_schedule(logs, now=None):
    now = now or datetime.utcnow() + timedelta(hours=8)
    result, details = {}, {}
    for meal, default in DEFAULTS.items():
        # One observation per day prevents a multi-item meal dominating the estimate.
        days = {}
        for log in logs:
            dt = log.logged_at
            if log.meal_type == meal and now - timedelta(days=28) <= dt <= now:
                minutes = dt.hour * 60 + dt.minute
                offset = (minutes - default + 720) % 1440 - 720
                days.setdefault(dt.date(), []).append(offset)
        observations = [median(values) for values in days.values()]
        learned = len(observations) >= 3
        minute = int(round((default + median(observations)) / 5) * 5) % 1440 if learned else default
        hour, mins = divmod(minute, 60)
        result[meal] = f'{hour % 12 or 12:02}:{mins:02} {"AM" if hour < 12 else "PM"}'
        details[meal] = {'source': 'learned' if learned else 'default', 'days': len(observations)}
    return {'times': result, 'details': details, 'timezone': 'Asia/Manila', 'minimum_days': 3}
