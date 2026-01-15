#!/bin/bash

cd "$(dirname "$0")"

python3 src/app.py > /tmp/finance_graphrag_backend.log 2>&1 &
BACKEND_PID=$!
sleep 2

streamlit run src/streamlit_app.py

kill $BACKEND_PID 2>/dev/null
