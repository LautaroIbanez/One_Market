#!/bin/bash
# Example cron job configuration for daily data updates
# 
# To set up this cron job:
# 1. Make this script executable: chmod +x scripts/cron_example.sh
# 2. Edit crontab: crontab -e
# 3. Add the following line (adjust path as needed):
#    0 2 * * * /path/to/One_Market/scripts/cron_example.sh >> /path/to/One_Market/logs/cron.log 2>&1
#
# This will run daily at 2:00 AM UTC (adjust timezone as needed)

# Set environment variables
export PYTHONPATH="/path/to/One_Market"
export PATH="/path/to/python/bin:$PATH"

# Change to project directory
cd /path/to/One_Market

# Run data sync
echo "$(date): Starting daily data sync"
python scripts/sync_data.py --batch --verbose

# Check exit status
if [ $? -eq 0 ]; then
    echo "$(date): Data sync completed successfully"
else
    echo "$(date): Data sync failed"
    # Could add email notification here
fi

