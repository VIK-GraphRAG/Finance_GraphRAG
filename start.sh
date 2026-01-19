
cd "$(dirname "$0")"

# Kill any existing processes on port 8000
echo "🧹 Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 1

# Start backend with unbuffered output
echo "🚀 Starting FastAPI backend..."
python3 -u src/app.py > /tmp/finance_graphrag_backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Backend failed to start. Check /tmp/finance_graphrag_backend.log"
        tail -20 /tmp/finance_graphrag_backend.log
        exit 1
    fi
    sleep 1
done

# Start Streamlit
echo "🎨 Starting Streamlit frontend..."
streamlit run src/streamlit_app.py

# Cleanup on exit
echo "🛑 Shutting down backend..."
kill $BACKEND_PID 2>/dev/null
