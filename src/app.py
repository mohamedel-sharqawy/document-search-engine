import html
import re
import streamlit as st
from pathlib import Path
from search import load_documents, build_tfidf, search
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


@st.cache_resource
def initialize_search_engine():
    df = load_documents()
    vectorizer, document_vectors = build_tfidf(df)
    return df, vectorizer, document_vectors


df, vectorizer, document_vectors = initialize_search_engine()

# Hero banner
st.markdown(
    f'<div class="hero">'
    f'<div class="hero-eyebrow">CRANFIELD COLLECTION</div>'
    f'<div class="hero-title">🔎 Document Search Engine</div>'
    f'<div class="hero-sub">Search scientific aerodynamics papers instantly using TF-IDF ranking.</div>'
    f'<span class="chip">{len(df):,} documents</span>'
    f'<span class="chip">TF-IDF</span>'
    f'<span class="chip">Cosine similarity</span>'
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
    # Empty state
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
            results = search(
                query,
                df,
                vectorizer,
                document_vectors,
                top_k=top_k,
            )

            useful_results = results[results["similarity"] > 0]

            response_time = time.perf_counter() - start_time

            logger.info(
                "Search completed | query=%r | results=%d | response_time_ms=%.2f",
                query,
                len(useful_results),
                response_time * 1000,
            )

            if useful_results.empty:
                logger.warning("No matches | query=%r", query)
                st.info("No relevant documents were found for this query.")

            else:
                best_match = float(useful_results["similarity"].max())

                # Stats row
                st.markdown(
                    f'<div class="stat-grid">'
                    f'<div class="stat"><div class="stat-label">Results</div>'
                    f'<div class="stat-value">{len(useful_results)}</div></div>'
                    f'<div class="stat"><div class="stat-label">Search time</div>'
                    f'<div class="stat-value">{response_time * 1000:.1f}<small>ms</small></div></div>'
                    f'<div class="stat"><div class="stat-label">Best match</div>'
                    f'<div class="stat-value">{best_match:.0%}</div></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                for rank, (_, row) in enumerate(useful_results.iterrows(), start=1):
                    sim = float(row["similarity"])
                    width = min(sim * 100, 100)

                    with st.container(border=True):
                        st.markdown(
                            f'<div class="result-row">'
                            f'<div class="rank">{rank}</div>'
                            f'<div class="result-body">'
                            f'<div class="result-title">{html.escape(str(row["title"]))}</div>'
                            f'<div class="result-meta">'
                            f'<span class="id-chip">ID {row["id"]}</span>'
                            f'<div class="bar"><span style="width:{width:.0f}%"></span></div>'
                            f'<span class="score">{sim:.1%} match</span>'
                            f'</div>'
                            f'<div class="snippet">{build_snippet(row["original_text"], query)}</div>'
                            f'</div></div>',
                            unsafe_allow_html=True,
                        )

                        with st.expander("View full document"):
                            st.write(row["original_text"])

        except Exception:
            logger.exception("Search failed | query=%r", query)
            st.error("Something went wrong during search. Check the application logs.")