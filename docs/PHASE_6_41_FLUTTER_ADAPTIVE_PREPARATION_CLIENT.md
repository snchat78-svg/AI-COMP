# Phase 6.41 — Flutter Adaptive Preparation Client Foundation

## Scope and repo discovery

The repository previously contained a FastAPI/Python backend, but no Flutter, Dart, web, or mobile UI. This phase creates the initial Flutter package at `apps/mobile/`, consumes the Phase 6.40 API contracts, and adds the first adaptive test UX. Platform-specific Android/iOS runner folders and APK signing/build are deliberately not claimed as complete here.

## Implemented files

- `apps/mobile/pubspec.yaml` and `analysis_options.yaml`: Flutter package and analyzer configuration.
- `lib/api/ai_comp_api_client.dart`: authenticated HTTP client for recommendations, saved sessions, session navigation/answering, submit/review, analytics, summary, and session/result history.
- `lib/models/preparation_models.dart`: typed client models and stable API error mapping.
- `lib/screens/preparation_home_screen.dart`: API connection, adaptive settings, learning summary, weak-topic panel, recent session history, and resume actions.
- `lib/screens/test_session_screen.dart`: persistent session start/resume, server-driven timer refreshes, auto-save selected options, previous/next navigation, review marking, and submit.
- `lib/screens/test_result_screen.dart`: score summary and post-submit explanation review.
- `test/`: model parsing, HTTP routes/headers/error contract, and dashboard smoke tests.
- `.github/workflows/flutter-mobile.yml`: Flutter stable dependency resolution, analysis, and test workflow.

## API behavior and recovery

- Uses existing endpoints; no second question composer, test engine, analytics source, or score store was added.
- Sends a bearer access token only when the learner enters it. The app does not persist the token to disk and does not invent an authentication scheme; the API deployment must validate credentials via its configured identity provider.
- Fetches saved session state for resume instead of reconstructing test progress in the client.
- The current-question endpoint now returns `selected_option_key` for the learner's own already-saved selection. It never returns `correct_option_key`; the latter remains available only from the post-submit answer-review endpoint.
- The server-returned remaining seconds are used to initialize/resynchronize the display timer. The local countdown is a display aid, not an independent deadline authority.
- Client-side routing branches on the stable API error code; it displays messages without parsing them for control flow.

## Running the tests

From `apps/mobile/`:

```sh
flutter pub get
flutter analyze
flutter test
```

The dedicated GitHub Actions workflow runs these commands on changes to the mobile package and relevant API contracts. The workflow does not build a signed APK. An Android/iOS runner scaffold, device packaging, and integration with a concrete identity provider should be handled in a follow-on packaging/authentication phase.
