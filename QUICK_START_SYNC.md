# Quick Start: Marketing Events Sync

## Run Sync Manually

```bash
cd /Users/JJR/SalesGPT
source venv/bin/activate
python3 scripts/sync_marketing_events.py --limit 1000
```

Or use the convenience script:
```bash
./scripts/run_sync.sh
```

## Set Up Automatic Sync (Cron)

Add to crontab:
```bash
crontab -e
```

Add this line (runs every 5 minutes):
```
*/5 * * * * cd /Users/JJR/SalesGPT && /Users/JJR/SalesGPT/venv/bin/python3 scripts/sync_marketing_events.py --limit 1000 >> /tmp/marketing_events_sync.log 2>&1
```

Or use the convenience script:
```
*/5 * * * * /Users/JJR/SalesGPT/scripts/run_sync.sh >> /tmp/marketing_events_sync.log 2>&1
```

## Check Sync Status

View recent sync logs:
```bash
tail -f /tmp/marketing_events_sync.log
```

Check unprocessed events in Supabase:
```sql
SELECT COUNT(*) FROM marketing_events WHERE processed_at IS NULL;
```

## Expected Output

```
Events processed: 4
Leads updated: 2
Events (leads not found): 2
```

- **Events processed**: Total events synced
- **Leads updated**: Leads in SalesGPT DB that were updated
- **Events (leads not found)**: Events for emails not in SalesGPT DB (organic signups)

