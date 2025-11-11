-- TimescaleDB Grafana Query Examples for Odds Tracker
-- All queries assume $__timeFilter macro for time range filtering in Grafana


#Query 1-2:  Table panel
#Query 3-4:  Time series (line graph)
#Query 5:    Table with colors/thresholds
#Query 6:    Stat panel or bar gauge
#Query 7:    Table panel
#Query 8-9:  Time series with dual axis
#Query 10:   Bar chart
#Query 11:   Time series with annotations
#Query 12:   Gauge or stat panel
#Query 13:   Table with alert thresholds
#Query 14-15: Stat panels
#



-- ====================
-- 1. LATEST ODDS BY BOOKMAKER
-- Shows the most recent odds for each event/bookmaker/market combination
-- ====================
SELECT 
    timestamp AS time,
    event_id,
    bookmaker,
    offer_type,
    choice,
    price,
    point
FROM eventoffer
WHERE timestamp = (
    SELECT MAX(timestamp) 
    FROM eventoffer AS eo2 
    WHERE eo2.event_id = eventoffer.event_id 
      AND eo2.bookmaker = eventoffer.bookmaker
      AND eo2.offer_type = eventoffer.offer_type
      AND eo2.choice = eventoffer.choice
)
ORDER BY timestamp DESC;


-- ====================
-- 2. ODDS MOVEMENT OVER TIME FOR SPECIFIC EVENT
-- Track how odds change over time for a single event
-- Variables: $event_id, $offer_type
-- ====================
SELECT 
    timestamp AS time,
    bookmaker,
    choice,
    price,
    point
FROM eventoffer
WHERE event_id = '$event_id'
  AND offer_type = '$offer_type'
  AND $__timeFilter(timestamp)
ORDER BY timestamp ASC;


-- ====================
-- 3. ODDS SPREAD COMPARISON (Best vs Worst Price)
-- Find arbitrage opportunities by comparing bookmaker prices
-- Variables: $event_id, $offer_type, $choice
-- ====================
WITH latest_odds AS (
    SELECT DISTINCT ON (bookmaker)
        timestamp AS time,
        bookmaker,
        price
    FROM eventoffer
    WHERE event_id = '$event_id'
      AND offer_type = '$offer_type'
      AND choice = '$choice'
    ORDER BY bookmaker, timestamp DESC
)
SELECT 
    time,
    MAX(price) AS best_price,
    MIN(price) AS worst_price,
    MAX(price) - MIN(price) AS spread,
    (MAX(price) - MIN(price)) / MIN(price) * 100 AS spread_percentage
FROM latest_odds
GROUP BY time;


-- ====================
-- 4. TIME BUCKETED AVERAGE ODDS
-- Average price across all bookmakers over time intervals
-- Variables: $event_id, $offer_type, $choice, $interval (e.g., '1 hour')
-- ====================
SELECT 
    time_bucket('$interval', timestamp) AS time,
    AVG(price) AS avg_price,
    MIN(price) AS min_price,
    MAX(price) AS max_price,
    COUNT(*) AS sample_count
FROM eventoffer
WHERE event_id = '$event_id'
  AND offer_type = '$offer_type'
  AND choice = '$choice'
  AND $__timeFilter(timestamp)
GROUP BY time
ORDER BY time ASC;


-- ====================
-- 5. BOOKMAKER COMPARISON TABLE
-- Latest odds from each bookmaker for comparison
-- Variables: $event_id, $offer_type
-- ====================
WITH ranked_offers AS (
    SELECT 
        bookmaker,
        choice,
        price,
        point,
        timestamp,
        ROW_NUMBER() OVER (PARTITION BY bookmaker, choice ORDER BY timestamp DESC) AS rn
    FROM eventoffer
    WHERE event_id = '$event_id'
      AND offer_type = '$offer_type'
)
SELECT 
    bookmaker,
    choice,
    price,
    point,
    timestamp AS last_updated
FROM ranked_offers
WHERE rn = 1
ORDER BY choice, price DESC;


-- ====================
-- 6. ODDS VOLATILITY INDEX
-- Measure how frequently odds change for each bookmaker
-- Variables: $event_id, $offer_type
-- ====================
SELECT 
    bookmaker,
    choice,
    COUNT(DISTINCT timestamp) AS change_count,
    MAX(price) - MIN(price) AS price_range,
    STDDEV(price) AS price_stddev,
    MAX(timestamp) AS last_change
FROM eventoffer
WHERE event_id = '$event_id'
  AND offer_type = '$offer_type'
  AND $__timeFilter(timestamp)
GROUP BY bookmaker, choice
ORDER BY change_count DESC;


-- ====================
-- 7. EVENT SUMMARY WITH ACTIVE MARKETS
-- List all events with their market counts
-- ====================
SELECT 
    se.id,
    se.home_team,
    se.away_team,
    se.sport_title,
    se.commence_time,
    COUNT(DISTINCT eo.offer_type) AS market_types,
    COUNT(DISTINCT eo.bookmaker) AS bookmaker_count,
    MAX(eo.timestamp) AS last_odds_update
FROM sportevent se
LEFT JOIN eventoffer eo ON se.id = eo.event_id
GROUP BY se.id, se.home_team, se.away_team, se.sport_title, se.commence_time
ORDER BY se.commence_time DESC;


-- ====================
-- 8. PRICE MOVEMENT VELOCITY
-- Calculate rate of change in odds
-- Variables: $event_id, $offer_type, $choice
-- ====================
WITH price_changes AS (
    SELECT 
        timestamp,
        price,
        LAG(price) OVER (ORDER BY timestamp) AS prev_price,
        LAG(timestamp) OVER (ORDER BY timestamp) AS prev_timestamp
    FROM eventoffer
    WHERE event_id = '$event_id'
      AND offer_type = '$offer_type'
      AND choice = '$choice'
      AND bookmaker = '$bookmaker'
    ORDER BY timestamp
)
SELECT 
    timestamp AS time,
    price,
    prev_price,
    price - prev_price AS price_delta,
    EXTRACT(EPOCH FROM (timestamp - prev_timestamp)) / 3600 AS hours_elapsed,
    (price - prev_price) / NULLIF(EXTRACT(EPOCH FROM (timestamp - prev_timestamp)) / 3600, 0) AS velocity_per_hour
FROM price_changes
WHERE prev_price IS NOT NULL
ORDER BY timestamp ASC;


-- ====================
-- 9. FIRST vs LAST ODDS COMPARISON
-- Opening lines vs current lines
-- Variables: $event_id
-- ====================
WITH first_odds AS (
    SELECT DISTINCT ON (bookmaker, offer_type, choice)
        bookmaker,
        offer_type,
        choice,
        price AS opening_price,
        timestamp AS opening_time
    FROM eventoffer
    WHERE event_id = '$event_id'
    ORDER BY bookmaker, offer_type, choice, timestamp ASC
),
last_odds AS (
    SELECT DISTINCT ON (bookmaker, offer_type, choice)
        bookmaker,
        offer_type,
        choice,
        price AS current_price,
        timestamp AS current_time
    FROM eventoffer
    WHERE event_id = '$event_id'
    ORDER BY bookmaker, offer_type, choice, timestamp DESC
)
SELECT 
    f.bookmaker,
    f.offer_type,
    f.choice,
    f.opening_price,
    l.current_price,
    l.current_price - f.opening_price AS price_movement,
    (l.current_price - f.opening_price) / f.opening_price * 100 AS movement_percentage,
    f.opening_time,
    l.current_time
FROM first_odds f
JOIN last_odds l ON f.bookmaker = l.bookmaker 
                 AND f.offer_type = l.offer_type 
                 AND f.choice = l.choice
ORDER BY f.offer_type, ABS(l.current_price - f.opening_price) DESC;


-- ====================
-- 10. BOOKMAKER UPDATE FREQUENCY
-- How often each bookmaker updates their odds
-- Variables: $interval (e.g., '6 hours')
-- ====================
SELECT 
    time_bucket('$interval', timestamp) AS time,
    bookmaker,
    COUNT(*) AS update_count,
    COUNT(DISTINCT event_id) AS events_updated
FROM eventoffer
WHERE $__timeFilter(timestamp)
GROUP BY time, bookmaker
ORDER BY time DESC, update_count DESC;


-- ====================
-- 11. SHARP MONEY INDICATOR
-- Detect when multiple bookmakers move odds in same direction
-- Variables: $event_id, $offer_type, $choice, $threshold (e.g., 0.1)
-- ====================
WITH price_movements AS (
    SELECT 
        bookmaker,
        timestamp,
        price,
        LAG(price) OVER (PARTITION BY bookmaker ORDER BY timestamp) AS prev_price
    FROM eventoffer
    WHERE event_id = '$event_id'
      AND offer_type = '$offer_type'
      AND choice = '$choice'
)
SELECT 
    timestamp AS time,
    bookmaker,
    price,
    prev_price,
    price - prev_price AS movement
FROM price_movements
WHERE ABS(price - prev_price) > $threshold
  AND prev_price IS NOT NULL
ORDER BY timestamp DESC;


-- ====================
-- 12. MARKET EFFICIENCY (Implied Probability Total)
-- Check if bookmaker odds create over-round (vig)
-- Variables: $event_id, $offer_type
-- ====================
WITH latest_h2h AS (
    SELECT DISTINCT ON (bookmaker, choice)
        bookmaker,
        choice,
        price,
        1.0 / price AS implied_probability
    FROM eventoffer
    WHERE event_id = '$event_id'
      AND offer_type = 'h2h'
    ORDER BY bookmaker, choice, timestamp DESC
)
SELECT 
    bookmaker,
    SUM(implied_probability) AS total_probability,
    (SUM(implied_probability) - 1.0) * 100 AS overround_percentage,
    CURRENT_TIMESTAMP AS calculated_at
FROM latest_h2h
GROUP BY bookmaker
ORDER BY overround_percentage ASC;


-- ====================
-- 13. DATA COLLECTION HEALTH CHECK
-- Monitor data freshness and gaps
-- ====================
SELECT 
    event_id,
    bookmaker,
    offer_type,
    MAX(timestamp) AS last_update,
    NOW() - MAX(timestamp) AS time_since_update,
    COUNT(*) AS total_records,
    COUNT(DISTINCT DATE_TRUNC('hour', timestamp)) AS hours_with_data
FROM eventoffer
WHERE $__timeFilter(timestamp)
GROUP BY event_id, bookmaker, offer_type
HAVING NOW() - MAX(timestamp) > INTERVAL '1 hour'
ORDER BY time_since_update DESC;


-- ====================
-- 14. HYPERTABLE STATS
-- Monitor TimescaleDB hypertable health
-- ====================
SELECT 
    hypertable_name,
    num_chunks,
    total_bytes / (1024*1024) AS total_mb,
    compression_enabled
FROM timescaledb_information.hypertables
WHERE hypertable_name = 'eventoffer';


-- ====================
-- 15. CHUNK INFO FOR RETENTION POLICIES
-- See how data is distributed across time chunks
-- ====================
SELECT 
    chunk_name,
    range_start,
    range_end,
    total_bytes / (1024*1024) AS chunk_size_mb,
    compressed_total_bytes / (1024*1024) AS compressed_mb
FROM timescaledb_information.chunks
WHERE hypertable_name = 'eventoffer'
ORDER BY range_start DESC
LIMIT 20;

