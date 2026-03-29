import os
import json
import sqlite3
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "phonepe.db"
MASTER_CSV_PATH = DATA_DIR / "phonepe_master_cleaned.csv"
EDA_CSV_PATH = DATA_DIR / "phonepe_cleaned.csv"
FILE_INDEX_CSV_PATH = DATA_DIR / "phonepe_file_index.csv"


def safe_read_json(file_path: Path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def clean_text(value):
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    return text.replace("-", " ").replace("_", " ").title()


def try_int(value):
    try:
        return int(value)
    except Exception:
        return None


def try_float(value):
    try:
        return float(value)
    except Exception:
        return None


def infer_metadata(file_path: Path, data_dir: Path):
    rel_parts = file_path.relative_to(data_dir).parts
    parts = [str(p) for p in rel_parts[:-1]]

    meta = {
        "relative_path": str(file_path.relative_to(data_dir)),
        "top_folder": rel_parts[0] if len(rel_parts) > 0 else None,
        "sub_folder": rel_parts[1] if len(rel_parts) > 1 else None,
        "country": None,
        "state": None,
        "district": None,
        "year": None,
        "quarter": None,
        "file_name": file_path.name,
    }

    for i, part in enumerate(parts):
        low = part.lower()
        if low == "country" and i + 1 < len(parts):
            meta["country"] = clean_text(parts[i + 1])
        elif low == "state" and i + 1 < len(parts):
            meta["state"] = clean_text(parts[i + 1])
        elif low == "district" and i + 1 < len(parts):
            meta["district"] = clean_text(parts[i + 1])

    for part in reversed(parts):
        yr = try_int(part)
        if yr is not None and 2000 <= yr <= 2100:
            meta["year"] = yr
            break

    q = try_int(file_path.stem)
    if q is not None and 1 <= q <= 4:
        meta["quarter"] = q

    return meta


def make_base_row(meta, source_type):
    return {
        "source_type": source_type,
        "top_folder": meta["top_folder"],
        "sub_folder": meta["sub_folder"],
        "country": meta["country"],
        "state": meta["state"],
        "district": meta["district"],
        "year": meta["year"],
        "quarter": meta["quarter"],
        "file_name": meta["file_name"],
        "relative_path": meta["relative_path"],
        "entity_name": None,
        "entity_type": None,
        "transaction_type": None,
        "transaction_count": None,
        "transaction_amount": None,
        "registered_users": None,
        "app_opens": None,
        "brand": None,
        "value": None,
        "raw_json": None,
    }


def extract_rows_from_file(file_path: Path, data_dir: Path):
    data = safe_read_json(file_path)
    meta = infer_metadata(file_path, data_dir)

    rows = []
    top_folder = (meta["top_folder"] or "").lower()
    sub_folder = (meta["sub_folder"] or "").lower()

    # aggregated/transaction
    if top_folder == "aggregated" and sub_folder == "transaction":
        tx_data = data.get("data", {}).get("transactionData", []) or []
        for item in tx_data:
            tx_name = item.get("name")
            for inst in item.get("paymentInstruments", []) or []:
                row = make_base_row(meta, "aggregated_transaction")
                row["transaction_type"] = clean_text(tx_name)
                row["transaction_count"] = try_int(inst.get("count"))
                row["transaction_amount"] = try_float(inst.get("amount"))
                rows.append(row)

    # aggregated/user
    elif top_folder == "aggregated" and sub_folder == "user":
        agg = data.get("data", {}).get("aggregated", {}) or {}
        devices = data.get("data", {}).get("usersByDevice", []) or []

        if devices:
            for item in devices:
                row = make_base_row(meta, "aggregated_user")
                row["brand"] = clean_text(item.get("brand"))
                row["registered_users"] = try_int(agg.get("registeredUsers"))
                row["app_opens"] = try_int(agg.get("appOpens"))
                row["value"] = try_int(item.get("count"))
                rows.append(row)
        else:
            row = make_base_row(meta, "aggregated_user")
            row["registered_users"] = try_int(agg.get("registeredUsers"))
            row["app_opens"] = try_int(agg.get("appOpens"))
            rows.append(row)

    # aggregated/insurance
    elif top_folder == "aggregated" and sub_folder == "insurance":
        insurance_data = data.get("data", {}).get("transactionData", []) or []
        for item in insurance_data:
            tx_name = item.get("name")
            for inst in item.get("paymentInstruments", []) or []:
                row = make_base_row(meta, "aggregated_insurance")
                row["transaction_type"] = clean_text(tx_name)
                row["transaction_count"] = try_int(inst.get("count"))
                row["transaction_amount"] = try_float(inst.get("amount"))
                rows.append(row)

    # map/transaction
    elif top_folder == "map" and sub_folder == "transaction":
        hover = data.get("data", {}).get("hoverDataList", []) or []
        for item in hover:
            metric = (item.get("metric") or [{}])[0]
            row = make_base_row(meta, "map_transaction")
            row["district"] = clean_text(item.get("name"))
            row["entity_name"] = clean_text(item.get("name"))
            row["entity_type"] = "district"
            row["transaction_count"] = try_int(metric.get("count"))
            row["transaction_amount"] = try_float(metric.get("amount"))
            rows.append(row)

    # map/user
    elif top_folder == "map" and sub_folder == "user":
        hover = data.get("data", {}).get("hoverData", {}) or {}
        for district_name, district_info in hover.items():
            row = make_base_row(meta, "map_user")
            row["district"] = clean_text(district_name)
            row["entity_name"] = clean_text(district_name)
            row["entity_type"] = "district"
            row["registered_users"] = try_int(district_info.get("registeredUsers"))
            row["app_opens"] = try_int(district_info.get("appOpens"))
            rows.append(row)

    # map/insurance
    elif top_folder == "map" and sub_folder == "insurance":
        hover = data.get("data", {}).get("hoverDataList", []) or []
        for item in hover:
            metric = (item.get("metric") or [{}])[0]
            row = make_base_row(meta, "map_insurance")
            row["district"] = clean_text(item.get("name"))
            row["entity_name"] = clean_text(item.get("name"))
            row["entity_type"] = "district"
            row["transaction_count"] = try_int(metric.get("count"))
            row["transaction_amount"] = try_float(metric.get("amount"))
            rows.append(row)

    # top/transaction
    elif top_folder == "top" and sub_folder == "transaction":
        districts = data.get("data", {}).get("districts", []) or []
        pincodes = data.get("data", {}).get("pincodes", []) or []

        for item in districts:
            metric = item.get("metric", {}) or {}
            row = make_base_row(meta, "top_transaction")
            row["district"] = clean_text(item.get("entityName"))
            row["entity_name"] = clean_text(item.get("entityName"))
            row["entity_type"] = "district"
            row["transaction_count"] = try_int(metric.get("count"))
            row["transaction_amount"] = try_float(metric.get("amount"))
            rows.append(row)

        for item in pincodes:
            metric = item.get("metric", {}) or {}
            row = make_base_row(meta, "top_transaction")
            row["entity_name"] = str(item.get("entityName")) if item.get("entityName") is not None else None
            row["entity_type"] = "pincode"
            row["transaction_count"] = try_int(metric.get("count"))
            row["transaction_amount"] = try_float(metric.get("amount"))
            rows.append(row)

    # top/user
    elif top_folder == "top" and sub_folder == "user":
        districts = data.get("data", {}).get("districts", []) or []
        pincodes = data.get("data", {}).get("pincodes", []) or []

        for item in districts:
            row = make_base_row(meta, "top_user")
            row["district"] = clean_text(item.get("name"))
            row["entity_name"] = clean_text(item.get("name"))
            row["entity_type"] = "district"
            row["registered_users"] = try_int(item.get("registeredUsers"))
            rows.append(row)

        for item in pincodes:
            row = make_base_row(meta, "top_user")
            row["entity_name"] = str(item.get("name")) if item.get("name") is not None else None
            row["entity_type"] = "pincode"
            row["registered_users"] = try_int(item.get("registeredUsers"))
            rows.append(row)

    # top/insurance
    elif top_folder == "top" and sub_folder == "insurance":
        districts = data.get("data", {}).get("districts", []) or []
        pincodes = data.get("data", {}).get("pincodes", []) or []

        for item in districts:
            metric = item.get("metric", {}) or {}
            row = make_base_row(meta, "top_insurance")
            row["district"] = clean_text(item.get("entityName"))
            row["entity_name"] = clean_text(item.get("entityName"))
            row["entity_type"] = "district"
            row["transaction_count"] = try_int(metric.get("count"))
            row["transaction_amount"] = try_float(metric.get("amount"))
            rows.append(row)

        for item in pincodes:
            metric = item.get("metric", {}) or {}
            row = make_base_row(meta, "top_insurance")
            row["entity_name"] = str(item.get("entityName")) if item.get("entityName") is not None else None
            row["entity_type"] = "pincode"
            row["transaction_count"] = try_int(metric.get("count"))
            row["transaction_amount"] = try_float(metric.get("amount"))
            rows.append(row)

    else:
        # fallback for unknown JSON structures
        row = make_base_row(meta, "other")
        row["raw_json"] = json.dumps(data, ensure_ascii=False)
        rows.append(row)

    return rows


def create_tables(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS phonepe_master (
            source_type TEXT,
            top_folder TEXT,
            sub_folder TEXT,
            country TEXT,
            state TEXT,
            district TEXT,
            year INTEGER,
            quarter INTEGER,
            file_name TEXT,
            relative_path TEXT,
            entity_name TEXT,
            entity_type TEXT,
            transaction_type TEXT,
            transaction_count REAL,
            transaction_amount REAL,
            registered_users REAL,
            app_opens REAL,
            brand TEXT,
            value REAL,
            raw_json TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS phonepe_file_index (
            file_no INTEGER,
            relative_path TEXT,
            top_folder TEXT,
            sub_folder TEXT,
            country TEXT,
            state TEXT,
            district TEXT,
            year INTEGER,
            quarter INTEGER,
            row_count_extracted INTEGER,
            status TEXT,
            error TEXT
        )
    """)
    conn.commit()


def build_complete_dataset():
    json_files = sorted(DATA_DIR.rglob("*.json"))

    if not json_files:
        print(f"No JSON files found under: {DATA_DIR}")
        return

    print(f"Found {len(json_files)} JSON files.")

    conn = sqlite3.connect(DB_PATH)
    create_tables(conn)

    conn.execute("DELETE FROM phonepe_master")
    conn.execute("DELETE FROM phonepe_file_index")
    conn.commit()

    file_index_rows = []
    batch_rows = []
    batch_size = 5000

    for i, file_path in enumerate(json_files, start=1):
        try:
            meta = infer_metadata(file_path, DATA_DIR)
            rows = extract_rows_from_file(file_path, DATA_DIR)
            batch_rows.extend(rows)

            file_index_rows.append((
                i,
                meta["relative_path"],
                meta["top_folder"],
                meta["sub_folder"],
                meta["country"],
                meta["state"],
                meta["district"],
                meta["year"],
                meta["quarter"],
                len(rows),
                "success",
                None
            ))

        except Exception as e:
            meta = infer_metadata(file_path, DATA_DIR)
            file_index_rows.append((
                i,
                meta["relative_path"],
                meta["top_folder"],
                meta["sub_folder"],
                meta["country"],
                meta["state"],
                meta["district"],
                meta["year"],
                meta["quarter"],
                0,
                "failed",
                str(e)
            ))

        if len(batch_rows) >= batch_size:
            pd.DataFrame(batch_rows).to_sql("phonepe_master", conn, if_exists="append", index=False)
            batch_rows = []

        if len(file_index_rows) >= batch_size:
            conn.executemany("""
                INSERT INTO phonepe_file_index (
                    file_no, relative_path, top_folder, sub_folder, country, state,
                    district, year, quarter, row_count_extracted, status, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, file_index_rows)
            conn.commit()
            file_index_rows = []

        if i % 1000 == 0:
            print(f"Processed {i} files...")

    if batch_rows:
        pd.DataFrame(batch_rows).to_sql("phonepe_master", conn, if_exists="append", index=False)

    if file_index_rows:
        conn.executemany("""
            INSERT INTO phonepe_file_index (
                file_no, relative_path, top_folder, sub_folder, country, state,
                district, year, quarter, row_count_extracted, status, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, file_index_rows)
        conn.commit()

    master_df = pd.read_sql_query("SELECT * FROM phonepe_master", conn)
    master_df = master_df.drop_duplicates()
    master_df.to_csv(MASTER_CSV_PATH, index=False, encoding="utf-8")

    file_index_df = pd.read_sql_query("SELECT * FROM phonepe_file_index", conn)
    file_index_df.to_csv(FILE_INDEX_CSV_PATH, index=False, encoding="utf-8")

    eda_query = """
        SELECT
            state,
            district,
            year,
            quarter,
            transaction_type,
            transaction_count,
            transaction_amount
        FROM phonepe_master
        WHERE source_type IN (
            'aggregated_transaction',
            'map_transaction',
            'top_transaction',
            'aggregated_insurance',
            'map_insurance',
            'top_insurance'
        )
    """
    eda_df = pd.read_sql_query(eda_query, conn)
    eda_df = eda_df.drop_duplicates()
    eda_df.to_csv(EDA_CSV_PATH, index=False, encoding="utf-8")

    conn.close()

    print(f"SQLite database saved to: {DB_PATH}")
    print(f"Master cleaned CSV saved to: {MASTER_CSV_PATH}")
    print(f"EDA cleaned CSV saved to: {EDA_CSV_PATH}")
    print(f"File index CSV saved to: {FILE_INDEX_CSV_PATH}")
    print(f"Master rows: {len(master_df)}")
    print(f"EDA rows: {len(eda_df)}")
    print("Done.")


if __name__ == "__main__":
    build_complete_dataset()