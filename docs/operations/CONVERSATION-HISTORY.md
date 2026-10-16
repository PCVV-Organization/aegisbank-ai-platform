# Conversational history

The assistant presents a customer-scoped transcript, not the model's internal
tool protocol. User and assistant messages are rendered as separate chat
bubbles and the transcript is loaded again when the authenticated session is
resumed.

## Security boundary

- The API derives the customer identity from the authenticated principal.
- A caller cannot select another customer's session by changing `session_id`.
- Only final user-visible text is stored. Tool calls, prompts, tokens, and
  internal routing metadata are never returned by the history endpoint.
- State-changing operations remain subject to the existing approval boundary.
- The current MVP stores local history in SQLite. Azure Container Apps local
  storage is not a durable cloud database; staging must use a managed Cosmos
  conversation repository before history is considered cloud-durable.

## UX contract

The interface keeps the current transcript, shows user and assistant bubbles,
shows a busy state while AegisBank is queried, and retrieves the transcript from
`GET /api/v1/conversations/{session_id}/messages` after a session is resumed.
The browser does not submit `customer_id` as an authority claim.

Financial assistants commonly keep conversations behind the authenticated
banking session and provide a clear privacy boundary. AegisBank follows that
pattern for this synthetic laboratory while retaining explicit data-minimizing
limits and a future retention/deletion control.
