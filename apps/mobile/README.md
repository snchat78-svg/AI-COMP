# AI-COMP Flutter Mobile Client

This package contains the Flutter adaptive-exam preparation client and the checked-in Android runner. The client uses the existing FastAPI endpoints; it does not create a second learning engine or local score store.

## Requirements

- Flutter stable and its bundled Dart SDK.
- Android SDK and Java 17 for local Android builds.
- A reachable AI-COMP API base URL.
- A learner ID recognized by that deployment. The signed-in mobile client uses the Firebase UID as its learner ID and sends a Firebase ID token as a Bearer token; the deployed API must verify it.
- The authenticated server must map the supplied access token to the same learner as the route's learner ID. A learner ID by itself is not authentication.

## Run and validate

From this directory:

```sh
flutter pub get
flutter analyze
flutter test
flutter run --dart-define=AI_COMP_API_BASE_URL=https://your-api.example.com --dart-define=AI_COMP_LEARNER_ID=your-learner-id
```

For a fresh Flutter SDK checkout, Flutter may need to generate local wrapper files ignored by Git. Run the following once from this directory if the Android/Gradle wrapper is missing:

```sh
flutter create --platforms=android --project-name ai_comp_mobile --org com.aicomp --no-pub .
```

The API URL and learner ID are optional compile-time defaults; both can also be entered on the first screen. Enter the access token in the screen. The token is held in memory and is not written to disk by this app.

For an Android emulator connecting to a development API running on the host computer, the base URL is commonly `http://10.0.2.2:8000`. Cleartext HTTP is permitted only by the debug Android manifest; release builds retain Android's cleartext restrictions. Use HTTPS for real deployments and never send production access tokens over plain HTTP. Your server may need its development network/firewall configured to permit emulator access.

The mobile app signs users in with Firebase Authentication (Email/Password), requires verified email, and obtains a Firebase ID token for API requests. The production API must independently verify that token with the Firebase Admin SDK and confirm the requested learner ID matches the verified UID. Client-side login is not a substitute for backend authentication. Until the configured PostgreSQL/Firebase API runtime is deployed, there is no real API base URL to enter.

## Current workflow

1. Connect to the API and load saved analytics, summary, and recent sessions.
2. Configure question count and time; ask the server for an adaptive recommendation. When there is no reliable focus signal yet, the app saves a mixed practice request so the learner can still take a test.
3. Create and start a persistent test, answer questions, mark questions for review, navigate, and submit. The first test may use MIXED mode to establish the history required for future focused recommendations. If fewer verified questions exist than requested, the server uses the available unique eligible questions; an empty verified pool returns an explicit actionable error.
4. Review correct answers and explanations after submission.
5. Resume a saved CREATED/IN_PROGRESS session from the dashboard; the server remains the source of truth for remaining time and previously saved answers.

The backend also exposes OpenAPI at `/openapi.json` and interactive docs at `/docs` when running in a configured server environment. Client response models are aligned with `src/ai_comp/api/preparation_client_contract.py`.

## Android build and artifact

The checked-in `android/` directory includes the application Gradle configuration, manifest/Internet permission, Kotlin activity, and launch themes. Flutter-generated local properties and wrapper files remain untracked by design.

The GitHub Actions workflow runs dependency resolution, `flutter analyze`, `flutter test`, and `flutter build apk --release`. On a successful run, download the `ai-comp-mobile-android-apk` artifact from that workflow run (retained for 14 days). Install on a connected test device with:

```sh
adb install -r app-release.apk
```

The CI APK is a release-mode test build signed with Flutter's local debug key. It is **not** a production-signed store release. No keystore, API URL, learner ID, or access token is embedded in the repository or build workflow. Production distribution requires a separately configured private signing key and release process.
