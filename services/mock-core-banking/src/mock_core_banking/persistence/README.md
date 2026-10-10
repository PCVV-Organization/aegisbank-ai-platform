# Persistence Layer

The persistence layer owns database access and transaction boundaries for the local mock service. Keep storage concerns separate from HTTP parsing and domain decisions.

Test persistence behavior with reproducible synthetic fixtures. Do not treat local database success as evidence of production durability, authorization, or deployment.
