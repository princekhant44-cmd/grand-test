"""Profile rules the model file cannot express."""
from datetime import date

from kirak.core.exceptions import ValidationError

MINIMUM_AGE_YEARS = 18


def _age_in_years(born: date, today: date) -> int:
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def _check_adult(payload):
    """Sync hook: raising here refuses the create or update."""
    born = (payload.get("data") or {}).get("date_of_birth")
    if not born:
        return payload
    try:
        born_on = date.fromisoformat(str(born)[:10])
    except ValueError:
        return payload  # the model's own date validation reports a malformed value
    if _age_in_years(born_on, date.today()) < MINIMUM_AGE_YEARS:
        raise ValidationError(f"A profile must belong to someone who is at least {MINIMUM_AGE_YEARS} years old")
    return payload


def register(kirak):
    kirak.on("profiles").hook("before_create")(_check_adult)
    kirak.on("profiles").hook("before_update")(_check_adult)
