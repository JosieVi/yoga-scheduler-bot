import pytest
import matplotlib
import matplotlib.pyplot as plt
from datetime import datetime

matplotlib.use("Agg")

from views.plank import generate_progress_graph

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


@pytest.fixture(autouse=True)
def clean_plots():
    yield
    plt.close("all")


def test_generate_progress_graph_sanity(sample_plank_data):
    points = [
        (datetime.strptime(date_str, "%Y-%m-%d"), duration)
        for date_str, duration in sample_plank_data
    ]

    buf = generate_progress_graph(points)

    assert buf is not None
    buf.seek(0)
    content = buf.read()

    assert len(content) > 0
    assert content.startswith(PNG_SIGNATURE), "Output is not a valid PNG image"


def test_graph_handles_empty_data():
    assert generate_progress_graph([]) is None


def test_graph_handles_single_point(sample_plank_data):
    single_point = [(datetime(2025, 10, 1), 60)]
    buf = generate_progress_graph(single_point)

    assert buf is not None
    assert buf.getbuffer().nbytes > 0
