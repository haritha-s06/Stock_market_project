"""
Load step of the ETL pipeline.

Inserts processed historical stock data into a local SQL Server database.
If the database (or the ODBC driver) is not available - for example when the
app is deployed on Streamlit Cloud - this step is skipped safely and the
dashboard keeps working.
"""

import urllib.parse
from sqlalchemy import create_engine


def get_engine():
    # Builds and URL-encodes the SQL Server connection string.
    connection_string = urllib.parse.quote_plus(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=HARI6104\\MSSQLSERVER1;"
        "DATABASE=StockDB;"
        "Trusted_Connection=yes;"
    )
    return create_engine("mssql+pyodbc:///?odbc_connect=%s" % connection_string)


# Created once and reused. If pyodbc is not installed (cloud), engine = None.
try:
    engine = get_engine()
except Exception as e:
    print("SQL Server not available, database saving disabled:", e)
    engine = None


def load_to_sql(stock_data):
    if engine is None:
        print("Skipping database insert (no database connection).")
        return

    try:
        if stock_data is None or stock_data.empty:
            print("DataFrame is empty")
            return

        print("Shows first 5 rows of dataframe inserted to SQL:")
        print(stock_data.head())
        print("Shows dataframe dimensions : ", stock_data.shape)

        stock_data.to_sql(
            name="stock_data",
            con=engine,
            if_exists="append",
            index=False,
        )
        print("Data inserted successfully")

    except Exception as e:
        print("SQL INSERT ERROR:")
        print(e)
