from json import loads
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import re


# used to parse simple js object using json
# it adds quotes before every attribute, changes quote to double quote
# puts non json objects in quotes
def parse_js_object(string):
    s = re.search('{.*}', string, re.DOTALL).group(0)
    pattern = '( *)(\w+):( *)(.*)'
    ob = []
    for line in s.splitlines():
        m = re.search(pattern, line)
        if not m:
            ob.append(line)
            continue

        last = m.group(4).replace("'", "\"")
        if last[0] not in ["\"", "[", "{"]:
            # fixing non json attributes
            last = last.replace("\"", "\\\"")
            last = f"\"{last}\""
        parsed = f"{m.group(1)}\"{m.group(2)}\":{m.group(3)}{last}"
        ob.append(parsed)

    s = '\r\n'.join(ob)
    return loads(s)


# iterates over the first days of months in range
def iterate_months(start_date, end_date):
    first = datetime(start_date.year, start_date.month, 1)
    last = datetime(end_date.year, end_date.month, 1)
    while first <= last:
        yield first
        first += relativedelta(months=1)
