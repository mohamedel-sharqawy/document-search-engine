from pathlib import Path
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def load_documents():
    project_root = Path(__file__).resolve().parent.parent
    data_path = project_root / "data" / "processed" / "documents.parquet"
    df = pd.read_parquet(data_path)
    return df


def build_tfidf(df):

    vectorizer = TfidfVectorizer()

    document_vectors = vectorizer.fit_transform(
        df["cleaned_text"]
    )

    return vectorizer, document_vectors


def search(query, df, vectorizer, document_vectors, top_k=5):

    query_vector = vectorizer.transform([query])

    similarities = cosine_similarity(
        query_vector,
        document_vectors
    ).flatten()

    top_indices = similarities.argsort()[-top_k:][::-1]

    results = df.iloc[top_indices].copy()

    results["similarity"] = similarities[top_indices]

    return results


if __name__ == "__main__":

    df = load_documents()

    vectorizer, document_vectors = build_tfidf(df)

    print(f"Documents loaded: {len(df)}")
    print(f"TF-IDF terms: {document_vectors.shape[1]}")

    query = input("\nEnter your search query: ")

    results = search(
        query,
        df,
        vectorizer,
        document_vectors
    )

    print("\n=== Search Results ===")

    for _, row in results.iterrows():

        print(f"\nDocument ID: {row['id']}")
        print(f"Title: {row['title']}")
        print(f"Similarity: {row['similarity']:.4f}")