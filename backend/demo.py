import fastf1

session = fastf1.get_session(2024, "United Kingdom", "Race")
session.load()

print(session.pos_data) # this is positional data, not full telemetry data