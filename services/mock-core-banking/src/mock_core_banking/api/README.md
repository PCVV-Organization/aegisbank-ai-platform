# API Layer

The API layer maps HTTP requests to validated schemas and application/domain operations. It should not duplicate domain policy or bypass persistence boundaries.

Review route behavior, request validation, error mapping, and tests together when changing an endpoint. This service is a synthetic local mock and does not itself establish user authentication, authorization, or human approval.
