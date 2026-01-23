import sys
import os
import ef_py

print(f"ef_py file: {ef_py.__file__}")
print("InstrumentState members:")
for m in dir(ef_py.InstrumentState):
    if not m.startswith("_"):
        print(f"  {m}")

print(f"\nHas on_runway? {'on_runway' in dir(ef_py.InstrumentState)}")
print(f"Has gear_stress? {'gear_stress' in dir(ef_py.InstrumentState)}")
print(f"Has lat? {'lat' in dir(ef_py.InstrumentState)}")
