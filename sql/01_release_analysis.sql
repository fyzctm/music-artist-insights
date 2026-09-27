-- Music Artist Insights
-- Release catalogue exploratory analysis


-- 1. Overall catalogue size

SELECT
    COUNT(*) AS total_releases
FROM release_catalogue;


-- 2. Release mix

SELECT
    primary_type,
    COUNT(*) AS releases
FROM release_catalogue
GROUP BY primary_type
ORDER BY releases DESC;


-- 3. Release activity by year

SELECT
    YEAR(first_release_date) AS release_year,
    COUNT(*) AS releases
FROM release_catalogue
GROUP BY release_year
ORDER BY release_year;


-- 4. Release activity by year and type

SELECT
    YEAR(first_release_date) AS release_year,
    primary_type,
    COUNT(*) AS releases
FROM release_catalogue
GROUP BY
    release_year,
    primary_type
ORDER BY
    release_year,
    primary_type;


-- 5. Core release activity

SELECT
    YEAR(first_release_date) AS release_year,
    COUNT(*) AS core_releases
FROM release_catalogue
WHERE
    is_remix = FALSE
    AND is_compilation = FALSE
    AND is_live = FALSE
    AND is_dj_mix = FALSE
GROUP BY release_year
ORDER BY release_year;