# Deploy to your existing Vercel project

Confirmed from your screenshots: GitHub repository **angelhope12/nutri-ai**, Vercel project **nutri-ai**, production branch **master**, production domain **nutri-ai-kohl.vercel.app**. No deployment has been made by this handoff.

## 1 Extract the application

Extract `NutriAI-App.zip`. Open its `nutri-ai` folder. The files inside this folder belong at the root of your existing GitHub repository, alongside `backend`, `frontend`, `requirements.txt`, and `vercel.json`. Do not upload the ZIP itself and do not nest another nutri-ai directory. Keep the dataset review ZIP out of GitHub/Vercel.

## 2 Configure Vercel settings

In your existing project, open **Settings → Environment Variables**. Keep existing valid values, but check the following. Never commit credentials or share their values in chat.

| Variable | Required for |
| --- | --- |
| SECRET_KEY | Login token signing. Must be at least 32 random characters. Generate locally with `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Changing it signs out existing sessions. |
| DATABASE_URL | PostgreSQL connection string with the provider's SSL settings. Alternatively preserve existing DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD. |
| APP_ENV | Set to production. |
| SMTP_EMAIL and SMTP_PASSWORD | Gmail account and app password for registration verification emails. |
| BLOB_READ_WRITE_TOKEN | Photo upload through your Vercel Blob store. |
| GOOGLE_CLIENT_ID | Optional Google login; authorize the exact deployed HTTPS origin in the Google OAuth configuration. |
| USDA_API_KEY | Optional external nutrition lookup. |
| VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_CLAIMS_EMAIL | Optional push notifications. |
| CRON_SECRET | Required if you configure a cron to call /api/push/cron. It must send Authorization: Bearer followed by this secret. |
| ENABLE_SCHEDULER | Keep false on Vercel. Background scheduling must use a supported external cron. |

Use a separate database for Preview deployments. The existing backend creates tables and runs legacy migrations on startup; pointing a preview at production can change the production database. Back up the database before publishing.

Root Directory should be the directory containing `vercel.json` (repository root if copying as described). The package retains the existing legacy Vercel builds/routes configuration, adds an explicit root-page route, and specifies Python 3.12. Do not replace the root directory with frontend: the backend is part of this deployment.

## 3 Upload to a preview branch

For the GitHub website workflow:

1. Open https://github.com/angelhope12/nutri-ai.
2. Use the branch selector currently showing master to create `codex/nutriai-ui-release` from master.
3. On that branch, choose **Add file → Upload files**. Upload the extracted app contents at repository root, preserving folder structure. Do not upload .env files, datasets, or virtual environments. If the browser upload cannot preserve the folders or exceeds limits, use Git as shown below.
4. Commit to the new branch. Vercel should create a Preview deployment for the connected branch; inspect its build logs and settings if it does not.
5. Open the Preview URL and perform the checks below.

For a local Git workflow, clone your existing repository, create a branch, and copy the extracted package contents into that checkout. Keep its .git directory. Then:

```
git switch -c codex/nutriai-ui-release
git add .
git diff --cached --stat
git commit -m "Redesign NutriAI and prepare deployment"
git push -u origin codex/nutriai-ui-release
```

Inspect the staged changes before committing. Existing files not included in this package are not automatically removed by copying. Do not upload `NutriAI-Dataset-Review.zip`.

## 4 Verify the preview

- Open `/api` and check that it reports the backend is running.
- Verify first visit → welcome → Next/Back/Skip → login/sign-up.
- Register a test account and verify actual email delivery; complete its profile.
- Log a supported text food and check totals, meal details, progress, profile updates, and logout.
- Test a food photo under 4 MB. Check Blob upload, food identification, and unsupported-food behavior. Predictions remain estimates.
- Check Today / Add meal / Progress / Profile on a phone and desktop. Camera use requires HTTPS and browser permission.
- Password recovery is intentionally unavailable until an authenticated email-reset flow is implemented. Do not interpret that as a deployment failure.

## 5 Publish

After the preview checks pass, open a pull request from `codex/nutriai-ui-release` into `master`. Merge it when ready. Your screenshot confirms that pushing to master updates production automatically. Watch Vercel → Deployments until Ready, then open https://nutri-ai-kohl.vercel.app.

Keep the previous deployment for Vercel Instant Rollback. Code rollback does not undo database changes. If an installed app shows old styling, reload it after deployment so the updated service worker assets load.

## Important limits

The included model is the original model, not retrained or accuracy-validated. The cleaned dataset does not repair existing weights. Read backend/models/MODEL_STATUS.md and REVIEW.md. Finish nutrition-source, allergy-rule, calorie-personalization, registration abuse protection, and secure recovery work before a public launch.

Uploads are limited to 4 MB to leave multipart overhead below Vercel's standard 4.5 MB function payload limit. The actual Vercel build must confirm bundle size. Python's standard bundle limit is 500 MB uncompressed; optional large-function support depends on project configuration. The package excludes training frameworks and dataset files. OCR is optional and not bundled.

Your screenshot shows the Hobby plan. No cron was added automatically: minute-level reminders require checking your plan's scheduling support. On-screen meal schedules remain available without push delivery.

Official references: https://vercel.com/docs/functions/runtimes/python, https://vercel.com/docs/functions/limitations, https://vercel.com/docs/cron-jobs/manage-cron-jobs.
