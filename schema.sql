CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id VARCHAR(32) UNIQUE,
    product_type VARCHAR(32),
    title VARCHAR(100),
    sold BOOLEAN,
    price FLOAT,
    url VARCHAR,
    alert_sent_dt DATETIME
);

CREATE VIEW IF NOT EXISTS never_seen_sofas
AS
SELECT *
FROM items
WHERE
    product_type = 'sofa'
    AND sold = False
    AND alert_sent_dt IS NULL
ORDER BY
    price
;
