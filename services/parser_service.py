from parsers.rockgig import parse_rockgig
# from parsers.another_source import parse_another_source
from db.operations.db_events import db_update_events

def parse_all_sources(user_id):
    events = []
    events.extend(parse_rockgig())
    # events.extend(parse_another_source())
    db_update_events(events, user_id)
    return events