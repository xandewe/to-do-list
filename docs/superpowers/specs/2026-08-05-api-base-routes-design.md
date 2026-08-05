# API Base Routes Design

## Goal

Prepare the HTTP infrastructure for future API endpoints without adding domain behavior. The existing public healthcheck remains at `/api/health/`, while future functional routes live below `/api/v1/`.

## Routing architecture

`config.urls` remains the project-level URL configuration. It keeps `/admin/` and the unversioned health routes, and delegates `/api/v1/` to a new `config.api_urls` module.

`config.api_urls` is only an aggregator. It includes `apps.accounts.urls` and `apps.tasks.urls`; both application URL modules start with empty `urlpatterns`. No API root, placeholder view, or domain endpoint is introduced. The application modules reserve ownership for their future account/authentication and category/task routes without committing their concrete paths in this task.

## DRF defaults

`settings.REST_FRAMEWORK` sets `rest_framework.permissions.IsAuthenticated` as the global default permission. Public views must opt out explicitly. The existing healthcheck continues to use `authentication_classes = []` and `permission_classes = [AllowAny]`, so it remains public even after this default changes.

Authentication backends are not changed. In particular, Simple JWT is neither installed nor referenced in this task.

The global pagination class is `config.pagination.DefaultPageNumberPagination`, derived from DRF's `PageNumberPagination`, with these settings:

- Default page size: 20
- Page query parameter: `page`
- Page-size query parameter: `page_size`
- Maximum page size: 100

DRF's standard paginated representation is retained: `count`, `next`, `previous`, and `results`. Invalid and out-of-range values retain DRF's standard behavior.

## Healthcheck behavior

`GET /api/health/` remains public and returns only `api` and `database`. A working database produces HTTP 200 with both values `online`; a database error produces HTTP 503 with the database value `offline`. Unsupported methods return HTTP 405, and `/api/v1/health/` does not resolve.

## Error conventions

No custom exception handler or response envelope is added. Future endpoints will use DRF's standard `detail` and field-error representations and conventional HTTP statuses. This task does not add behavior solely to demonstrate those formats.

## Testing strategy

Configuration tests verify the installed DRF app, authenticated default permission, project pagination class, pagination limits, and absence of Simple JWT references.

Routing tests verify the existing admin and health routes, the absence of versioned health and domain endpoints, and the ability to load the account and task URL modules.

Health tests preserve the public HTTP 200/503/405 behavior and exact response keys after the global permission change.

Pagination tests use a test-only DRF view and URL configuration. They exercise the class through HTTP responses without adding any production endpoint, covering the default and requested sizes, the maximum cap, response shape, first and last links, invalid pages, and preservation of query parameters in navigation links.

## Documentation and scope boundaries

The README documents only `/api/v1/`, the unversioned healthcheck, pagination fields and limits, and the focused API test command. It does not document future endpoints or JWT behavior.

This task does not change dependencies, models, migrations, serializers, authentication mechanisms, or domain views. It does not add repositories, base views, custom exceptions, filters, schema tooling, rate limiting, or functional account/task routes.
