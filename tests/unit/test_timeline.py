"""Unit tests for deterministic timeline builder."""

from datetime import datetime, timezone, timedelta
import pytest

from aletheia.evidence.events import Event, EventType, Timeline


@pytest.mark.unit
def test_timeline_chronological_ordering():
    """Verify Timeline maintains strict chronological order regardless of insertion order."""
    t0 = datetime(2026, 9, 25, 2, 0, 0, tzinfo=timezone.utc)
    t1 = t0 + timedelta(minutes=2)
    t2 = t0 + timedelta(minutes=4)

    e_mid = Event(
        event_id="EVT-2",
        timestamp=t1,
        type=EventType.DEPLOYMENT_COMPLETE,
        service="checkout-api",
        summary="Deployment finished",
    )
    e_last = Event(
        event_id="EVT-3",
        timestamp=t2,
        type=EventType.DB_LATENCY_INCREASE,
        service="checkout-api",
        summary="Latency rose",
    )
    e_first = Event(
        event_id="EVT-1",
        timestamp=t0,
        type=EventType.NORMAL_TRAFFIC,
        service="checkout-api",
        summary="Normal traffic",
    )

    timeline = Timeline()
    # Insert out of order
    timeline.add_event(e_last)
    timeline.add_event(e_first)
    timeline.add_event(e_mid)

    sorted_events = timeline.get_events()
    assert [e.event_id for e in sorted_events] == ["EVT-1", "EVT-2", "EVT-3"]


@pytest.mark.unit
def test_timeline_time_window_and_ascii():
    """Verify time window filtering and ASCII output formatting."""
    t0 = datetime(2026, 9, 25, 2, 0, 0, tzinfo=timezone.utc)
    timeline = Timeline()
    timeline.add_event(
        Event(
            event_id="E1",
            timestamp=t0,
            type=EventType.NORMAL_TRAFFIC,
            service="checkout-api",
            summary="Normal state",
        )
    )
    timeline.add_event(
        Event(
            event_id="E2",
            timestamp=t0 + timedelta(minutes=10),
            type=EventType.API_LATENCY_INCREASE,
            service="checkout-api",
            summary="Latency increased",
        )
    )

    window = timeline.get_time_window(t0, t0 + timedelta(minutes=5))
    assert len(window) == 1
    assert window[0].event_id == "E1"

    ascii_out = timeline.format_ascii()
    assert "=== INCIDENT TIMELINE ===" in ascii_out
    assert "Normal state" in ascii_out
    assert "Latency increased" in ascii_out
