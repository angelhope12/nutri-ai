# NutriAI handoff 2026 09 29

The app now has a first-visit introduction, a food-themed dashboard with calorie ring and nutrient cards, a meal journal, a refreshed scanner and progress page, organized settings, and consistent Today / Add meal / Progress / Profile navigation. The in-app guide remains replayable. Notification permission is an explicit opt-in.

UI verification used a separate local server with labeled synthetic data. No account or database was changed. All four main screens were visually checked on mobile, and the dashboard was checked on desktop. First-visit routing, Next, Back, Skip, account links, and repeat visits were checked.

The earlier accuracy/security fixes include stricter food matching, portion validation, rejection of invented default nutrition, disabling shared medical-warning cache and unauthenticated password recovery, enforcing a signing secret, and requiring separate training/validation directories. See REVIEW.md for remaining issues.

Deployment preparation includes the original 16.25 MB ONNX model and labels, a model status note, .env.example, Python 3.12 selection, smaller runtime requirements, explicit Vercel root route, ignore rules, protected cron endpoint, 4 MB image checks, PostgreSQL URL support, and production email configuration checks. No secrets are included and no live deployment was performed.

Dataset materials are separate: 1,383 unrelated/unsuitable images, 382 requiring label review, and 479 food candidates. All 2,244 extracted files were hash-verified. Candidates are not approved training data; the model has not been retrained.

Checks: 11 offline Python regression tests, five entry-routing JavaScript tests, Python compilation, JavaScript syntax, and page ID/asset checks. These do not replace live backend or Vercel build testing.
