#!/bin/bash

# Database Migration Helper Script
# Usage: ./scripts/migrate.sh [command]
#
# Commands:
#   up         - Apply all pending migrations
#   down       - Rollback the last migration
#   rollback   - Rollback the last migration (alias for down)
#   status     - Show migration status
#   new [name] - Create a new migration file
#   redo       - Rollback and re-apply the last migration

set -e

DATABASE_URL="postgres://rss_user:rss_password@localhost:5432/rss_monitor?sslmode=disable"

COMMAND=${1:-up}

case $COMMAND in
  up)
    echo "Applying migrations..."
    docker-compose run --rm dbmate up
    ;;

  down)
    echo "Rolling back last migration..."
    docker-compose run --rm dbmate down
    ;;

  rollback)
    echo "Rolling back last migration..."
    docker-compose run --rm dbmate down
    ;;

  status)
    echo "Migration status:"
    docker-compose run --rm dbmate status
    ;;

  new)
    MIGRATION_NAME=${2:-"new_migration"}
    echo "Creating new migration: $MIGRATION_NAME"
    docker-compose run --rm dbmate new "$MIGRATION_NAME"
    echo "Migration file created in db/migrations/"
    ;;

  redo)
    echo "Redoing last migration..."
    docker-compose run --rm dbmate down
    docker-compose run --rm dbmate up
    ;;

  *)
    echo "Unknown command: $COMMAND"
    echo ""
    echo "Usage: ./scripts/migrate.sh [command]"
    echo ""
    echo "Commands:"
    echo "  up         - Apply all pending migrations"
    echo "  down       - Rollback the last migration"
    echo "  rollback   - Rollback the last migration (alias for down)"
    echo "  status     - Show migration status"
    echo "  new [name] - Create a new migration file"
    echo "  redo       - Rollback and re-apply the last migration"
    exit 1
    ;;
esac
