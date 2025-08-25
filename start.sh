set -euo pipefail
ENTRY="a1spreche.py"
if [ ! -f "$ENTRY" ]; then
  if [ -f "a1sprechen.py" ]; then ENTRY="a1sprechen.py"
  else echo "No entry file: a1spreche.py or a1sprechen.py"; ls -1 *.py; exit 1
  fi
fi
echo "Starting Streamlit with $ENTRY on port ${PORT:-8080}..."
exec python -m streamlit run "$ENTRY" --server.port="${PORT:-8080}" --server.address="0.0.0.0"
