import argparse
import json
import time
from pathlib import Path

from kafka import KafkaProducer


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "documents.json"
KAFKA_BOOTSTRAP_SERVERS = "localhost:29092"
KAFKA_TOPIC = "documents"


def main():
    parser = argparse.ArgumentParser(
        description="Stream Cranfield documents into Kafka."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of documents to send. Default: all documents.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.2,
        help="Delay in seconds between messages. Default: 0.2.",
    )
    args = parser.parse_args()

    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be at least 1.")

    if args.interval < 0:
        parser.error("--interval cannot be negative.")

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda value: json.dumps(
            value, ensure_ascii=False
        ).encode("utf-8"),
        acks="all",
        retries=5,
    )

    sent = 0

    try:
        with DATA_PATH.open("r", encoding="utf-8") as file:
            for line in file:
                if args.limit is not None and sent >= args.limit:
                    break

                if not line.strip():
                    continue

                document = json.loads(line)

                producer.send(KAFKA_TOPIC, value=document)
                sent += 1

                print(
                    f"Sent document {sent}: "
                    f"id={document.get('id')}, "
                    f"title={document.get('title', '')[:60]}"
                )

                if args.interval > 0:
                    time.sleep(args.interval)

        producer.flush()
        print(f"\nFinished. Successfully acknowledged {sent} messages.")

    finally:
        producer.close()


if __name__ == "__main__":
    main()
