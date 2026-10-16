from aegisbank_agent.conversation_store import ConversationStore


class FakeRepository:
    def __init__(self):
        self.items = []

    def initialize(self, default_ttl=None):
        self.default_ttl = default_ttl

    def create_item(self, item):
        self.items.append(item)

    def query_items(self, query, parameters, partition_key):
        customer = parameters[0]["value"]
        session = parameters[1]["value"] if len(parameters) > 1 else None
        items = [item for item in self.items if item["customer_id"] == customer]
        if session is not None:
            items = [item for item in items if item["session_id"] == session]
        return items


def test_conversation_store_partitions_turns_by_customer():
    repository = FakeRepository()
    store = ConversationStore(repository)
    store.append_turn(
        customer_id="CUST-0001",
        session_id="session-a",
        role="user",
        content="Hola",
        metadata={"execution_mode": "deterministic", "tool_count": 1, "latency_ms": 12.5},
    )
    store.append_turn(customer_id="CUST-0002", session_id="session-b", role="user", content="Hola")

    turns = store.get_session("CUST-0001", "session-a")
    assert len(turns) == 1
    assert turns[0]["customer_id"] == "CUST-0001"
    assert turns[0]["metadata"]["tool_count"] == 1


def test_conversation_store_rejects_invalid_roles_and_empty_content():
    store = ConversationStore(FakeRepository())
    try:
        store.append_turn(customer_id="CUST-0001", session_id="session-a", role="tool", content="x")
        raise AssertionError("invalid role accepted")
    except ValueError:
        pass
