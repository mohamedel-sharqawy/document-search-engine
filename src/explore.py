import ir_datasets


def load_documents():
    dataset = ir_datasets.load("cranfield")
    return list(dataset.docs_iter())


def main():
    documents = load_documents()

    print("=" * 60)
    print("CRANFIELD DATASET EXPLORATION")
    print("=" * 60)

    # Number of documents
    print(f"\nTotal documents: {len(documents)}")

    # Example documents
    print("\nFirst 3 documents:")
    for doc in documents[:3]:
        print(f"\nID: {doc.doc_id}")
        print(f"Title: {doc.title}")
        print(f"Text length: {len(doc.text)} characters")

    # Missing values
    missing_ids = sum(
        1 for doc in documents
        if not doc.doc_id
    )

    missing_titles = sum(
        1 for doc in documents
        if not doc.title or not doc.title.strip()
    )

    missing_text = sum(
        1 for doc in documents
        if not doc.text or not doc.text.strip()
    )

    print("\nMissing values:")
    print(f"Missing IDs: {missing_ids}")
    print(f"Missing titles: {missing_titles}")
    print(f"Missing text: {missing_text}")

    # Duplicate IDs
    ids = [doc.doc_id for doc in documents]
    unique_ids = set(ids)

    duplicate_count = len(ids) - len(unique_ids)

    print("\nDuplicate IDs:")
    print(f"Duplicate records: {duplicate_count}")

    # Document lengths
    lengths = [len(doc.text) for doc in documents]

    print("\nDocument length:")
    print(f"Minimum: {min(lengths)} characters")
    print(f"Maximum: {max(lengths)} characters")
    print(f"Average: {sum(lengths) / len(lengths):.2f} characters")


if __name__ == "__main__":
    main()