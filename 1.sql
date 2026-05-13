CREATE EXTENSION postgis;

SELECT PostGIS_Version();

-- 1. Core tower table
CREATE TABLE towers (
    tower_id        SERIAL PRIMARY KEY,
    cell_id         BIGINT,
    operator        VARCHAR(20),
    mcc             INTEGER,
    mnc             INTEGER,
    radio_type      VARCHAR(10),
    frequency_band  INTEGER,
    latitude        DECIMAL(9,6),
    longitude       DECIMAL(9,6),
    geom            GEOGRAPHY(POINT, 4326),
    state_circle    VARCHAR(50),
    district        VARCHAR(50),
    avg_signal_dbm  INTEGER,
    sample_count    INTEGER,
    range_m         INTEGER,
    last_seen       DATE
);

-- 2. Crowd-sourced signal samples
CREATE TABLE signal_samples (
    sample_id       SERIAL PRIMARY KEY,
    tower_id        INTEGER REFERENCES towers(tower_id),
    signal_dbm      INTEGER,
    measured_at     TIMESTAMP,
    geom            GEOGRAPHY(POINT, 4326)
);

-- 3. Districts (for gap analysis)
CREATE TABLE districts (
    district_id     SERIAL PRIMARY KEY,
    district_name   VARCHAR(100),
    state_name      VARCHAR(100),
    population      INTEGER,
    area_sqkm       DECIMAL(10,2),
    geom            GEOGRAPHY(MULTIPOLYGON, 4326)
);

-- 4. TRAI QoS data
CREATE TABLE trai_qos (
    qos_id              SERIAL PRIMARY KEY,
    operator            VARCHAR(20),
    state_circle        VARCHAR(50),
    quarter             VARCHAR(10),
    avg_download_mbps   DECIMAL(6,2),
    avg_upload_mbps     DECIMAL(6,2),
    call_drop_rate      DECIMAL(5,2),
    complaint_count     INTEGER
);

CREATE INDEX idx_towers_geom ON towers USING GIST(geom);

ALTER TABLE towers ALTER COLUMN operator TYPE VARCHAR(50);
ALTER TABLE towers ALTER COLUMN radio_type TYPE VARCHAR(10);

SELECT operator, radio_type, COUNT(*) as tower_count
FROM towers
GROUP BY operator, radio_type
ORDER BY tower_count DESC;

-- Test: find all towers within 5km of Nagpur city centre
SELECT operator, radio_type, COUNT(*) as towers_nearby
FROM towers
WHERE ST_DWithin(
    geom,
    ST_SetSRID(ST_MakePoint(79.0882, 21.1458), 4326)::geography,
    5000
)
GROUP BY operator, radio_type
ORDER BY towers_nearby DESC;


SELECT state_circle, COUNT(*) as tower_count
FROM towers
WHERE state_circle IS NOT NULL
GROUP BY state_circle
ORDER BY tower_count DESC;

--Tower count per state per operator
SELECT 
    state_circle,
    operator,
    COUNT(*) as tower_count
FROM towers
WHERE operator IN ('Jio', 'Airtel', 'Vi', 'BSNL')
AND state_circle IS NOT NULL
GROUP BY state_circle, operator
ORDER BY state_circle, tower_count DESC;


--compute area from geometry
UPDATE districts
SET area_sqkm = ROUND(
    CAST(ST_Area(geom::geography) / 1000000 AS DECIMAL), 2
);

--Gap score
SELECT 
    t.state_circle,
    COUNT(*) AS total_towers,
    COUNT(*) FILTER (WHERE t.operator = 'Jio')    AS jio_towers,
    COUNT(*) FILTER (WHERE t.operator = 'Airtel') AS airtel_towers,
    COUNT(*) FILTER (WHERE t.operator = 'Vi')     AS vi_towers,
    COUNT(*) FILTER (WHERE t.operator = 'BSNL')   AS bsnl_towers,
    ROUND(COUNT(*)::decimal / MAX(d.area_sqkm), 4) AS towers_per_sqkm,
    ROUND(MAX(d.area_sqkm) / NULLIF(COUNT(*), 0), 2) AS sqkm_per_tower
FROM towers t
JOIN districts d ON t.state_circle = d.district_name
WHERE t.operator IN ('Jio', 'Airtel', 'Vi', 'BSNL')
AND t.state_circle IS NOT NULL
GROUP BY t.state_circle
ORDER BY towers_per_sqkm ASC;

--gap_score with rank
SELECT 
    state_circle,
    total_towers,
    jio_towers,
    airtel_towers,
    towers_per_sqkm,
    sqkm_per_tower,
    RANK() OVER (ORDER BY towers_per_sqkm ASC) AS gap_rank
FROM (
    SELECT 
        t.state_circle,
        COUNT(*) AS total_towers,
        COUNT(*) FILTER (WHERE t.operator = 'Jio')    AS jio_towers,
        COUNT(*) FILTER (WHERE t.operator = 'Airtel') AS airtel_towers,
        ROUND(COUNT(*)::decimal / MAX(d.area_sqkm), 4) AS towers_per_sqkm,
        ROUND(MAX(d.area_sqkm) / NULLIF(COUNT(*), 0), 2) AS sqkm_per_tower
    FROM towers t
    JOIN districts d ON t.state_circle = d.district_name
    WHERE t.operator IN ('Jio', 'Airtel', 'Vi', 'BSNL')
    AND t.state_circle IS NOT NULL
    GROUP BY t.state_circle
) sub
ORDER BY gap_rank ASC;

--5g Availability per state
SELECT 
    state_circle,
    COUNT(*) FILTER (WHERE radio_type = 'NR') AS towers_5g,
    COUNT(*) FILTER (WHERE radio_type = 'LTE') AS towers_4g,
    COUNT(*) FILTER (WHERE radio_type = 'UMTS') AS towers_3g,
    COUNT(*) FILTER (WHERE radio_type = 'GSM') AS towers_2g,
    COUNT(*) AS total_towers,
    ROUND(COUNT(*) FILTER (WHERE radio_type = 'NR') * 100.0 / NULLIF(COUNT(*), 0), 2) AS pct_5g
FROM towers
WHERE operator IN ('Jio', 'Airtel', 'Vi', 'BSNL')
AND state_circle IS NOT NULL
GROUP BY state_circle
ORDER BY pct_5g DESC;