#!/bin/bash
# Append Docker bridge network rules to pg_hba.conf
# This allows Debezium and other Docker-network clients to connect to PostgreSQL.
# Runs last (alphabetically) in docker-entrypoint-initdb.d so pg_hba.conf already exists.
set -e

cat >> "$PGDATA/pg_hba.conf" << 'EOF'

# Allow connections from Docker bridge networks (172.16.0.0/12 covers 172.16-172.31)
# Required for Debezium CDC and any other inter-container access
host    all             all             172.16.0.0/12           trust
host    replication     all             172.16.0.0/12           trust
EOF

echo "[99-pg-hba.sh] Docker bridge network rules appended to pg_hba.conf"
