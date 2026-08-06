# Current User Endpoint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement authenticated GET and PATCH operations at `/api/v1/users/me/` with strict public-field serialization and partial name updates.

**Architecture:** A dedicated `CurrentUserSerializer` owns representation and payload validation. A small `APIView` operates exclusively on `request.user`, relying on global JWT authentication and explicitly declaring `IsAuthenticated`.

**Tech Stack:** Python 3, Django 5.2, Django REST Framework 3.17, Simple JWT 5.5, pytest-django.

## Global Constraints

- Add exactly one success test and one error test for each route operation.
- Do not modify models, migrations, settings, requirements, or JWT behavior.
- PATCH accepts only `first_name` and `last_name`; GET exposes exactly `id`, `email`, `first_name`, and `last_name`.
- Obtain authenticated-test access tokens through `POST /api/v1/auth/token/`.

---

### Task 1: Define the endpoint contract with failing API tests

**Files:**
- Create: `backend/apps/accounts/tests/api/test_current_user.py`

**Interfaces:**
- Consumes: `POST /api/v1/auth/token/` with email and password.
- Produces: expected contract for `GET /api/v1/users/me/` and `PATCH /api/v1/users/me/`.

- [ ] **Step 1: Write four API tests**

Create an `APITestCase` with a user fixture and login helper. Test authenticated GET output, unauthenticated GET `401`, valid partial PATCH persistence, and forbidden-field PATCH `400` with atomic rejection.

- [ ] **Step 2: Verify RED**

Run: `pytest apps/accounts/tests/api/test_current_user.py -v`

Expected: all four tests fail because `/api/v1/users/me/` is not registered.

### Task 2: Implement strict serialization and the authenticated view

**Files:**
- Modify: `backend/apps/accounts/serializers.py`
- Modify: `backend/apps/accounts/views.py`
- Modify: `backend/apps/accounts/urls.py`
- Test: `backend/apps/accounts/tests/api/test_current_user.py`

**Interfaces:**
- Consumes: `request.user`, `StrictCharField`, and DRF serializer validation.
- Produces: `CurrentUserSerializer` and `CurrentUserView` supporting GET and PATCH.

- [ ] **Step 1: Add `CurrentUserSerializer`**

Define strict optional name fields with `allow_blank=True`, `allow_null=False`, and `max_length=150`. Declare `id` and `email` read-only. Override `run_validation` to require a mapping with at least one permitted field and reject every other key in deterministic order using `detail` messages.

- [ ] **Step 2: Add `CurrentUserView`**

Declare `permission_classes = [IsAuthenticated]`. GET returns `CurrentUserSerializer(request.user).data`. PATCH constructs the serializer with `instance=request.user`, `data=request.data`, and `partial=True`, validates, saves, and returns status `200`.

- [ ] **Step 3: Register the URL**

Add `path("users/me/", CurrentUserView.as_view(), name="current-user")` before the registration route.

- [ ] **Step 4: Verify GREEN**

Run: `pytest apps/accounts/tests/api/test_current_user.py -v`

Expected: 4 passed.

### Task 3: Document and verify the feature

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: final HTTP contract.
- Produces: usage examples for API consumers.

- [ ] **Step 1: Document GET and PATCH**

Add a `## Usuário autenticado` section with curl examples and the rules for JWT, editable fields, partial updates, immutable email, empty payload `400`, and invalid authentication `401`.

- [ ] **Step 2: Run focused and regression tests**

Run from `backend/`:

```powershell
pytest apps/accounts/tests/api/test_current_user.py -v
pytest -v
python manage.py check
python manage.py makemigrations --check --dry-run
```

Expected: four focused tests pass, the complete suite passes, Django reports no issues, and no model changes are detected.

- [ ] **Step 3: Review and commit**

Review `git diff`, confirm only scoped files changed, then commit with `feat: add current user endpoint`.
