import os
import sys
import pandas as pd


def main():
    base = os.path.dirname(os.path.dirname(__file__))
    parquet_path = os.path.join(base, "news_collection.parquet")
    csv_path = os.path.join(base, "news_collection_full.csv")

    if not os.path.exists(parquet_path):
        print(f"Parquet file not found: {parquet_path}")
        sys.exit(1)

    try:
        df = pd.read_parquet(parquet_path)
    except Exception as e:
        print("Failed to read parquet file. Error:", e)
        print("Make sure required engines are installed (pyarrow or fastparquet) and pandas is available.")
        sys.exit(2)

    print(f"Loaded dataframe with shape: {df.shape}")
    print("Sample rows:")
    print(df.head(10).to_string(index=False))

    try:
        df.to_csv(csv_path, index=False, encoding="utf-8")
        print(f"Wrote full CSV to: {csv_path}")
    except Exception as e:
        print("Failed to write CSV. Error:", e)
        sys.exit(3)


if __name__ == '__main__':
    main()
