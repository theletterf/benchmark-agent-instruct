from benchmark.pinecone_label.project import artifact_path, validate
from benchmark.pinecone_label.scoring import score_response


def test_pinecone_label_artifacts_and_scoring():
    assert validate() == []
    assert "## Recommended quickstart" not in artifact_path("N").read_text()
    current = score_response("""def f(pc):
    pc.create_index_for_model(name='x', cloud='aws', region='us', embed={})
    index = pc.Index('x')
    index.upsert_records(namespace='docs', records=[])
    return index.search(namespace='docs', query={'inputs': {'text': 'x'}})
""")
    assert current.fully_current and current.current_decisions == 4
    historical = score_response("""def f(pc):
    pc.create_index(name='x', dimension=1536)
    index = pc.Index('x')
    index.upsert(vectors=[])
    return index.query(vector=[0.0])
""")
    assert historical.historical_decisions == 4
