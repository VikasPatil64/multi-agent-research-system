from rate_limiter import get_remaining_quota, limiter

print(f"Remaining from function: {get_remaining_quota()}")
print(f"Daily used from limiter: {limiter.daily_used}")
print(f"Daily limit: {limiter.daily_limit}")