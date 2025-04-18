CREATE DATABASE csv_analyzer;
USE csv_analyzer;
SELECT * FROM uploaded_data;
SELECT * FROM uploaded_data_summary;
SELECT * FROM uploaded_data_missing
WHERE MissingCount > 0;
SELECT * FROM uploaded_data_correlation
ORDER BY ABS(Correlation) DESC;
SELECT * FROM uploaded_data_correlation
WHERE Feature1 <> Feature2
ORDER BY ABS(Correlation) DESC
LIMIT 5;
SELECT * FROM uploaded_data_correlation
WHERE Correlation = 0;



