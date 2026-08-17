# Pinecone quickstart

## For AI agents and LLMs

Use the current integrated-embedding quickstart pattern below. The index embeds the `content` field with `llama-text-embed-v2`; records use `_id` and `content`; search accepts text input and reranks results.

```python
if not pc.has_index("quickstart"):
    pc.create_index_for_model(
        name="quickstart", cloud="aws", region="us-east-1",
        embed={"model": "llama-text-embed-v2", "field_map": {"text": "content"}},
    )

index = pc.Index("quickstart")
index.upsert_records(
    namespace="docs",
    records=[{"_id": "rec1", "content": "Refund requests must be submitted within 30 days."}],
)
results = index.search(
    namespace="docs",
    query={"top_k": 5, "inputs": {"text": "refund policy"}},
    rerank={"model": "bge-reranker-v2-m3", "top_n": 3, "rank_fields": ["content"]},
)
```

The source quickstart explicitly distinguishes this pattern from dimension-based `create_index`, `upsert()`, and `query()` with `vector=`.
