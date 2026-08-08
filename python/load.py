"""
Load step of the ETL pipeline.

Connects to the local SQL Server database and inserts the
processed historical stock data into the stock_data table.
"""

from sqlalchemy import create_engine
import urllib

def get_engine():
    # Builds and URL-encodes the SQL Server connection string.
    # quote_plus() makes special characters safe to use in a connection URL.
    connection_string = urllib.parse.quote_plus(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=HARI6104\\MSSQLSERVER1;"
        "DATABASE=StockDB;"
        "Trusted_Connection=yes;"
    )

    # mssql+pyodbc tells SQLAlchemy to talk to SQL Server using pyodbc.
    engine = create_engine(
        "mssql+pyodbc:///?odbc_connect=%s" % connection_string
    )

    return engine

# Created once and reused for every insert, instead of reconnecting
# to the database every time load_to_sql() runs.
engine = get_engine()

def load_to_sql(stock_data):
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
            if_exists="append",   # add new rows without deleting old ones
            index=False            # don't insert the pandas index as a column
        )

        print("Data inserted successfully")

    except Exception as e:
        print("SQL INSERT ERROR:")
        print(e)
