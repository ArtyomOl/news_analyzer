import os
import sys
import pandas as pd


def main():
    base = os.path.dirname(os.path.dirname(__file__))
    parquet_path = os.path.join(base, "news_descriptions\\news_collection_old.parquet")
    aligned_csv_path = os.path.join(base, "news_collection_old.csv")
    full_csv_path = os.path.join(base, "news_collection_full.csv")

    if not os.path.exists(parquet_path):
        print(f"Parquet file not found: {parquet_path}")
        sys.exit(1)

    # Load source data from parquet
    try:
        df = pd.read_parquet(parquet_path)
    except Exception as e:
        print("Failed to read parquet file. Error:", e)
        print("Make sure required engines are installed (pyarrow or fastparquet) and pandas is available.")
        sys.exit(2)

    print(f"Loaded dataframe from {parquet_path} with shape: {df.shape}")
    # Normalize / split datetime into `date` and `time` if needed
    def ensure_date_time_columns(df: pd.DataFrame) -> pd.DataFrame:
        import re
        import pandas as pd
        import pandas.api.types as ptypes

        # If both exist, try to normalize formats
        if 'date' in df.columns and 'time' in df.columns:
            try:
                d = pd.to_datetime(df['date'], errors='coerce')
                t = pd.to_datetime(df['time'].astype(str), errors='coerce')
                if d.notna().sum() > 0 and (d.dt.time != pd.to_datetime('00:00').time()).any():
                    df['date'] = d.dt.strftime('%Y-%m-%d')
                    df['time'] = d.dt.strftime('%H:%M:%S')
                else:
                    df['date'] = d.dt.strftime('%Y-%m-%d')
                    if t.notna().any():
                        df['time'] = t.dt.strftime('%H:%M:%S')
                return df
            except Exception:
                pass

        # Candidate columns by name
        name_candidates = [c for c in df.columns if c.lower() in (
            'datetime', 'timestamp', 'ts', 'date_time', 'dateutc', 'published_at', 'created_at', 'pub_date', 'datepublished'
        )]

        # If none found, scan string/object columns for ISO-like datetime patterns
        if not name_candidates:
            dt_re = re.compile(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}")
            for c in df.columns:
                if ptypes.is_string_dtype(df[c]) or df[c].dtype == object:
                    sample = df[c].dropna().astype(str).head(200)
                    if any(dt_re.search(s) for s in sample):
                        name_candidates.append(c)
                        break

        if name_candidates:
            col = name_candidates[0]
            dt = pd.to_datetime(df[col], errors='coerce')
            df['date'] = dt.dt.strftime('%Y-%m-%d')
            df['time'] = dt.dt.strftime('%H:%M:%S')
            print(f"Split datetime-like column '{col}' into `date` and `time` (parsed {dt.notna().sum()} values)")
            return df

        # If only `date` exists and contains time information
        if 'date' in df.columns:
            dt = pd.to_datetime(df['date'], errors='coerce')
            if dt.notna().sum() > 0 and (dt.dt.time != pd.to_datetime('00:00').time()).any():
                df['date'] = dt.dt.strftime('%Y-%m-%d')
                df['time'] = dt.dt.strftime('%H:%M:%S')
                print("Parsed `date` column containing times into `date` and `time`")
                return df

        # Ensure columns exist even if NA
        if 'date' not in df.columns:
            df['date'] = pd.NA
        if 'time' not in df.columns:
            df['time'] = pd.NA
        print('No datetime-like column found; ensured `date` and `time` exist (may contain NA)')
        return df

    df = ensure_date_time_columns(df)

    # If full CSV exists, align columns to match its header
    # Align columns to match full CSV if available; else write aligned file with existing columns
    try:
        if os.path.exists(full_csv_path):
            full_cols = list(pd.read_csv(full_csv_path, nrows=0).columns)
            df = df.reindex(columns=full_cols)
        # write aligned output
        out_path = aligned_csv_path
        df_to_write = df
    except Exception as e:
        print("Failed to align columns to full CSV. Error:", e)
        print("Will write parquet contents to aligned CSV without alignment.")
        out_path = aligned_csv_path
        df_to_write = df

    try:
        df_to_write.to_csv(out_path, index=False, encoding="utf-8")
        print(f"Wrote CSV to: {out_path}")
    except Exception as e:
        print("Failed to write CSV. Error:", e)
        sys.exit(3)


if __name__ == '__main__':
    main()
