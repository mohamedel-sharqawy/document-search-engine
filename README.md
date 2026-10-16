<div align="center">

# Document Search Engine with Real-Time Streaming & Monitoring

**A real-time document search pipeline built on Kafka, Flink and Elasticsearch, with Prometheus and Grafana monitoring.**

![Docker Compose](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Apache Kafka](https://img.shields.io/badge/Apache%20Kafka-3.9.1-231F20?logo=apachekafka&logoColor=white)
![Apache Flink](https://img.shields.io/badge/Apache%20Flink-1.20.3-E6526F?logo=apacheflink&logoColor=white)
![Elasticsearch](https://img.shields.io/badge/Elasticsearch-8.17-005571?logo=elasticsearch&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?logo=streamlit&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-Metrics-E6522C?logo=prometheus&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-Dashboard-F46800?logo=grafana&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Java](https://img.shields.io/badge/Java-17-ED8B00?logo=openjdk&logoColor=white)

</div>

<p align="center">
  <img src="docs/images/architecture.png" alt="Architecture diagram" width="100%">
</p>

---

## Overview

This project ingests documents as a stream, validates and cleans them in real time, indexes them for full-text search, and exposes a search interface. The streaming layer is observed through a dedicated monitoring stack.

- Documents are prepared and explored in Python, then published to a Kafka topic.
- An Apache Flink job (`DocumentSearchJob`, Java 17) consumes the stream, validates and cleans each record, and writes it to Elasticsearch.
- A Streamlit app provides the search and retrieval interface.
- Prometheus scrapes Flink metrics and Grafana visualizes the health of the streaming job.

<!-- TODO: add docs/images/demo.gif (10-20 s: documents streaming in, then appearing in search results) -->
<p align="center">
  <img src="docs/images/demo.gif" alt="Demo: documents streaming in and appearing in search results" width="85%">
</p>

## Features

- **Real-time ingestion** through the Kafka topic `documents` (KRaft mode, 3 partitions).
- **Stream processing with Flink** that validates and cleans the `id`, `title` and `original_text` fields.
- **Fault tolerance** with Flink checkpointing every **5 seconds**.
- **Full-text search** on the Elasticsearch 8 index `documents`.
- **Search UI** built with Python and Streamlit.
- **Observability**: Flink JobManager and TaskManager metrics exposed in Prometheus format, scraped every **5 seconds**, and visualized in Grafana.
- **Containerized infrastructure** with Docker Compose and a custom Flink image that bundles the Kafka, Elasticsearch and Prometheus connectors.

## Architecture

| Layer | Component | Role |
|---|---|---|
| Ingestion | Python data preparation + Kafka producer | Prepares documents and publishes them to topic `documents` |
| Messaging | Apache Kafka 3.9.1 | Broker; topic `documents`; bootstrap address `kafka:9092` inside the Docker network |
| Stream processing | Apache Flink 1.20.3 (`DocumentSearchJob`) | Reads from Kafka, validates/cleans fields, writes to Elasticsearch |
| Storage / search | Elasticsearch 8.17 | Index `documents`; stores processed documents and serves search |
| Application | Python / Streamlit | Search and retrieval UI |
| Monitoring | Prometheus + Grafana | Metrics scraping and dashboards |

**Data flow:** `Documents → Python producer → Kafka → Flink → Elasticsearch → Streamlit`

**Monitoring flow (separate from the data pipeline):** `Flink JobManager / TaskManager → Prometheus → Grafana`

> The Kafka producer and the Streamlit app are application components that interact with the infrastructure. Kafka, Flink (JobManager and TaskManager) and Elasticsearch run in Docker Compose.

## Tech Stack

| Technology | Used for |
|---|---|
| Python 3.12 | Data preparation and exploration, Kafka producer, Streamlit app |
| Pandas, NumPy, SciPy, scikit-learn, PyArrow | Data processing (see [`requirements.txt`](requirements.txt)) |
| Apache Kafka 3.9.1 | Message broker for document streaming |
| Apache Flink 1.20.3 (Java 17, Maven) | Stream processing job `DocumentSearchJob` |
| Elasticsearch 8.17 | Document storage and search |
| Streamlit | Search user interface |
| Prometheus | Metrics collection |
| Grafana | Monitoring dashboard |
| Docker Compose | Running the infrastructure services |

## How It Works

1. **Prepare the data.** The dataset is explored and prepared in Python.
2. **Publish to Kafka.** The producer sends each document as a message to the topic `documents`.
3. **Process with Flink.** `DocumentSearchJob` reads the messages, validates and cleans `id`, `title` and `original_text`, with checkpointing every 5 seconds and parallelism 1.
4. **Index in Elasticsearch.** Processed documents are written to the `documents` index.
5. **Search.** The Streamlit app lets users search and retrieve documents.
   <!-- TODO: confirm src/app.py queries Elasticsearch. requirements.txt has no Elasticsearch client, so if the app searches local data (for example TF-IDF with scikit-learn), describe that here instead. -->
6. **Monitor.** Prometheus scrapes the Flink JobManager and TaskManager metrics every 5 seconds; Grafana queries Prometheus to render the dashboard.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Java 17 and Maven (to build the Flink job)
- Python 3.12 (to run the producer and the Streamlit app locally)

### 1. Clone the repository

```bash
git clone https://github.com/mohamedel-sharqawy/document-search-engine.git
cd document-search-engine
```

### 2. Build the custom Flink image

The Flink image bundles the Kafka, Elasticsearch 8 and Prometheus connector JARs from [`connectors/`](connectors/).

```bash
docker build -f Dockerfile.flink -t document-search-flink:1.20.3 .
```

### 3. Start the infrastructure

```bash
docker compose up -d
docker compose ps
```

### 4. Build the Flink job

```bash
mvn clean package
```

The JAR is created in `target/` (`document-search-streaming-1.0.0.jar`).

### 5. Submit the job to Flink

Open the Flink Web UI at `http://localhost:8081`, go to **Submit New Job**, upload the JAR and set the entry class to `DocumentSearchJob`.

<!-- TODO: add the fully qualified entry class (package + DocumentSearchJob) and any program arguments -->

### 6. Run the producer

```bash
# TODO: replace with the real command (script name and arguments)
python src/producer.py
```

### 7. Launch the search app

```bash
pip install -r requirements.txt
cd src
streamlit run app.py
```

The app is also containerized. See the [`Dockerfile`](Dockerfile):

```bash
docker build -t document-search-app .
docker run -p 8501:8501 document-search-app
```

### 8. Verify

```bash
# Documents indexed in Elasticsearch
curl "http://localhost:9200/documents/_count"

# Flink metrics endpoints
curl http://localhost:9249/metrics   # JobManager
curl http://localhost:9250/metrics   # TaskManager
```

### Stop everything

```bash
docker compose down
# add -v to also remove the Kafka and Elasticsearch volumes
```

## Services & Ports

These addresses work on your own machine after you start the stack locally with Docker Compose.

| Service | Address | Notes |
|---|---|---|
| Kafka (inside the Docker network) | `kafka:9092` | Bootstrap address used by Flink |
| Kafka (from the host) | `localhost:29092` | Host listener, used by a producer running outside Docker |
| Flink Web UI | `http://localhost:8081` | JobManager UI |
| Flink JobManager metrics | `http://localhost:9249/metrics` | Prometheus endpoint |
| Flink TaskManager metrics | `http://localhost:9250/metrics` | Mapped to port 9249 inside the container |
| Elasticsearch | `http://localhost:9200` | Index `documents` |
| Streamlit app | `http://localhost:8501` | Search UI |
| Prometheus | `http://localhost:9090` | Scrape interval: 5 s |
| Grafana | `http://localhost:3000` | Monitoring dashboard |

<!-- TODO: Prometheus and Grafana are not defined in docker-compose.yml yet. Add them (or remove their rows and the Monitoring section) so this table matches the repo. -->

<!-- TODO: add docs/images/streamlit-search.png and docs/images/flink-ui.png -->
<p align="center">
  <img src="docs/images/streamlit-search.png" alt="Streamlit search interface" width="85%">
</p>

<p align="center">
  <img src="docs/images/flink-ui.png" alt="Flink Web UI showing the running job" width="85%">
</p>

## Monitoring

Monitoring is a separate layer and does not touch the document data pipeline.

- **Flink JobManager** exposes Prometheus metrics (port `9249`).
- **Flink TaskManager** exposes Prometheus metrics (port `9250` on the host, `9249` inside the container).
- **Prometheus** scrapes both endpoints every **5 seconds**.
- **Grafana** queries Prometheus and displays the dashboard.

Metrics shown on the dashboard:

| Metric | Source |
|---|---|
| Running Flink jobs | JobManager |
| Registered TaskManagers | JobManager |
| Available and total task slots | JobManager |
| JVM heap memory usage | JobManager / TaskManager |
| JVM CPU load | JobManager / TaskManager |

<!-- TODO: add docs/images/grafana-dashboard.png -->
<p align="center">
  <img src="docs/images/grafana-dashboard.png" alt="Grafana monitoring dashboard" width="85%">
</p>

## Configuration

| Setting | Value | Where |
|---|---|---|
| Kafka topic | `documents` (3 partitions) | `docker-compose.yml`, producer, Flink job |
| Kafka bootstrap address | `kafka:9092` (in-network) / `localhost:29092` (host) | `docker-compose.yml` |
| Elasticsearch index | `documents` | Flink job |
| Flink checkpoint interval | 5 seconds | `DocumentSearchJob` |
| Flink parallelism | 1 (`parallelism.default`) | `docker-compose.yml` |
| Task slots per TaskManager | 2 | `docker-compose.yml` |
| Flink process memory | 1024 MB (JobManager and TaskManager) | `docker-compose.yml` |
| Prometheus scrape interval | 5 seconds | Prometheus configuration |

> The Flink checkpoint interval and the Prometheus scrape interval are two independent settings that both happen to be 5 seconds.

> Elasticsearch runs as a single node with security disabled (`xpack.security.enabled: false`). This setup is intended for local development only.

## Project Structure

```
.
├── connectors/            # Flink connector JARs (Kafka, Elasticsearch 8, Prometheus metrics)
├── data/                  # Dataset and processed data
├── sql/                   # SQL scripts
├── src/                   # Python source (Streamlit app and related code)
├── Dockerfile             # Streamlit app image
├── Dockerfile.flink       # Custom Flink image with connectors
├── docker-compose.yml     # Kafka, Flink JobManager/TaskManager, Elasticsearch
├── pom.xml                # Maven build for the Flink job
├── requirements.txt       # Python dependencies
└── docs/images/           # Architecture diagram and screenshots
```

<!-- TODO: describe sql/ and the exact files in src/ and data/ -->

## Challenges & Lessons Learned

<!-- TODO: write 3-5 real points from your experience. Examples of what fits here: Docker networking (kafka:9092 vs localhost:29092), connector versions compatible with Flink 1.20, exposing Flink metrics for Prometheus. -->

- **Challenge:** _what was hard_ → **Solution:** _what you did_.
- **Lesson:** _what you would do differently next time_.

## Future Improvements

- Add filters, pagination and result highlighting to the search UI.
- Tune search relevance (analyzers, field boosting) in Elasticsearch.
- Add automated tests for the Flink job and the producer.
- Add alerting rules on the monitored metrics.
- Increase Flink parallelism and run load tests.

## License

<!-- TODO: add a LICENSE file (for example MIT) and keep this line, or remove this section -->
This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Author

**Mohamed**, Data Science student, Faculty of Artificial Intelligence, Menoufia University

- GitHub: [@mohamedel-sharqawy](https://github.com/mohamedel-sharqawy)
- LinkedIn: <!-- TODO: add link -->
