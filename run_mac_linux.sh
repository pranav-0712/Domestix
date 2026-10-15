#!/bin/bash
echo "==============================================================================="
echo "                DOMESTIX - SMART HOUSEHOLD MANAGEMENT APPLICATION"
echo "   Saee Takale (5185) | Ayusha Kale (3205) | Pranav Joshi (5208) | Vaishnavi Thite (5188)"
echo "==============================================================================="

if command -v python3 &>/dev/null; then
    PY_CMD="python3"
elif command -v python &>/dev/null; then
    PY_CMD="python"
else
    echo "[!] Python not found. Opening standalone HTML mode..."
    if command -v xdg-open &>/dev/null; then
        xdg-open login.html
    elif command -v open &>/dev/null; then
        open login.html
    fi
    exit 0
fi

echo "[*] Installing dependencies..."
$PY_CMD -m pip install -r requirements.txt --quiet

echo "[*] Opening browser..."
if command -v xdg-open &>/dev/null; then
    xdg-open "http://127.0.0.1:8000/login.html" &
elif command -v open &>/dev/null; then
    open "http://127.0.0.1:8000/login.html" &
fi

echo "[*] Starting FastAPI Server on http://127.0.0.1:8000 ..."
$PY_CMD -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
