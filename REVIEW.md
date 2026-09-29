# NutriAI review and first improvements

Reviewed September 29, 2026. This is a source review and corrective patch, not a certification of nutritional or clinical accuracy. The original ZIP is unchanged. The release excludes secrets, Git history and installed environments. Original model weights have now been restored, unchanged and not accuracy-validated. Reviewed datasets are delivered separately; candidates still require approval before training. See DEPLOYMENT.md for preview deployment and remaining launch checks.

## Findings and changes

| Priority | Finding | Change or remaining work |
| --- | --- | --- |
| Critical | `/api/forgot-password` accepted an email and a new password without proof of ownership. | Disabled with HTTP 503. Build an expiring, single-use email reset token flow with request throttling before re-enabling recovery. Authenticated password changes remain available. |
| High | JWT signing defaulted to the literal `secret`. | Startup now requires a configured secret of at least 32 characters. Generate a random secret; length alone does not establish randomness. |
| High | Shared analysis cache returned stored medical warnings and image URLs across users and discarded analysis metadata. | Disabled reads and writes. A replacement needs user isolation, profile and model versioning, provenance fields, and invalidation rules. |
| High | Unsupported classes received fabricated defaults of 250 calories, 10 g protein, 30 g carbohydrate, and 10 g fat. | Unknown nutrition now returns HTTP 422 instead. Existing static profiles still require source verification. |
| High | Substring matching silently mapped compound names to unrelated or partial foods. | Removed partial local matching and restricted dataset label matching to exact normalized names. Explicit aliases still need review. |
| High | Volume was treated as gram weight; arbitrary pieces were assumed to weigh 100 g. | Reject unsupported volume and other units. Local piece counts require a known piece weight; USDA piece counts require grams. Reject nonpositive local portions. |
| High | A confident image prediction ignored accompanying text and portions. | Explicit text takes precedence over the image. The image is still uploaded by the endpoint. |
| High | Validation reused training images when no validation folder existed. | Require separate `train/` and `val/` folders and identical class mappings. This does not detect duplicate images across folders. |
| Medium | Inference stretched images to a square while validation resized and center-cropped. | Inference now uses an aspect-preserving resize and center crop matching the validation geometry. Numerical parity with torchvision remains untested. |
| Medium | Negative nutrition and nonfinite or nonpositive body measurements were accepted by schemas. | Added Pydantic field constraints. Full request/response integration remains to be tested. |
| Medium | Results did not disclose assumed portions. | Added local portion metadata and a frontend estimate notice. Static profile and USDA provenance still need a consistent schema. |
| Medium | Uploads were unbounded and storage requests had no timeout. | Added a 4 MB read limit, empty-upload rejection, null filename handling, and upload timeout. Image format verification and cleanup after failed analysis remain outstanding. |

## Accuracy work still required

1. **Verify the nutrition database.** `common_foods.py` combines per-100 g and per-100 ml descriptions without a per-record basis. Some aliases equate different preparations, such as boiled, scrambled, and fried eggs. Record a source ID, preparation method, nutrient basis, serving weight, retrieval date, and missing-value status for every food. Remove aliases that change nutrition. Do not treat missing nutrients as measured zeros.
2. **Make USDA matching reviewable.** The current function uses only the first search hit and initializes missing nutrients to zero. Return candidate foods for confirmation, persist the selected FDC ID, validate nutrient units, and handle missing energy and micronutrients explicitly. Gram portion scaling should use nutrient values per 100 g and the actual portion weight, as described in [USDA Foundation Foods documentation](https://fdc.nal.usda.gov/Foundation_Foods_Documentation/). Branded records need their own basis checks.
3. **Replace name-only medical screening.** Ingredient and cross-contact information cannot be established from a dish name or a photo. Current allergy and illness rules and suggested substitutes have not been validated and should not be presented as confirmation that a meal is safe. Replace them with reviewed ingredient evidence and explicit unknown states.
4. **Correct calorie personalization.** `calculate_daily_calories` assumes age 25, male sex, and a fixed activity multiplier for every user. The current profile does not collect enough data to justify personalized calorie targets. Add the necessary inputs, define the intended population, and have the calculation and limits reviewed before presenting it as personalized guidance.
5. **Measure recognition separately from nutrition.** Prepare a deduplicated, manually labeled test set that is never used for training or threshold selection. Include unknown foods, non-food photos, mixed dishes, varied lighting, and real user portions. Report per-class precision/recall, confusion matrix, unknown-food rejection, and confidence calibration. A softmax score is not a measured probability of correctness. The existing 0.40 threshold has not been validated here.
6. **Finish deployment and security review.** Test Google login audience configuration, registration verification attempt limits, push subscription ownership, cron authorization, frontend asset routes, migrations, and storage error handling. These paths have not received a complete integration audit.

## Verification performed

- Seven offline regression tests passed: gram scaling, piece scaling, assumed-portion metadata, false substring matches, invalid portions, unavailable nutrition, and disabled unauthenticated password recovery.
- All backend Python files passed compilation.
- `frontend/scripts/app.js` passed `node --check`.
- Tests load selected functions through Python's AST to avoid optional cloud, database, and ML imports. They do not exercise FastAPI routing, database transactions, external services, or browser behavior.
- The backend, ONNX model, retraining, and browser UI were not run. This environment lacks the application dependencies, and credentials were deliberately excluded from the working copy.

Run the offline suite from this directory with `python -m unittest discover -s tests -v`. Run `python -m compileall -q backend` and `node --check frontend/scripts/app.js` for syntax checks.

## Deployment implications

Password recovery currently reports temporary unavailability. The server requires a new configured strong signing secret. Analysis caching is disabled, so each request recomputes results. Training now fails until independent training and validation folders are provided. Matching is intentionally stricter; users may need to enter a supported food name and grams. No service was deployed and no production database was changed.
