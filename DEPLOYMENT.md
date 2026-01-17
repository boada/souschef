# 🐳 souschef.ai Deployment Guide

## Quick Start (Home Server)

```bash
# On your home server
git clone https://github.com/boada/souschef.git
cd souschef
mkdir data  # Database will be stored here
docker compose up -d
```

Access at: `http://your-server-ip:8000`

## What's Running

- **gunicorn**: Production WSGI server (2 workers, 4 threads each)
- **Flask app**: Your souschef.ai backend
- **SQLite**: Database persisted in `./data/` directory

## Commands

```bash
# Start
docker compose up -d

# Stop
docker compose down

# View logs
docker compose logs -f

# Rebuild after code changes
docker compose up -d --build

# Backup database
cp data/database.db data/database.db.backup
```

## Configuration

Edit `docker-compose.yml` to change:
- Port mapping (default: 8000)
- Worker count (default: 2 workers, 4 threads)
- Database location

## Adding HTTPS (Optional)

Uncomment the nginx service in `docker-compose.yml` and add SSL certificates.

## Performance

Current setup handles:
- **8 concurrent requests** (2 workers × 4 threads)
- Way more than enough for home use
- Tested on: Raspberry Pi 4, NAS, any Linux box

## Scaling to Series B 🚀

Need more performance? Increase workers:
```yaml
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "4", "app:app"]
```

But seriously, 2 workers is plenty for your household.
