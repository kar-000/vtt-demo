"""
WebSocket Stress Tests

Tests for WebSocket connection cleanup, memory leaks, and stability
under high-load scenarios. Critical for 4+ hour session stability.
"""

import asyncio
import gc
import sys
import time
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.websocket.manager import ConnectionManager


class MockWebSocket:
    """Mock WebSocket for testing without actual network connections."""

    def __init__(self, client_id: int):
        self.client_id = client_id
        self.accepted = False
        self.closed = False
        self.sent_messages = []

    async def accept(self):
        self.accepted = True

    async def send_text(self, message: str):
        if self.closed:
            raise Exception("Connection closed")
        self.sent_messages.append(message)

    async def close(self):
        self.closed = True

    def __hash__(self):
        return hash(self.client_id)

    def __eq__(self, other):
        if isinstance(other, MockWebSocket):
            return self.client_id == other.client_id
        return False


class TestConnectionManagerCleanup:
    """Test that connection manager properly cleans up resources."""

    def test_connect_disconnect_single(self):
        """Basic connect/disconnect should leave no orphaned data."""
        manager = ConnectionManager()
        ws = MockWebSocket(1)

        # Connect
        asyncio.run(manager.connect(ws, campaign_id=1, user_id=1, username="test"))
        assert manager.get_campaign_connections(1) == 1
        assert ws in manager.connection_info

        # Disconnect
        manager.disconnect(ws)
        assert manager.get_campaign_connections(1) == 0
        assert ws not in manager.connection_info
        assert 1 not in manager.active_connections  # Campaign should be removed

    def test_multiple_users_same_campaign(self):
        """Multiple users in same campaign should all be tracked."""
        manager = ConnectionManager()
        users = [MockWebSocket(i) for i in range(5)]

        # Connect all
        for i, ws in enumerate(users):
            asyncio.run(manager.connect(ws, campaign_id=1, user_id=i, username=f"user{i}"))

        assert manager.get_campaign_connections(1) == 5

        # Disconnect half
        for ws in users[:3]:
            manager.disconnect(ws)

        assert manager.get_campaign_connections(1) == 2

        # Disconnect rest
        for ws in users[3:]:
            manager.disconnect(ws)

        assert manager.get_campaign_connections(1) == 0
        assert 1 not in manager.active_connections

    def test_multiple_campaigns(self):
        """Connections across multiple campaigns should be isolated."""
        manager = ConnectionManager()

        # Create connections in different campaigns
        for campaign_id in range(1, 4):
            for user_id in range(3):
                ws = MockWebSocket(campaign_id * 100 + user_id)
                asyncio.run(
                    manager.connect(
                        ws,
                        campaign_id=campaign_id,
                        user_id=user_id,
                        username=f"user{user_id}_c{campaign_id}",
                    )
                )

        assert manager.get_campaign_connections(1) == 3
        assert manager.get_campaign_connections(2) == 3
        assert manager.get_campaign_connections(3) == 3

        # Disconnect all from campaign 2
        campaign2_connections = list(manager.active_connections[2])
        for ws in campaign2_connections:
            manager.disconnect(ws)

        assert manager.get_campaign_connections(1) == 3
        assert manager.get_campaign_connections(2) == 0
        assert manager.get_campaign_connections(3) == 3
        assert 2 not in manager.active_connections

    def test_disconnect_nonexistent_is_safe(self):
        """Disconnecting a non-connected WebSocket should be safe."""
        manager = ConnectionManager()
        ws = MockWebSocket(999)

        # Should not raise
        manager.disconnect(ws)

        # Should still work normally
        assert manager.get_campaign_connections(1) == 0

    def test_double_disconnect_is_safe(self):
        """Double disconnect should be safe."""
        manager = ConnectionManager()
        ws = MockWebSocket(1)

        asyncio.run(manager.connect(ws, campaign_id=1, user_id=1, username="test"))
        manager.disconnect(ws)
        manager.disconnect(ws)  # Should not raise

        assert manager.get_campaign_connections(1) == 0


class TestConnectionManagerStress:
    """Stress tests for connection manager stability."""

    def test_rapid_connect_disconnect_cycles(self):
        """Rapid connect/disconnect cycles should not leak memory."""
        manager = ConnectionManager()
        cycles = 100

        for cycle in range(cycles):
            ws = MockWebSocket(cycle)
            asyncio.run(manager.connect(ws, campaign_id=1, user_id=1, username="stress"))
            manager.disconnect(ws)

        # After all cycles, should be clean
        assert len(manager.active_connections) == 0
        assert len(manager.connection_info) == 0

    def test_many_simultaneous_connections(self):
        """Many simultaneous connections should be handled."""
        manager = ConnectionManager()
        num_connections = 50  # Simulating a large session

        connections = []
        for i in range(num_connections):
            ws = MockWebSocket(i)
            asyncio.run(manager.connect(ws, campaign_id=1, user_id=i, username=f"user{i}"))
            connections.append(ws)

        assert manager.get_campaign_connections(1) == num_connections

        # Disconnect all
        for ws in connections:
            manager.disconnect(ws)

        assert manager.get_campaign_connections(1) == 0
        assert len(manager.connection_info) == 0

    def test_interleaved_connect_disconnect(self):
        """Interleaved connects and disconnects should work correctly."""
        manager = ConnectionManager()
        active = []

        # Simulate realistic session: users joining and leaving
        for i in range(100):
            ws = MockWebSocket(i)
            asyncio.run(manager.connect(ws, campaign_id=1, user_id=i % 10, username=f"user{i % 10}"))
            active.append(ws)

            # Every 5 connections, disconnect some
            if i % 5 == 4 and len(active) > 3:
                for _ in range(3):
                    old_ws = active.pop(0)
                    manager.disconnect(old_ws)

        # Final count should match active list
        assert manager.get_campaign_connections(1) == len(active)

        # Clean up all
        for ws in active:
            manager.disconnect(ws)

        assert manager.get_campaign_connections(1) == 0

    def test_broadcast_with_failed_connection(self):
        """Broadcast should handle and clean up failed connections."""

        async def run_test():
            manager = ConnectionManager()

            good_ws = MockWebSocket(1)
            bad_ws = MockWebSocket(2)
            bad_ws.closed = True  # Simulate already closed

            await manager.connect(good_ws, campaign_id=1, user_id=1, username="good")
            await manager.connect(bad_ws, campaign_id=1, user_id=2, username="bad")

            assert manager.get_campaign_connections(1) == 2

            # Broadcast should clean up the bad connection
            await manager.broadcast_to_campaign(1, {"type": "test", "data": "hello"})

            # Bad connection should be removed
            assert manager.get_campaign_connections(1) == 1
            assert bad_ws not in manager.connection_info

        asyncio.run(run_test())

    def test_send_personal_message_failed_connection(self):
        """Personal message to failed connection should clean it up."""

        async def run_test():
            manager = ConnectionManager()

            ws = MockWebSocket(1)
            ws.closed = True

            await manager.connect(ws, campaign_id=1, user_id=1, username="test")

            # This should handle the error and disconnect
            await manager.send_personal_message({"type": "test"}, ws)

            assert ws not in manager.connection_info

        asyncio.run(run_test())


class TestMemoryLeaks:
    """Tests specifically targeting memory leak scenarios."""

    def test_no_reference_cycles(self):
        """Manager should not create reference cycles with connections."""
        manager = ConnectionManager()

        # Create and disconnect many times
        for i in range(50):
            ws = MockWebSocket(i)
            asyncio.run(manager.connect(ws, campaign_id=1, user_id=1, username="test"))
            manager.disconnect(ws)

        # Force garbage collection
        gc.collect()

        # Check manager is clean
        assert len(manager.active_connections) == 0
        assert len(manager.connection_info) == 0

    def test_campaign_dict_cleanup(self):
        """Empty campaign entries should be removed from dict."""
        manager = ConnectionManager()

        # Create connections in multiple campaigns
        for campaign_id in range(1, 11):
            ws = MockWebSocket(campaign_id)
            asyncio.run(manager.connect(ws, campaign_id=campaign_id, user_id=1, username="test"))

        assert len(manager.active_connections) == 10

        # Disconnect all
        for campaign_id in range(1, 11):
            ws = MockWebSocket(campaign_id)
            # Need to find the actual connection
            campaign_ws = list(manager.active_connections[campaign_id])[0]
            manager.disconnect(campaign_ws)

        # All campaign entries should be removed
        assert len(manager.active_connections) == 0

    def test_long_session_simulation(self):
        """Simulate a long session with many events."""
        manager = ConnectionManager()
        events = 1000  # Simulate many events over a long session

        active_connections = {}

        for event in range(events):
            action = event % 3

            if action == 0:  # Join
                user_id = event % 20
                if user_id not in active_connections:
                    ws = MockWebSocket(event)
                    asyncio.run(manager.connect(ws, campaign_id=1, user_id=user_id, username=f"user{user_id}"))
                    active_connections[user_id] = ws

            elif action == 1:  # Leave
                if active_connections:
                    user_id = list(active_connections.keys())[0]
                    ws = active_connections.pop(user_id)
                    manager.disconnect(ws)

            else:  # Broadcast (async wrapped in run)
                if active_connections:
                    asyncio.run(manager.broadcast_to_campaign(1, {"type": "event", "id": event}))

        # Verify consistency
        assert manager.get_campaign_connections(1) == len(active_connections)

        # Clean up remaining
        for ws in active_connections.values():
            manager.disconnect(ws)

        assert manager.get_campaign_connections(1) == 0
        assert len(manager.connection_info) == 0


class TestConcurrency:
    """Tests for concurrent access patterns."""

    def test_concurrent_broadcasts(self):
        """Multiple concurrent broadcasts should be safe."""

        async def run_test():
            manager = ConnectionManager()

            # Connect several users
            connections = []
            for i in range(10):
                ws = MockWebSocket(i)
                await manager.connect(ws, campaign_id=1, user_id=i, username=f"user{i}")
                connections.append(ws)

            # Clear connect notifications to get clean count
            for ws in connections:
                ws.sent_messages.clear()

            # Send many broadcasts concurrently
            tasks = []
            for i in range(50):
                task = manager.broadcast_to_campaign(1, {"type": "concurrent", "id": i})
                tasks.append(task)

            await asyncio.gather(*tasks)

            # All connections should still be valid
            assert manager.get_campaign_connections(1) == 10

            # Each connection should have received all broadcast messages
            for ws in connections:
                assert len(ws.sent_messages) == 50

        asyncio.run(run_test())

    def test_connect_during_broadcast(self):
        """Connecting during a broadcast should be safe."""

        async def run_test():
            manager = ConnectionManager()

            # Initial connection
            ws1 = MockWebSocket(1)
            await manager.connect(ws1, campaign_id=1, user_id=1, username="user1")

            # Start broadcast
            broadcast_task = asyncio.create_task(manager.broadcast_to_campaign(1, {"type": "test"}))

            # Connect new user during broadcast
            ws2 = MockWebSocket(2)
            await manager.connect(ws2, campaign_id=1, user_id=2, username="user2")

            await broadcast_task

            # Both should be connected
            assert manager.get_campaign_connections(1) == 2

        asyncio.run(run_test())
