# Apply Alembic Migration

## Prerequisites
- PostgreSQL server running
- Database `bp_monitor` exists
- Connection config in `app/config.py` is correct

## Steps to apply migration

### 1. Verify database connection
```bash
cd d:\Downloads\bp_monitor-main
python -c "from app.infrastructure.orm import engine; print('Connected:', engine.url)"
```

### 2. Apply migration
```bash
cd d:\Downloads\bp_monitor-main
alembic -c migrations_alembic/alembic.ini upgrade head
```

### 3. Verify tables created
Connect to PostgreSQL and run:
```sql
\dt
```

Expected tables:
- `alembic_version` (migration tracking)
- `users`
- `weather_snapshots`
- `measurements`

### 4. Verify indexes
```sql
\di
```

Expected indexes:
- `ix_users_email`
- `ix_users_id`
- `ix_weather_snapshots_city`
- `ix_weather_city_recorded`
- `ix_measurements_user_id`
- `ix_measurements_measured_at`

## Troubleshooting

### If alembic command not found:
```bash
python -m alembic -c migrations_alembic/alembic.ini upgrade head
```

### If database doesn't exist:
```bash
# Create database first
psql -U postgres -c "CREATE DATABASE bp_monitor;"
```

### To rollback:
```bash
alembic -c migrations_alembic/alembic.ini downgrade -1
```
