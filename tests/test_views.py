from datetime import datetime

from views.plank import generate_progress_graph


def test_generate_progress_graph_returns_image(sample_plank_data):
    """generate_progress_graph should return a non-empty image buffer."""
    points = [
        (datetime.strptime(date_str, "%Y-%m-%d"), duration)
        for date_str, duration in sample_plank_data
    ]

    buf = generate_progress_graph(points)

    assert buf is not None
    assert buf.getbuffer().nbytes > 0


def test_generate_progress_graph_empty_returns_none():
    """generate_progress_graph should return None for empty input."""
    assert generate_progress_graph([]) is None

