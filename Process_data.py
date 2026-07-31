import json
from pathlib import Path
import re
import numpy as np
import pandas as pd

# Define paths to your templates and testing data
IS_PATH = Path("0.1.1 Income Statement (testing data).xlsx")
BS_PATH = Path("0.1.2 Balance Sheet (testing data).xlsx")
CF_PATH = Path("0.1.3 Cash Flow Statement(testing data).xlsx")
OUTPUT_JSON_PATH = Path("data.json")


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
  """Standardizes column naming conventions across all statements.

  - Strips leading/trailing whitespace from all column headers.
  - Normalizes year/period column names (e.g., converts '31 Dec 2025' or 'FY2025'
  to '2025')
    so that Income Statement, Balance Sheet, and Cash Flow use uniform period
    keys.
  """
  new_columns = {}
  for col in df.columns:
    col_str = str(col).strip()
    # Search for a 4-digit year pattern (2023, 2024, 2025, 2026, etc.)
    match = re.search(r"(20\d{2})", col_str)
    if match:
      # Standardize period column to just the 4-digit year string
      new_columns[col] = match.group(1)
    else:
      new_columns[col] = col_str
  df = df.rename(columns=new_columns)
  return df


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
  """Cleans structural fields, strips whitespace from keys and text cells,

  and maps NaN values to None for valid JSON compliance.
  """
  # 1. Standardize column names (strips whitespace and standardizes years)
  df = standardize_columns(df)

  # 2. Remove unwanted artifact columns (like Excel 'Unnamed: X' columns)
  df = df.loc[:, ~df.columns.str.contains(r"^Unnamed", na=False)]

  # 3. Strip leading and trailing whitespace from all string/text cell values
  # This resolves issues like trailing spaces in line items (e.g., 'Operating Cash Flow (CFO) ')
  for col in df.select_dtypes(include=["object", "string"]).columns:
    df[col] = df[col].apply(
        lambda x: x.strip() if isinstance(x, str) else x
    )

  # 4. Replace NaN/NaT with None so json.dump outputs clean 'null' values
  return df.replace({np.nan: None})


def parse_financial_sheet(file_path: Path, sheet_name: str) -> dict:
  """Universal high-fidelity staging parser for tabular financial statements.

  Preserves hierarchical rows, counts original Excel rows accurately for

  metadata, and ensures uniform column naming.
  """
  print(f"Reading complete dataset for {sheet_name} from {file_path}...")

  if file_path.suffix == ".csv":
    df_raw = pd.read_csv(file_path)
  else:
    df_raw = pd.read_excel(file_path)

  # Capture original Excel physical row count before cleaning/filtering
  original_row_count = len(df_raw)

  # Clean and normalize the dataframe
  df_cleaned = clean_dataframe(df_raw)

  # Drop rows where all elements are null (empty structural spacer rows)
  df_filtered = df_cleaned.dropna(how="all")

  return {
      "table_rows": df_filtered.to_dict(orient="records"),
      "columns": list(df_filtered.columns),
      "total_rows": original_row_count,  # Preserves original physical row count
      "notes": (
          f"Complete raw data extraction layer preserving original {sheet_name}"
          " structure with standardized schema"
      ),
  }


def main():
  print("--- Starting Standardized Financial Data Extraction Layer ---")

  # Handle fallbacks for local CSV test representations vs actual Excel templates
  is_file = (
      IS_PATH
      if IS_PATH.exists()
      else Path("0.1.1 Income Statement (template).xlsx - Sheet1.csv")
  )
  bs_file = (
      BS_PATH
      if BS_PATH.exists()
      else Path("0.1.2 Balance Sheet (template).xlsx - Sheet1.csv")
  )
  cf_file = (
      CF_PATH
      if CF_PATH.exists()
      else Path("0.1.3 Cash Flow Statement(template).xlsx - Sheet1.csv")
  )

  master_data_layer = {
      "income_statement": parse_financial_sheet(is_file, "Income Statement"),
      "balance_sheet": parse_financial_sheet(bs_file, "Balance Sheet"),
      "cash_flow_statement": parse_financial_sheet(
          cf_file, "Cash Flow Statement"
      ),
  }

  # Export standardized extraction layer to JSON
  with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(master_data_layer, f, indent=4, ensure_ascii=False)

  print(
      f"Success! Standardized financial data layer successfully compiled and"
      f" saved to {OUTPUT_JSON_PATH}"
  )


if __name__ == "__main__":
  main()