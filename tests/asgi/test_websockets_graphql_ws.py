# pylint: disable=not-context-manager
import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLWSHandler
from ariadne.types import WebSocketConnectionError


def test_field_can_be_subscribed_using_websocket_connection(client):
    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GraphQLWSHandler.GQL_START,
                "id": "test1",
                "payload": {"query": "subscription { ping }"},
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_DATA
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "pong"}
        ws.send_json({"type": GraphQLWSHandler.GQL_STOP, "id": "test1"})
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_COMPLETE
        assert response["id"] == "test1"
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_TERMINATE})


def test_field_can_be_subscribed_using_unnamed_operation_in_websocket_connection(
    client,
):
    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GraphQLWSHandler.GQL_START,
                "id": "test1",
                "payload": {
                    "operationName": None,
                    "query": "subscription { ping }",
                },
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_DATA
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "pong"}
        ws.send_json({"type": GraphQLWSHandler.GQL_STOP, "id": "test1"})
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_COMPLETE
        assert response["id"] == "test1"
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_TERMINATE})


def test_field_can_be_subscribed_using_named_operation_in_websocket_connection(client):
    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GraphQLWSHandler.GQL_START,
                "id": "test1",
                "payload": {
                    "operationName": "PingTest",
                    "query": "subscription PingTest { ping }",
                },
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_DATA
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "pong"}
        ws.send_json({"type": GraphQLWSHandler.GQL_STOP, "id": "test1"})
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_COMPLETE
        assert response["id"] == "test1"
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_TERMINATE})


def test_query_can_be_executed_using_websocket_connection(client):
    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GraphQLWSHandler.GQL_START,
                "id": "test2",
                "payload": {
                    "operationName": None,
                    "query": "query Hello($name: String){ hello(name: $name) }",
                    "variables": {"name": "John"},
                },
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_DATA
        assert response["id"] == "test2"
        assert response["payload"]["data"] == {"hello": "Hello, John!"}
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_TERMINATE})


def test_query_using_websocket_connection_fails_without_http_handler(
    client_graphql_ws_no_http,
):
    with client_graphql_ws_no_http.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GraphQLWSHandler.GQL_START,
                "id": "test2",
                "payload": {
                    "operationName": None,
                    "query": "query Hello($name: String){ hello(name: $name) }",
                    "variables": {"name": "John"},
                },
            }
        )
        with pytest.raises(WebSocketDisconnect, match="4406"):
            ws.receive_json()


def test_immediate_disconnect(client):
    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_TERMINATE})


def test_stop(client):
    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GraphQLWSHandler.GQL_START,
                "id": "test1",
                "payload": {"query": "subscription { ping }"},
            }
        )
        ws.send_json({"type": GraphQLWSHandler.GQL_STOP, "id": "test1"})
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_COMPLETE
        assert response["id"] == "test1"
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_TERMINATE})


def test_custom_websocket_on_connect_is_called(schema):
    test_payload = None

    def on_connect(websocket, payload):
        assert payload == test_payload
        websocket.scope["payload"] = payload

    handler = GraphQLWSHandler(schema, on_connect=on_connect)
    app = GraphQL(subscription_handler=handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
        assert ws.scope["payload"] == test_payload
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_TERMINATE})


def test_custom_websocket_on_connect_is_called_with_payload(schema):
    test_payload = {"test": "ok"}

    def on_connect(websocket, payload):
        assert payload == test_payload
        websocket.scope["payload"] = payload

    handler = GraphQLWSHandler(schema, on_connect=on_connect)
    app = GraphQL(subscription_handler=handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json(
            {"type": GraphQLWSHandler.GQL_CONNECTION_INIT, "payload": test_payload}
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
        assert ws.scope["payload"] == test_payload
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_TERMINATE})


def test_custom_websocket_on_connect_is_awaited_if_its_async(schema):
    test_payload = {"test": "ok"}

    async def on_connect(websocket, payload):
        assert payload == test_payload
        websocket.scope["payload"] = payload

    handler = GraphQLWSHandler(schema, on_connect=on_connect)
    app = GraphQL(subscription_handler=handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json(
            {"type": GraphQLWSHandler.GQL_CONNECTION_INIT, "payload": test_payload}
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
        assert ws.scope["payload"] == test_payload
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_TERMINATE})


def test_error_in_custom_websocket_on_connect_is_handled(schema):
    def on_connect(websocket, payload):
        raise ValueError("Oh No!")

    handler = GraphQLWSHandler(schema, on_connect=on_connect)
    app = GraphQL(subscription_handler=handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ERROR
        assert response["payload"] == {"message": "Unexpected error has occurred."}


def test_custom_websocket_connection_error_in_custom_websocket_on_connect_is_handled(
    schema,
):
    def on_connect(websocket, payload):
        raise WebSocketConnectionError({"msg": "Token required", "code": "auth_error"})

    handler = GraphQLWSHandler(schema, on_connect=on_connect)
    app = GraphQL(subscription_handler=handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ERROR
        assert response["payload"] == {"msg": "Token required", "code": "auth_error"}


def test_custom_websocket_on_operation_is_called(schema):
    def on_operation(websocket, operation):
        assert operation.name == "TestOp"
        websocket.scope["on_operation"] = True

    handler = GraphQLWSHandler(schema, on_operation=on_operation)
    app = GraphQL(subscription_handler=handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GraphQLWSHandler.GQL_START,
                "id": "test1",
                "payload": {
                    "operationName": "TestOp",
                    "query": "subscription TestOp { ping }",
                },
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_DATA
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "pong"}
        ws.send_json({"type": GraphQLWSHandler.GQL_STOP, "id": "test1"})
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_TERMINATE})
        assert ws.scope["on_operation"] is True


def test_custom_websocket_on_operation_is_awaited_if_its_async(schema):
    async def on_operation(websocket, operation):
        assert operation.name == "TestOp"
        websocket.scope["on_operation"] = True

    handler = GraphQLWSHandler(schema, on_operation=on_operation)
    app = GraphQL(subscription_handler=handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GraphQLWSHandler.GQL_START,
                "id": "test1",
                "payload": {
                    "operationName": "TestOp",
                    "query": "subscription TestOp { ping }",
                },
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_DATA
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "pong"}
        ws.send_json({"type": GraphQLWSHandler.GQL_STOP, "id": "test1"})
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_TERMINATE})
        assert ws.scope["on_operation"] is True


def test_error_in_custom_websocket_on_operation_is_handled(schema):
    async def on_operation(websocket, operation):
        raise ValueError("Oh No!")

    handler = GraphQLWSHandler(schema, on_operation=on_operation)
    app = GraphQL(subscription_handler=handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GraphQLWSHandler.GQL_START,
                "id": "test1",
                "payload": {
                    "operationName": "TestOp",
                    "query": "subscription TestOp { ping }",
                },
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_DATA
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "pong"}
        ws.send_json({"type": GraphQLWSHandler.GQL_STOP, "id": "test1"})
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_TERMINATE})


def test_custom_websocket_on_complete_is_called_on_stop(schema):
    def on_complete(websocket, operation):
        assert operation.name == "TestOp"
        websocket.scope["on_complete"] = True

    handler = GraphQLWSHandler(schema, on_complete=on_complete)
    app = GraphQL(subscription_handler=handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GraphQLWSHandler.GQL_START,
                "id": "test1",
                "payload": {
                    "operationName": "TestOp",
                    "query": "subscription TestOp { ping }",
                },
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_DATA
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "pong"}
        ws.send_json({"type": GraphQLWSHandler.GQL_STOP})
        assert "on_complete" not in ws.scope

    assert ws.scope["on_complete"] is True


def test_custom_websocket_on_complete_is_called_on_terminate(schema):
    def on_complete(websocket, operation):
        assert operation.name == "TestOp"
        websocket.scope["on_complete"] = True

    handler = GraphQLWSHandler(schema, on_complete=on_complete)
    app = GraphQL(subscription_handler=handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GraphQLWSHandler.GQL_START,
                "id": "test1",
                "payload": {
                    "operationName": "TestOp",
                    "query": "subscription TestOp { ping }",
                },
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_DATA
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "pong"}
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_TERMINATE})
        assert "on_complete" not in ws.scope

    assert ws.scope["on_complete"] is True


def test_custom_websocket_on_complete_is_called_on_disconnect(schema):
    def on_complete(websocket, operation):
        assert operation.name == "TestOp"
        websocket.scope["on_complete"] = True

    handler = GraphQLWSHandler(schema, on_complete=on_complete)
    app = GraphQL(subscription_handler=handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GraphQLWSHandler.GQL_START,
                "id": "test1",
                "payload": {
                    "operationName": "TestOp",
                    "query": "subscription TestOp { ping }",
                },
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_DATA
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "pong"}
        assert "on_complete" not in ws.scope

    assert ws.scope["on_complete"] is True


def test_custom_websocket_on_complete_is_awaited_if_its_async(schema):
    async def on_complete(websocket, operation):
        assert operation.name == "TestOp"
        websocket.scope["on_complete"] = True

    handler = GraphQLWSHandler(schema, on_complete=on_complete)
    app = GraphQL(subscription_handler=handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GraphQLWSHandler.GQL_START,
                "id": "test1",
                "payload": {
                    "operationName": "TestOp",
                    "query": "subscription TestOp { ping }",
                },
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_DATA
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "pong"}
        ws.send_json({"type": GraphQLWSHandler.GQL_STOP})
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_TERMINATE})
        assert "on_complete" not in ws.scope

    assert ws.scope["on_complete"] is True


def test_error_in_custom_websocket_on_complete_is_handled(schema):
    async def on_complete(websocket, operation):
        raise ValueError("Oh No!")

    handler = GraphQLWSHandler(schema, on_complete=on_complete)
    app = GraphQL(subscription_handler=handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GraphQLWSHandler.GQL_START,
                "id": "test1",
                "payload": {
                    "operationName": "TestOp",
                    "query": "subscription TestOp { ping }",
                },
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_DATA
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "pong"}
        ws.send_json({"type": GraphQLWSHandler.GQL_STOP})
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_TERMINATE})


def test_custom_websocket_on_disconnect_is_called_on_terminate_message(schema):
    def on_disconnect(websocket):
        websocket.scope["on_disconnect"] = True

    handler = GraphQLWSHandler(schema, on_disconnect=on_disconnect)
    app = GraphQL(subscription_handler=handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_TERMINATE})
        assert "on_disconnect" not in ws.scope

    assert ws.scope["on_disconnect"] is True


def test_custom_websocket_on_disconnect_is_called_on_connection_close(schema):
    def on_disconnect(websocket):
        websocket.scope["on_disconnect"] = True

    handler = GraphQLWSHandler(schema, on_disconnect=on_disconnect)
    app = GraphQL(subscription_handler=handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
        assert "on_disconnect" not in ws.scope

    assert ws.scope["on_disconnect"] is True


def test_custom_websocket_on_disconnect_is_awaited_if_its_async(schema):
    async def on_disconnect(websocket):
        websocket.scope["on_disconnect"] = True

    handler = GraphQLWSHandler(schema, on_disconnect=on_disconnect)
    app = GraphQL(subscription_handler=handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_TERMINATE})
        assert "on_disconnect" not in ws.scope

    assert ws.scope["on_disconnect"] is True


def test_error_in_custom_websocket_on_disconnect_is_handled(schema):
    async def on_disconnect(websocket):
        raise ValueError("Oh No!")

    handler = GraphQLWSHandler(schema, on_disconnect=on_disconnect)
    app = GraphQL(subscription_handler=handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_TERMINATE})


def test_websocket_connection_can_be_kept_alive(
    client_graphql_ws_keepalive,
):
    with client_graphql_ws_keepalive.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        ws.receive_json()
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_KEEP_ALIVE
