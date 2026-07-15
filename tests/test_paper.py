from mosaicopdf.models.paper import Paper


def test_create_paper():
    paper = Paper(
        name="Carta",
        width=612,
        height=792
    )

    assert paper.name == "Carta"
    assert paper.width == 612
    assert paper.height == 792