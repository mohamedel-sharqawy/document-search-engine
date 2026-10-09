import json
from pathlib import Path

import ir_datasets


def load_documents():
    dataset = ir_datasets.load("cranfield")

    documents = []

    for doc in dataset.docs_iter():
        documents.append(
            {
                "id": doc.doc_id,
                "title": doc.title,
                "original_text": doc.text,
            }
        )

    return documents


def save_raw_data(documents):
    output_path = Path("data/raw/documents.json")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        for document in documents:
            file.write(json.dumps(document, ensure_ascii=False) + "\n")

    print(f"Saved {len(documents)} documents to {output_path}")


def main():
    documents = load_documents()
    save_raw_data(documents)


if __name__ == "__main__":
    main()