# ICE Automated Backup Setup Instructions

## Option 1: Traditional Cron (Linux/Unix/macOS)

To set up daily automated backups at 2:00 AM:

1. Open your crontab editor:
   ```bash
   crontab -e
   ```

2. Add this line (adjust path if needed):
   ```cron
   0 2 * * * /Users/royyeo/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone\ Project/scripts/automated_backup.sh
   ```

   This runs the backup every day at 2:00 AM.

3. Save and exit the editor.

4. Verify the cron job was added:
   ```bash
   crontab -l
   ```

### Alternative Schedules:
- Every 6 hours: `0 */6 * * *`
- Every weekday at 3 AM: `0 3 * * 1-5`
- Every Sunday at midnight: `0 0 * * 0`
- Every hour: `0 * * * *`

## Option 2: macOS launchd (Recommended for macOS)

1. Copy the provided plist file to LaunchAgents:
   ```bash
   cp ~/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone\ Project/scripts/com.ice.backup.plist ~/Library/LaunchAgents/
   ```

2. Load the launchd job:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.ice.backup.plist
   ```

3. To unload (stop) the job:
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.ice.backup.plist
   ```

4. To check if it's running:
   ```bash
   launchctl list | grep ice.backup
   ```

## Monitoring Backups

Check backup logs:
```bash
tail -f ~/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone\ Project/logs/backups/backup_$(date +%Y%m%d).log
```

List recent backups:
```bash
cd ~/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone\ Project
python scripts/backup_ice_storage.py list
```

## Testing

Run manual backup:
```bash
cd ~/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone\ Project
./scripts/automated_backup.sh
```

## Troubleshooting

1. **Permission denied**: Make sure the script is executable:
   ```bash
   chmod +x scripts/automated_backup.sh
   ```

2. **Python not found**: Update PATH in the script or use full Python path

3. **Backup fails silently**: Check logs in `logs/backups/`

4. **macOS asks for permissions**: Grant Terminal/cron full disk access in System Preferences > Security & Privacy

## Cloud Backup (Optional)

To enable S3 uploads, set environment variables in the script:
```bash
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
```

Then modify the backup command to include:
```bash
--s3-bucket your-bucket-name
```