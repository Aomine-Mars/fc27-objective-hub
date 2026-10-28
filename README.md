# FC27 Objective Hub

Unofficial, mobile-friendly FC27 Ultimate Team objective planner. Created for personal use. Not affiliated with EA or FCData.

## Current state

- Functional static website committed and ready for GitHub Pages.
- Local progress and match history are stored in your browser. Use Settings > Export backup before migrating.
- `cloud-sync.js` adds **optional Firebase Authentication + Firestore cloud backup**. It is not active until a Firebase project is created and configured in the app. The public Firebase web configuration can be pasted into the ☁ Cloud panel after deployment.
- `refresh_catalog.py` attempts a source catalog check on GitHub Actions every four hours. It preserves the last saved public `catalog.json` if the source refuses or fails a check. The **last successful** timestamp and source coverage are displayed in Discover. No EA sign-in or EA progress syncing occurs.
- Some source-listed objectives may lack verified task details. They will remain listed, not invented.

## Free hosting (one-time)

1. Repository Settings > Pages > Build and deployment > Source: **GitHub Actions**. Save. An automatic enablement attempt failed because the GitHub Actions token cannot enable Pages.
2. Open Actions > **Publish FC27 Objective Hub** > Run workflow to build and publish. The expected repository Pages URL is `https://aomine-mars.github.io/fc27-objective-hub/` **only after a successful deployment**.

## Free private cloud saves (one-time)

1. Create a separate **Spark (no-cost)** project at https://console.firebase.google.com/ . This is not a Supabase project.
2. Enable Authentication > Sign-in method > **Email/Password**.
3. Create Cloud Firestore, and publish the exact permissions from [firebase.rules](firebase.rules) under Firestore > Rules. These limit each user's document to their own user ID.
4. Firebase Project settings > Your apps > register a **Web app** and copy its **public web configuration object** (apiKey, authDomain, projectId, appId). Do **not** copy a service-account/private key.
5. Firebase Authentication > Settings > Authorized domains: add `aomine-mars.github.io` if not present.
6. On the hosted tracker click **☁ Cloud** > paste web config > Connect project > sign up with your email > Back up this device.

The initial backup/restore is explicit. Once it succeeds, subsequent browser changes sync online using transaction-based revision checks. A conflict stops cloud sync instead of silently overwriting a newer copy. Retain occasional exported JSON backups.

## Security and limitations

- Local storage is browser-specific; it is not guaranteed after browser data deletion. Cloud saving isn't verified until a real Firebase project and successful first backup exist.
- Public web Firebase API keys are not administrative secrets; never paste a Firebase Admin SDK private key into the app or GitHub.
- Firebase free plan subject to usage quotas; third-party catalog data is best effort.
- Objective discovery and completion tracking are different: only catalog discovery is automated.
