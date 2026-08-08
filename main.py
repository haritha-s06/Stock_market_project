"""
ETL pipeline controller.
This file only Connects the pipeline

    extract.py -> transform.py -> load.py
"""

from python.extract import (
    extract_live_stock,
    extract_history_stock
)
from python.transform import transform_data
from python.load import load_to_sql


def run_pipeline(symbol):

    # ── Live data: fetched and cleaned, but not stored in the database ──
    live_data = extract_live_stock(symbol)

    if live_data is not None and not live_data.empty:
        live_data = transform_data(live_data, keep_time=True)

    # ── Historical data: fetched, cleaned, and stored in the database ──
    history_data = extract_history_stock(symbol)

    if history_data is not None and not history_data.empty:
        history_data = transform_data(history_data, keep_time=False)
        load_to_sql(history_data)

    return live_data, history_data
