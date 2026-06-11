from datetime import datetime, timezone

now = datetime.now(timezone.utc)
reset = datetime(now.year, now.month, now.day + 1, 0, 0, 0, tzinfo=timezone.utc)
time_diff = reset - now
hours = time_diff.seconds // 3600
minutes = (time_diff.seconds % 3600) // 60

print("="*40)
print("QUOTA RESET INFORMATION")
print("="*40)
print(f"Current UTC time: {now.strftime('%H:%M:%S')}")
print(f"Quota resets at: 00:00 UTC")
print(f"Time remaining: {hours} hours and {minutes} minutes")
print("="*40)

# Also show your local time
from datetime import datetime as local_dt
print(f"\nYour local time: {local_dt.now().strftime('%H:%M:%S')}")
print(f"Reset in your local time: {(local_dt.now() + time_diff).strftime('%H:%M')} tomorrow")