from pyspark.sql import SparkSession


spark = (
    SparkSession.builder
    .appName("DocumentSearchEngineSQL")
    .master("local[*]")
    .config(
        "spark.hadoop.fs.file.impl",
        "org.apache.hadoop.fs.LocalFileSystem"
    )
    .getOrCreate()
)

# Load processed documents
df = spark.read.parquet(
    "data/processed/documents.parquet"
)

# Create temporary SQL table
df.createOrReplaceTempView("documents")


# Read SQL queries from file
with open("sql/analysis.sql", "r", encoding="utf-8") as file:
    sql_script = file.read()


# Run each SQL query separately
queries = [
    query.strip()
    for query in sql_script.split(";")
    if query.strip()
]


for i, query in enumerate(queries, start=1):

    print(f"\n=== Query {i} ===")

    result = spark.sql(query)

    result.show(truncate=False)


spark.stop()