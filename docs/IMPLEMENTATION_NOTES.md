# Arkrishitech implementation notes

## Sensor input
The current frontend uses the Web Serial API at 115200 baud. The Arduino sketch emits one JSON object per line with `moisture`, `soil_t`, and `ph`. The dashboard plots live bar/history readings. Without a connected serial device, it generates explicitly labelled simulation values locally. Simulation values are not written to the device readings database. Real device readings are saved to the selected field.

## Traditional knowledge assistant
`backend/app/kb.py` implements local retrieval over `backend/app/knowledge.json`. It tokenizes and scores titles, keywords, and practice text, retrieves relevant entries, returns their source and review status, and declines to invent advice when no match is found. It is retrieval-grounded and offline; it is not a fine-tuned or generative LLM.

## Verification limits
The web application and backend tests can be checked in software, but the Arduino sketch, sensor wiring, calibration values, and USB serial behaviour still require testing on the team's actual hardware. The existing knowledge records are broad South Asian community practices and are marked pending review; they must not be presented as verified local Indigenous knowledge until reviewed with consent and attribution.
