# Pinecone section/heading replication

## Question

Does removing section hierarchy, adding a generic heading, or targeting a heading to AI agents change selection of the current Pinecone Quickstart API pattern?

## Design

One task, three conditions, and three temperature-zero repetitions per condition: nine OpenRouter calls total. The frozen source is the [Pinecone Quickstart](https://docs.pinecone.io/guides/get-started/quickstart), retrieved on 2026-08-17. The body documentation is identical in every condition.

- **N — No section:** no heading above the shared body.
- **G — Generic section:** `## Recommended quickstart` above that body.
- **AI — AI-targeted section:** `## For AI agents and LLMs` above that body.

The four deterministic decisions are model-based index creation, record ingestion, text search, and text inputs. The primary measure is decision-level current API selection.

## Results

| Condition | Calls | Current decisions | Decision-level currentness | Fully current responses | Prompt tokens | Cost |
|---|---:|---:|---:|---:|---:|---:|
| N — No section | 3 | 12 / 12 | 100% | 3 / 3 | 1,254 | $0.016092 |
| G — Generic section | 3 | 12 / 12 | 100% | 3 / 3 | 1,272 | $0.016146 |
| AI — AI-targeted section | 3 | 12 / 12 | 100% | 3 / 3 | 1,281 | $0.016173 |
| **Total** | **9** | **36 / 36** | **100%** | **9 / 9** | **3,807** | **$0.048411** |

All responses used all four current Quickstart APIs. Completion tokens totalled 2,466.

## Planned contrasts

| Contrast | Difference in current-decision rate |
|---|---:|
| No section → generic section | 0 percentage points |
| Generic section → AI-targeted section | 0 percentage points |
| No section → AI-targeted section | 0 percentage points |

## Interpretation

This is a ceiling result, including the no-section control. Under this narrow task and source excerpt, neither generic section hierarchy nor an AI-targeted heading produced a detectable change. It does not establish that headings never matter: the shared documentation body itself explicitly directs the current Quickstart pattern and was followed in every call.

The earlier generic-versus-AI-only run is retained unchanged as a separate historical result.
