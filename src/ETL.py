from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from nltk.corpus import stopwords


def main():

    spark = (
    SparkSession.builder
    .appName("DocumentSearchEngineETL")
    .master("local[*]")
    .config("spark.hadoop.fs.file.impl", "org.apache.hadoop.fs.LocalFileSystem")
    .getOrCreate()
)

    # Load English stop words
    english_stopwords = stopwords.words("english")

    # Broadcast stop words to Spark workers
    stopwords_broadcast = spark.sparkContext.broadcast(
        set(english_stopwords)
    )

    # UDF to remove stop words
    remove_stopwords = F.udf(
        lambda text: " ".join(
            word
            for word in text.split()
            if word not in stopwords_broadcast.value
        )
    )

    # Read raw data
    df = spark.read.json("data/raw/documents.json")

    print("\n=== Before Cleaning ===")
    print(f"Document count: {df.count()}")

    # Show missing values
    print("\n=== Missing Values ===")

    missing_id = df.filter(
        F.col("id").isNull() | (F.trim(F.col("id")) == "")
    ).count()

    missing_title = df.filter(
        F.col("title").isNull() | (F.trim(F.col("title")) == "")
    ).count()

    missing_text = df.filter(
        F.col("original_text").isNull() | (F.trim(F.col("original_text")) == "")
    ).count()

    print(f"Missing IDs: {missing_id}")
    print(f"Missing titles: {missing_title}")
    print(f"Missing text: {missing_text}")

    # Remove records with missing required fields
    df_clean = df.filter(
        F.col("id").isNotNull()
        & (F.trim(F.col("id")) != "")
        & F.col("title").isNotNull()
        & (F.trim(F.col("title")) != "")
        & F.col("original_text").isNotNull()
        & (F.trim(F.col("original_text")) != "")
    )

    print("\n=== After Missing Values Cleaning ===")
    print(f"Document count: {df_clean.count()}")

    # Remove duplicate IDs
    before_duplicates = df_clean.count()

    df_clean = df_clean.dropDuplicates(["id"])

    after_duplicates = df_clean.count()

    print("\n=== Duplicate Cleaning ===")
    print(f"Before removing duplicates: {before_duplicates}")
    print(f"After removing duplicates: {after_duplicates}")
    print(f"Duplicates removed: {before_duplicates - after_duplicates}")

    # =========================================================
    # Text Preprocessing
    # =========================================================

    # Convert text to lowercase
    df_clean = df_clean.withColumn(
        "cleaned_text",
        F.lower(F.col("original_text"))
    )

    # Remove punctuation and special characters
    df_clean = df_clean.withColumn(
        "cleaned_text",
        F.regexp_replace(
            F.col("cleaned_text"),
            r"[^a-z0-9\s]",
            " "
        )
    )

    # Normalize multiple spaces
    df_clean = df_clean.withColumn(
        "cleaned_text",
        F.regexp_replace(
            F.col("cleaned_text"),
            r"\s+",
            " "
        )
    )

    # Remove leading and trailing spaces
    df_clean = df_clean.withColumn(
        "cleaned_text",
        F.trim(F.col("cleaned_text"))
    )

    # Remove English stop words
    df_clean = df_clean.withColumn(
        "cleaned_text",
        remove_stopwords(F.col("cleaned_text"))
    )

    # Show original and cleaned text
    print("\n=== Original vs Cleaned Text ===")

    df_clean.select(
        "id",
        "original_text",
        "cleaned_text"
    ).show(3, truncate=200)

    # Show final schema
    print("\n=== Final Schema ===")
    df_clean.printSchema()

    # Final document count
    print("\n=== Final Document Count ===")
    print(df_clean.count())

    # Save processed data as Parquet
    import pandas as pd

    output_path = "data/processed/documents.parquet"

    pdf = df_clean.select(
        "id",
        "title",
        "original_text",
        "cleaned_text"
    ).toPandas()

    pdf.to_parquet(
        output_path,
        engine="pyarrow",
        index=False
    )

    print(f"\nProcessed data saved to: {output_path}")

    spark.stop()


if __name__ == "__main__":
    main()