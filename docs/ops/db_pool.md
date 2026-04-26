# Database connection pool sizing

This document describes how to size and monitor the SQLAlchemy connection pool.

## Key settings

- `pool_size`: steady-state number of connections kept in the pool.
- `max_overflow`: extra connections allowed above `pool_size` during spikes.

## Monitoring

Watch these metrics:

- `db_pool_size`
- `db_pool_checked_out`
- `db_pool_overflow`
- `db_pool_wait_time_seconds`

## Guidance

- Increase `pool_size` if `db_pool_overflow` is frequently > 0.
- Reduce `pool_size` if many connections are idle and DB `max_connections` is pressured.

