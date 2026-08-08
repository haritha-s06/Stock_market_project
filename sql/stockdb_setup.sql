-- =====================================================
-- CREATE DATABASE
-- =====================================================
CREATE DATABASE StockDB;
GO


-- =====================================================
-- USE DATABASE
-- =====================================================
USE StockDB;
GO


-- =====================================================
-- DELETE OLD TABLE IF EXISTS
-- =====================================================
DROP TABLE IF EXISTS stock_data;
GO


-- =====================================================
-- CREATE CLEAN STOCK TABLE
-- =====================================================
CREATE TABLE stock_data (

    Date DATE,

    OpenPrice DECIMAL(10,2),

    High DECIMAL(10,2),

    Low DECIMAL(10,2),

    ClosePrice DECIMAL(10,2),

    Volume BIGINT,

    MA_20 DECIMAL(10,2),

    Trend VARCHAR(10)

);
GO


-- =====================================================
-- VERIFY TABLE STRUCTURE
-- =====================================================
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'stock_data';
GO


-- =====================================================
-- VIEW INSERTED DATA
-- =====================================================
SELECT TOP 100 *
FROM stock_data;
GO