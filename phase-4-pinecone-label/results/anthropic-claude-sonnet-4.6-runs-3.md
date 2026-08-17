# Pinecone AI-audience heading replication

Model: `anthropic/claude-sonnet-4.6`  
Temperature: 0  
Design: one task × two headings × three repetitions = six calls

## Manipulation

The frozen documents are byte-identical after replacing the level-two heading `Recommended quickstart` with `For AI agents and LLMs`.

## Results

| Condition | Responses | Current decisions | Fully current |
|---|---:|---:|---:|
| Recommended quickstart | 3 | 12/12 (100%) | 3/3 (100%) |
| For AI agents and LLMs | 3 | 12/12 (100%) | 3/3 (100%) |

Decision-level difference: **0.0 percentage points** (AI-targeted minus generic).

## Interpretation

No detectable label effect under a ceiling condition. The generic heading already produced the complete current Pinecone pattern: `create_index_for_model`, `upsert_records`, `search`, and text `inputs`.

The run consumed 2,553 provider-reported prompt tokens, 1,644 completion tokens, and $0.032319.
