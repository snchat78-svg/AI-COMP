# Phase 6.46 — Free-Tier Cloud Hosting Readiness

## Goal

Prepare a repeatable, ₹0-starting-cost deployment path for the existing AI-COMP backend without changing exam research, question identity/history, test generation, scoring, results, or adaptive-learning contracts.

This phase adds deployment configuration and a manually triggered migration workflow. It does not create cloud resources, store secrets, run migrations, or claim the service has been deployed.

## Chosen prototype architecture

- **API:** Render Free Web Service using the existing root `Dockerfile`.
- **Database:** Supabase Free PostgreSQL with the existing SQL migration set and `vector` extension.
- **Authentication:** existing Firebase Authentication in Flutter, independently verified by the Phase 6.45 API runtime.
- **Firebase Admin credentials:** a Render secret file, never a committed JSON key.
- **Database migrations:** explicitly triggered GitHub Actions workflow, never run from API startup.
- **AI:** this phase does not add a paid API dependency or change AI behavior. Rule/database-backed features remain the baseline; model-backed operations are only usable when a no-cost provider/allowance is configured in a later, separately verified step.

## Files added

- `render.yaml`: Render Blueprint using the Free plan, current Dockerfile, and an OpenAPI liveness check. It requests the database URL and Firebase project ID as Dashboard-supplied environment variables; it contains no real secrets.
- `.github/workflows/database-migrations.yml`: manual-only database migration workflow. It requires selecting `APPLY` and a GitHub Actions repository secret named `AI_COMP_DATABASE_URL`. Concurrent migration runs are serialized.
- The workflow calls the existing `python -m ai_comp.database.migrate_cli`; it does not duplicate or alter migration logic.

## Render Free Service setup

1. Sign in to Render and create a Blueprint from this repository after the Phase 6.46 PR is merged.
2. Select the `free` plan. Do not add paid services or optional paid add-ons.
3. In the service's **Environment → Secret Files**, add a file named `firebase-service-account.json` containing the Firebase Admin service-account JSON for the same Firebase project used by the mobile app. Render makes Docker-service secret files available at `/etc/secrets/<filename>`; the Blueprint sets `GOOGLE_APPLICATION_CREDENTIALS=/etc/secrets/firebase-service-account.json`.
4. Set `FIREBASE_PROJECT_ID` to the exact project ID (not the display name).
5. Set `AI_COMP_DATABASE_URL` to the Supabase PostgreSQL connection string described below.
6. Ensure `FIREBASE_AUTH_EMULATOR_HOST` is **absent**. Phase 6.45 deliberately stops production startup if that variable exists, even if its value is empty.
7. Deploy and inspect Render logs. Do not enter the URL into the APK unless the HTTPS service starts and the checks in the final section pass.

Create/download the Firebase service-account key from Firebase Console → Project settings → Service accounts. Keep it in the Render secret-file field only. Never commit it, add it to a GitHub workflow, paste it into chat, or include it in the APK. Restrict access to the Render service and rotate the key if it is exposed.

## Supabase Free PostgreSQL setup

1. Create a Supabase project on the Free plan.
2. Open **Connect** and choose **Session pooler**; copy the full connection string and replace only its password placeholder with the database password.
3. Use the session-pooler string (normally port `5432`) for both Render and GitHub Actions. Supabase's free direct database endpoint is IPv6-only by default, while Render and GitHub-hosted runners are IPv4-only; the shared session pooler provides IPv4 connectivity without purchasing the IPv4 add-on.
4. In **Database → Extensions**, make sure the `vector` extension is available/enabled. The existing first migration expects it.
5. Add the same complete database connection string in both places:
   - Render service environment variable `AI_COMP_DATABASE_URL`
   - GitHub repository Settings → Secrets and variables → Actions → New repository secret, named `AI_COMP_DATABASE_URL`

Treat this connection string as a password. Never put it in a committed file, issue, PR comment, workflow output, or chat. URL-encode reserved characters in the password if needed.

## Controlled migration procedure

Only after the database exists and the secret is configured:

1. Open the repository's **Actions** tab.
2. Select **Apply database migrations**.
3. Choose **Run workflow** on `main`.
4. Choose `APPLY` only after checking that `AI_COMP_DATABASE_URL` points to the intended new AI-COMP database.
5. Confirm the run succeeds and says which migration versions were applied or that the schema is already up to date.

The workflow runs only from a manual dispatch, does not execute on pushes or PRs, and refuses to proceed if the secret is missing or the confirmation is not `APPLY`. Never run it against an unrelated or production database. Do not start the API before migration succeeds.

## Free-plan limitations and cost safety

- Render Free web services spin down after 15 minutes without inbound traffic and may take about a minute to respond after waking. Their local filesystem is ephemeral, so persistent data must stay in PostgreSQL/object storage.
- Render documents 750 free instance hours per workspace per calendar month and usage limits; it is a prototype/testing option, not an uptime guarantee. Avoid adding a payment method or paid add-ons if the hard requirement is ₹0.
- Supabase Free currently lists 500 MB database size and may pause projects with low database activity over a 7-day period. It can be resumed from the dashboard. Monitor usage and export/back up any important learner data using a suitable process before relying on the prototype.
- Free plan terms and quotas can change. ₹0 means no paid resources are intentionally selected; it does not mean unlimited usage or guaranteed availability.

Official references:
- Render Free services: https://render.com/docs/free
- Render environment variables and secret files: https://render.com/docs/configure-environment-variables
- Render Docker secret files: https://render.com/docs/docker-secrets
- Supabase Free limits: https://supabase.com/docs/guides/platform/billing-on-supabase
- Supabase free-project pausing: https://supabase.com/docs/guides/platform/free-project-pausing
- Supabase connection methods and IPv4 notes: https://supabase.com/docs/guides/database/connecting-to-postgres

## Acceptance criteria

- [ ] Render Blueprint is accepted without selecting a paid plan.
- [ ] No service-account JSON or database credential is present in source control.
- [ ] API runtime uses the existing Phase 6.45 Firebase UID verification and keeps the emulator-mode guard.
- [ ] Supabase session-pooler URL connects from Render/GitHub Actions.
- [ ] Manual migration workflow successfully applies the repository migrations to the intended empty database.
- [ ] Render service starts and returns HTTP 200 from `/openapi.json`.
- [ ] Flutter is configured only with the real HTTPS API root; learner login, UID matching, and protected API calls are tested.
- [ ] Current Python/PostgreSQL, container-build, Flutter-analysis, Flutter-test and APK CI checks remain green.

Until these criteria pass, the project is hosting-ready by configuration only, not deployed. Existing exam and learner-data phases remain unchanged.
