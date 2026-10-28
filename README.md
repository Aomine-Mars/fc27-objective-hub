# FC27 Objective Hub

Unofficial EA SPORTS FC 27 Ultimate Team objective tracker.

## Deployment status

- GitHub repository initialized.
- Firebase Edition application package prepared, but application files are not yet deployed.
- Firebase connection and cloud database provisioning are pending.
- No EA account credentials are required.

## Planned functionality

- Scheduled objective catalog checks (third-party source, coverage not guaranteed)
- Manual objective and match progress
- Local offline saves plus optional Firebase Auth / Firestore cloud saves
- JSON export/import to protect existing progress
- Free GitHub Pages hosting

## Next steps

1. Connect Firebase in ChatGPT Plugins or create a Firebase Spark project at https://console.firebase.google.com.
2. Enable Firestore and Email/Password Authentication.
3. Publish the application and scheduled catalog update workflow through GitHub Actions.
4. Validate a real cloud save and restore before claiming cross-device syncing works.

**Security:** Do not publish service-account keys, private Firebase credentials, or EA login credentials.

