# Troubleshooting Guide

This document covers common errors, mistakes, and setup issues encountered in the SatTrade terminal.

## 1. SyntaxError: source code string cannot contain null bytes

**Issue**: This occurs if `src/preprocess/optical.py` or other files become corrupted with NUL characters.

**Fix**: Re-save the file in UTF-8 encoding. If the file is truncated, restore it from the repository or use the provided reconstruction script.

## 2. PermissionError: [WinError 32] (Windows Only)

**Issue**: During testing (`pytest`), Windows may fail to delete temporary directories because a database file (e.g., `catalog.db`) is still being accessed by a process.

**Fix**:

- Ensure all database connections are explicitly closed in your code.
- In tests, use a context manager or `try...finally` block to ensure cleanup happens after the file handle is released.
- Restart the development server if it's holding a lock on the file.

## 3. Risk Engine Assertion Errors

**Issue**: `test_gross_exposure_gate_blocks_breach` fails because it returns `sector` instead of `gross_exposure`.

**Fix**: Check `src/execution/risk_engine.py`. The gate order matters; ensure `gross_exposure` check is performed and reported correctly if multiple gates are breached.

## 4. Missing Native Dependencies (C++ Build Tools)

**Issue**: Installing `requirements.txt` fails on packages like `blazingmq-sdk-python` or `memray`.

**Fix**:

- Install [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) with the "Desktop development with C++" workload.
- Alternatively, use the pre-built Docker containers provided in the repository.

## 5. Global Intelligence Hub "Stuck Loading"

**Issue**: The frontend shows a loading spinner indefinitely.

**Fix**:

- Check if the backend server is running (`python src/api/server.py`).
- Verify WebSocket connection in the browser console (F12 -> Network -> WS).
- Ensure `.env` contains the correct `API_URL`.

## 6. Sentinel-2 Data Ingestion Failures

**Issue**: `403 Forbidden` or `401 Unauthorized`.

**Fix**:

- Ensure your `SENTINEL_HUB_CLIENT_ID` and `SECRET` are set in `.env`.
- Check if your quota has been exceeded on the Sentinel Hub dashboard.

