# AI-COMP Flutter Mobile Client

This folder contains the first Flutter client slice for adaptive exam preparation. The client uses the existing FastAPI endpoints; it does not create a second learning engine or local score store.

## Requirements

- Flutter stable and a Dart SDK bundled with Flutter.
- A reachable AI-COMP API base URL.
- A learner ID recognized by that deployment and an access token that the deployment's configured authentication provider understands.
- The authenticated server must map the supplied access token to the same learner as the route's learner ID. A learner ID by itself is not authentication.

## Run

From this directory:

```sh
flutter pub get
flutter analyze
flutter test
flutter run --dart-define=AI_COMP_API_BASE_URL=https://your-api.example.com --dart-define=AI_COMP_LEARNER_ID=your-learner-id
```

The API URL and learner ID are optional compile-time defaults; both can also be entered on the first screen. Enter the access token in the screen. The token is held in memory and is not written to disk by this app.

For an Android emulator connecting to a development API running on the host computer, the base URL is commonly `http://10.0.2.2:8000`. Use HTTPS for real deployments; do not send production access tokens over plain HTTP. Your server may need its development network/firewall configured to permit emulator access.

This repository has no mobile login endpoint. The client therefore accepts a token issued by the host application's existing authentication system; it does not mint credentials or bypass server-side learner-scope checks.

## Current workflow

1. Connect to the API and load saved analytics, summary, and recent sessions.
2. Configure question count and time; ask the server to build the next adaptive preparation request.
3. Create and start a persistent test, answer questions, mark questions for review, navigate, and submit.
4. Review correct answers and explanations after submission.
5. Resume a saved CREATED/IN_PROGRESS session from the dashboard; the server remains the source of truth for remaining time and previously saved answers.

The backend also exposes OpenAPI at `/openapi.json` and interactive docs at `/docs` when running in a configured server environment. Client response models are aligned with `src/ai_comp/api/preparation_client_contract.py`.

## Platform scaffolding

The first commit adds the Flutter package, Dart screens, and tests. Platform-specific Android/iOS runner files are not generated in this phase. To generate local platform runners without overwriting the client sources, create a temporary Flutter scaffold and copy the desired platform directory into this package, or use the next Android packaging phase to add and verify the platform project. The committed CI currently validates the Dart/Flutter package with `flutter analyze` and `flutter test`; it does not claim that an APK has been built.
