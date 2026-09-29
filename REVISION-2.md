# NutriAI revision 2 — profile and guide

## Included
- Contained, scrollable app guide; keyboard navigation, Escape dismissal and focus handling; dashboard no longer sits above the dialog.
- Refined setup and profile screens, with cm / metres / feet-and-inches and kg / lb choices. API and database values remain cm and kg.
- Multi-condition selection stays open, preserves existing selections and shows selected names.
- Change/remove profile picture. Uploads are authenticated, capped at 4 MB, decoded and cropped to 384px JPEG with metadata discarded. Only the storage URL is saved in users.avatar_url. Images use the existing public Vercel Blob store, so anyone possessing an image URL can retrieve it. Old-image cleanup is best effort; a failed cleanup needs a storage-dashboard retry.
- Additive, idempotent startup migration: ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(1000). Test it on the isolated Neon preview branch first; existing records remain intact. A database backup remains necessary before production deployment.
- Optional actual meal time at logging. Stored times follow the existing Philippines/UTC+8 convention. Recent logs (up to 1,000, last 28 days) are grouped by meal and day; the median is used after at least three distinct days. Duplicate meal items no longer overweight one day. Older entries remain logging times because actual eating times cannot be reconstructed.
- Reminder screen discloses learning/default status and timezone. Browser timers are replaced on refresh. Background push still needs an external scheduler and configured push keys; this release does not provision those services.
- Removed generic, unchecked allergy substitutions. Warnings no longer claim ingredient verification from a food name or photo. All saved conditions are acknowledged. A recipe-level, clinically reviewed recommendation engine is NOT implemented: recipe ingredients, cross-contact information and condition-specific constraints are not available in the current dataset.

## Deploy this revision
Use the contents of NutriAI-Revision-2.zip, not an earlier extraction. Update both frontend and backend on codex/nutriai-ui-release, then check the Vercel preview. Keep existing configuration and Preview DATABASE_URL. Never upload .env. The app code is ready for preview integration testing; it has not been deployed by this revision.

Check setup conversions, saving/reloading multiple conditions, photo upload/reload/removal, actual meal time, and guide dismissal. Test storage and database operations with a test account. The local UI preview uses synthetic data and refuses saves; offline tests do not prove cloud service integration.

Only merge to master after these checks. Master is the final production deployment; Preview is the test stage before that deployment. Do not promote the preview deployment directly: production must use production database settings.

## Before public release
Credentials previously committed in backend/.env remain exposed in Git history; deleting the latest file is not rotation. Rotate real provider credentials and update the corresponding Vercel environments, without sharing them in chat. Nutrition sources, calorie personalization and secure account recovery still need the work described in REVIEW.md. Original food model weights remain unchanged and unvalidated. See TRAINING.md for the next stage.

Validation: 18 offline Python tests and 8 Node tests passed. Python compilation and JavaScript syntax checks passed. Local browser checks covered feet/inches conversion, persistent multi-selection, four guide steps and dismissal, mobile profile/setup and desktop setup. Cloud photo storage, database migration and meal saves still require preview integration testing.
