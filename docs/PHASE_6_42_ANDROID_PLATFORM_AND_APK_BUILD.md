# Phase 6.42 — Android Platform Integration and APK Build

## Objective

Extend the Phase 6.41 Flutter client into an Android-buildable package and make CI verify a distributable test APK, without changing the existing preparation engine or API/data contracts.

## Changes

- Added `apps/mobile/android/` application project configuration: Gradle settings/build scripts, Android manifest, Internet permission, Kotlin `MainActivity`, and light/dark launch themes.
- Added a debug-only manifest overlay permitting cleartext HTTP for local emulator development. Release builds keep the platform's cleartext restrictions; production deployments should use HTTPS.
- Pinned the Android Gradle Plugin/Kotlin/Gradle versions to the current Flutter stable Android template versions used when this phase was prepared.
- Expanded `.github/workflows/flutter-mobile.yml` to set up Java 17, bootstrap Flutter-generated wrapper files, resolve dependencies, analyze Dart, run Flutter tests, build `app-release.apk`, verify the file exists, and upload it as `ai-comp-mobile-android-apk` for 14 days.
- Updated mobile/root setup documentation and the master roadmap coverage audit.

## Validation contract

A successful Flutter Actions run must complete all of these commands successfully:

```sh
flutter create --platforms=android --project-name ai_comp_mobile --org com.aicomp --no-pub .
flutter pub get
flutter analyze
flutter test
flutter build apk --release
test -s build/app/outputs/flutter-apk/app-release.apk
```

The uploaded artifact is a **release-mode test APK** signed with Flutter's local debug key. It proves the package builds; it is not evidence of a production signing setup, app-store readiness, backend deployment, or real-device end-to-end coverage.

## Security and remaining work

- Internet access is granted to the app so it can reach the configured API.
- Cleartext HTTP is enabled only in the debug manifest for local emulator workflows; production APIs should use HTTPS.
- API URL and learner ID remain operator-configured; no secret or bearer token is embedded in the binary.
- The access token remains in memory as documented in Phase 6.41.
- iOS scaffolding, concrete host identity-provider integration, private production signing, store publication, and physical-device end-to-end verification remain separate tasks.

## Non-duplication

Phase 6.42 adds native packaging only. It reuses the Phase 6.40 API contract, Phase 6.41 Flutter screens/client/models, existing FastAPI routes, persisted preparation sessions, and existing analytics/recommendation services.
