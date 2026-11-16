#!/usr/bin/env bash
# One command start for Mac / Linux / the UNO Q:  ./run.sh
set -e
cd "$(dirname "$0")"
[ -d venv ] || python3 -m venv venv
. venv/bin/activate
pip install -q -r backend/requirements.txt
cd backend
echo "Open http://localhost:8000  (phones on the same Wi-Fi: http://<this-computer-address>:8000)"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
