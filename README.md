# NutriAI

Latest changes: [Revision 2](REVISION-2.md). Next stage: [Food recognition training](TRAINING.md).

Food and nutrition tracking with a guided welcome, food entry, daily journal, progress and profile screens.

## Deployment

Start with [DEPLOYMENT.md](DEPLOYMENT.md) for your existing angelhope12/nutri-ai GitHub repository and Vercel project. Deploy a preview and verify connected services before merging to master.

## Local setup

Use Python 3.12 and a PostgreSQL test database with password authentication. Keep database authentication enabled.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Fill in .env with your test database, a random SECRET_KEY and service credentials. Never commit .env. Start the backend from the project root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --port 8000
```

In a second terminal:

```powershell
.\.venv\Scripts\python.exe -m http.server 3000 --directory frontend
```

Open http://localhost:3000. Backend startup creates tables and runs legacy migrations; use a dedicated test database.

## Checks

```powershell
python -m unittest discover -s tests -p "test_*.py"
node --test tests/entry.test.cjs
```

These are focused offline regression checks, not full database or production integration tests.

## Model and dataset status

The included ONNX weights are the original model. They have not been retrained or validated after dataset review. Nutrition results remain estimates. Read [REVIEW.md](REVIEW.md), [RELEASE_NOTES.md](RELEASE_NOTES.md) and [MODEL_STATUS.md](backend/models/MODEL_STATUS.md).

The separate dataset review archive quarantines unrelated images and labels needing review. Food candidates are not approved training data. Training requires independently reviewed, separate train and validation folders. Training dependencies are intentionally excluded from the deployment requirements.
