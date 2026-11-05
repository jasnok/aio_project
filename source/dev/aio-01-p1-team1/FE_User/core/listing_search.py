"""Submitted search conditions, independent of Streamlit widget reruns."""
STATE_KEY = "user-listing-search"

def submitted_search(location, deposit, rent, sort):
    result = {"sort": sort}
    if location != "전체":
        result["location"] = location
    for name, value in (("max_deposit", deposit), ("max_monthly_rent", rent)):
        if int(value) > 0:
            result[name] = int(value)
    return result
