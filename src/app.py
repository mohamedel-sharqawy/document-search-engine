import html
import re
import streamlit as st
from pathlib import Path
import requests
import logging
import time

# Monitoring: logging configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "app.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8",
    force=True,
)

logger = logging.getLogger(__name__)


st.set_page_config(
    page_title="Document Search Engine",
    page_icon="🔎",
    layout="centered",
)

EXAMPLE_QUERIES = [
    "boundary layer",
    "aircraft vibration",
    "heat transfer",
    "supersonic flow",
]


def load_css():
    css_path = Path(__file__).parent / "style.css"
    css = css_path.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def build_snippet(text, query, length=280):
    """Cut a short excerpt around the first query word and highlight matches."""
    text = " ".join(str(text).split())
    terms = [t for t in re.findall(r"\w+", query.lower()) if len(t) > 2]

    start = 0
    positions = [text.lower().find(t) for t in terms if t in text.lower()]
    if positions:
        start = max(min(positions) - 60, 0)

    excerpt = html.escape(text[start:start + length])
    if terms:
        pattern = re.compile(
            "(" + "|".join(re.escape(t) for t in sorted(terms, key=len, reverse=True)) + ")",
            re.IGNORECASE,
        )
        excerpt = pattern.sub(r"<mark>\1</mark>", excerpt)

    prefix = "..." if start > 0 else ""
    suffix = "..." if start + length < len(text) else ""
    return f"{prefix}{excerpt}{suffix}"


def run_example(example_query):
    """Callback: fill the search box and trigger a search on the next rerun."""
    st.session_state["query_input"] = example_query
    st.session_state["run_search"] = True


load_css()


ELASTICSEARCH_URL = "http://localhost:9200"
ELASTICSEARCH_INDEX = "documents"

# Hero banner
st.markdown(
    f'<div class="hero">'
    f'<div class="hero-eyebrow">CRANFIELD COLLECTION</div>'
    f'<div class="hero-title">🔎 Document Search Engine</div>'
    f'<div class="hero-sub">Search scientific documents using Elasticsearch relevance ranking.</div>'
    f'<span class="chip">Elasticsearch Index</span>'
    f'<span class="chip">BM25 Relevance</span>'
    f'<span class="chip">Kafka + Flink Pipeline</span>'
    f'</div>',
    unsafe_allow_html=True,
)

# Search form (Enter key also works)
with st.form("search_form"):
    query = st.text_input(
        "Enter your search query",
        placeholder="Example: aircraft vibration",
        key="query_input",
    )
    col1, col2 = st.columns([2, 1], vertical_alignment="bottom")
    with col1:
        top_k = st.selectbox("Number of results", [3, 5, 10], index=1)
    with col2:
        submitted = st.form_submit_button("Search", type="primary", use_container_width=True)

# Example queries (clicking one runs the search immediately)
st.markdown('<div class="suggest-label">Try an example</div>', unsafe_allow_html=True)
example_cols = st.columns(len(EXAMPLE_QUERIES))
for col, example in zip(example_cols, EXAMPLE_QUERIES):
    col.button(
        example,
        key=f"example_{example}",
        on_click=run_example,
        args=(example,),
        use_container_width=True,
    )

run_flag = st.session_state.pop("run_search", False)
should_search = submitted or run_flag


if not should_search:
    st.markdown(
        '<div class="empty-state">'
        '<div class="empty-icon">🔎</div>'
        '<div class="empty-title">Start exploring the collection</div>'
        '<div class="empty-text">Type a query above or pick an example to see '
        'ranked results with highlighted matches.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
else:
    if not query.strip():
        logger.warning("Search rejected: empty query")
        st.warning("Please enter a search query.")
    else:
        start_time = time.perf_counter()
        try:
            response = requests.post(
                f"{ELASTICSEARCH_URL}/{ELASTICSEARCH_INDEX}/_search",
                json={
                    "size": top_k,
                    "query": {
                        "multi_match": {
                            "query": query,
                            "fields": ["title^2", "original_text"],
                        }
                    },
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            hits = data["hits"]["hits"]
            response_time = time.perf_counter() - start_time

            logger.info(
                "Elasticsearch search completed | query=%r | results=%d | response_time_ms=%.2f",
                query,
                len(hits),
                response_time * 1000,
            )

            if not hits:
                st.info("No relevant documents were found for this query.")
            else:
                best_score = float(hits[0]["_score"])

                st.markdown(
                    f'<div class="stat-grid">'
                    f'<div class="stat"><div class="stat-label">Results</div>'
                    f'<div class="stat-value">{len(hits)}</div></div>'
                    f'<div class="stat"><div class="stat-label">Search time</div>'
                    f'<div class="stat-value">{response_time * 1000:.1f}<small>ms</small></div></div>'
                    f'<div class="stat"><div class="stat-label">Top relevance score</div>'
                    f'<div class="stat-value">{best_score:.2f}</div></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                for rank, hit in enumerate(hits, start=1):
                    doc = hit["_source"]
                    score = float(hit["_score"])
                    width = (score / best_score * 100) if best_score > 0 else 0

                    doc_id = doc.get("id", hit["_id"])
                    title = doc.get("title", "Untitled document")
                    original_text = doc.get("original_text", "")

                    with st.container(border=True):
                        st.markdown(
                            f'<div class="result-row">'
                            f'<div class="rank">{rank}</div>'
                            f'<div class="result-body">'
                            f'<div class="result-title">{html.escape(str(title))}</div>'
                            f'<div class="result-meta">'
                            f'<span class="id-chip">ID {html.escape(str(doc_id))}</span>'
                            f'<div class="bar"><span style="width:{width:.0f}%"></span></div>'
                            f'<span class="score">Score: {score:.2f}</span>'
                            f'</div>'
                            f'<div class="snippet">{build_snippet(original_text, query)}</div>'
                            f'</div></div>',
                            unsafe_allow_html=True,
                        )

                        with st.expander("View full document"):
                            st.write(original_text)

        except requests.exceptions.RequestException:
            logger.exception("Elasticsearch request failed | query=%r", query)
            st.error(
                "Could not connect to Elasticsearch. Make sure Docker services are running."
            )
        except Exception:
            logger.exception("Search failed | query=%r", query)
            st.error("Something went wrong during search. Check the application logs.")