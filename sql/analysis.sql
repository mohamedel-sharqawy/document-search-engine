-- 1. Total number of documents

SELECT COUNT(*) AS document_count
FROM documents;


-- 2. Missing values

SELECT
    SUM(CASE WHEN id IS NULL THEN 1 ELSE 0 END) AS missing_ids,
    SUM(CASE WHEN title IS NULL THEN 1 ELSE 0 END) AS missing_titles,
    SUM(CASE WHEN original_text IS NULL THEN 1 ELSE 0 END) AS missing_text,
    SUM(CASE WHEN cleaned_text IS NULL THEN 1 ELSE 0 END) AS missing_cleaned_text
FROM documents;


-- 3. Document length statistics

SELECT
    MIN(LENGTH(original_text)) AS min_length,
    MAX(LENGTH(original_text)) AS max_length,
    ROUND(AVG(LENGTH(original_text)), 2) AS avg_length
FROM documents;


-- 4. Longest documents

SELECT
    id,
    title,
    LENGTH(original_text) AS text_length
FROM documents
ORDER BY text_length DESC
LIMIT 10;