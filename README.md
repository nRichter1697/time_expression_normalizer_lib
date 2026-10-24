# time_expression_normalizer_lib

Converts natural-language time references like `"now"`, `"today at 5"`, or `"in 3 days"` into UTC `datetime` objects.

```python
from time_expression_normalizer_lib import TimeNormalizer

from datetime import datetime, timezone

t = TimeNormalizer(lambda: datetime(2024, 3, 15, 10, 30, tzinfo=timezone.utc))
t.normalize("now")              # 2024-03-15 10:30:00+00:00
t.normalize("today")            # 2024-03-15 00:00:00+00:00
t.normalize("today at 5")       # 2024-03-15 05:00:00+00:00
t.normalize("today at 14:30")   # 2024-03-15 14:30:00+00:00
t.normalize("tomorrow at 8")    # 2024-03-16 08:00:00+00:00
t.normalize("yesterday")        # 2024-03-14 00:00:00+00:00
t.normalize("in 3 days")        # 2024-03-18 10:30:00+00:00
t.normalize("in 5 minutes")     # 2024-03-15 10:35:00+00:00
```

The constructor accepts a `clock` callable returning a `datetime`; it defaults to the real UTC wall clock. Passing a fake clock is how tests stay deterministic — and how you can pin behaviour in your own application if you need reproducibility.

Exported names: `TimeNormalizer`, `NormalizationError`.

## Why this exists

Timestamping user input — "log this at today at 5" — should not require a date library the size of a small framework. This library covers a fixed, small grammar so callers get `datetime` objects without pulling in anything the standard library doesn't already ship.

The trade-off is explicit: this is not a general NLP parser. It recognises the forms listed above, case-insensitively, and nothing else. Anything outside that grammar raises `NormalizationError`. The scope is deliberately smaller than what a casual reader might expect from "natural language"; that is the price of zero dependencies and tests that actually pass.

## Edge you will hit

`today at 5` means 05:00 on the current day, not 17:00. There is no 12-hour / AM-PM handling; hours are 0–23. If you need `5pm`, parse it yourself before calling — or add a layer that does so, but do not expect this library to guess.
