"""
data_cleaning.py
----------------
Purpose: Turn the messy raw sales export (data/raw/sales_data_raw.csv) into a
tidy, analysis-ready file (data/processed/sales_data_clean.csv).

The raw export came out of a point-of-sale system and has the usual problems:
inconsistent column headers, padded whitespace inside quoted text, blank price
and quantity cells, negative numbers where negatives make no sense, and rows
that were entered twice. Every fix below happens in code so the raw file stays
untouched and the whole cleanup can be re-run and audited.

Run from the project root:
    python src/data_cleaning.py
"""

import pandas as pd

# Acronyms that title case would otherwise flatten into "Usb", "Hdmi", etc.
# Kept as a named constant so the list is easy to extend as the catalog grows.
ACRONYMS = ["USB", "HDMI", "LED", "SSD", "TV"]


# Copilot-assisted function.
# Prompt comment used: "read a CSV into a DataFrame, treat blank/NA-looking
# cells as missing, and print how many rows and columns were loaded"
def load_data(file_path: str) -> pd.DataFrame:
    """Load the raw CSV into a DataFrame and report its shape."""
    # skipinitialspace=True is needed because this export writes ', "USB Cable"'
    # with a space after every comma, which otherwise leaves the quote marks
    # inside the value and makes "Electronics" and " Electronics" two categories.
    df = pd.read_csv(file_path,skipinitialspace=True,na_values=["", " ", "NA", "N/A", "null"])

    print(f"Loaded {len(df)} rows and {len(df.columns)} columns from {file_path}")
    return df


# Copilot-assisted function.
# Prompt comment used: "standardize dataframe column names to lowercase with
# underscores and no surrounding whitespace"
def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Make column names lowercase, underscore-separated, and whitespace-free."""
    df = df.copy()

    # WHAT: lowercase every header, trim the padding, and collapse any run of
    # whitespace into a single underscore.
    # WHY: the raw headers are "ProdName ", " CATEGORY ", "   date_sold ", so
    # column access is unpredictable until they all follow one convention.
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(r"\s+", "_", regex=True)
    )

    # WHAT: give the abbreviated columns full names.
    # WHY: "prodname" and "qty" are shorthand only the exporting system
    # understands, and every later step in this script refers to the full names.
    df = df.rename(columns={"prodname": "product_name", "qty": "quantity"})

    print(f"Standardized column names: {list(df.columns)}")
    return df


def clean_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Trim and normalize the free-text product and category columns."""
    df = df.copy()

    for column in ["product_name", "category"]:
        # WHAT: strip the padding, squeeze repeated inner spaces down to one,
        # and apply title case.
        # WHY: the raw file holds "USB Cable", "usb cable", " electronics ", and
        # "Laptop  Stand" as separate values. They are the same product and the
        # same category, so without this step every later grouping or duplicate
        # check counts them twice.
        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
            .str.replace(r"\s+", " ", regex=True)
            .str.title()
        )

        # WHAT: put product acronyms back in uppercase after title casing.
        # WHY: .str.title() turns "USB Cable" into "Usb Cable". Title case is
        # still the right default for the rest of the catalog, so the acronyms
        # get restored instead of dropping the rule entirely.
        for acronym in ACRONYMS:
            df[column] = df[column].str.replace(
                rf"\b{acronym.title()}\b", acronym, regex=True
            )

    return df


def clean_date_column(df: pd.DataFrame) -> pd.DataFrame:
    """Parse date_sold into real dates instead of padded strings."""
    df = df.copy()

    # WHAT: convert date_sold to datetime; anything unparseable becomes NaT.
    # WHY: the column arrives as text with stray spaces and one blank cell, so
    # sorting or filtering by date would be alphabetical rather than
    # chronological. Rows with a missing date are kept — the sale itself is
    # still valid, only the timestamp is unknown.
    df["date_sold"] = pd.to_datetime(df["date_sold"].astype("string").str.strip(),
                                     errors="coerce")

    missing_dates = int(df["date_sold"].isna().sum())
    if missing_dates:
        print(f"Note: {missing_dates} row(s) have no sale date; keeping them.")

    return df


# Copilot-assisted function.
# Prompt comment used: "convert price and quantity to numeric and drop the rows
# where either one is missing, printing how many rows were removed"
def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with missing price or quantity, and report how many."""
    df = df.copy()
        # WHAT: run the text and date cleanup before anything else.
    # WHY: those steps normalize product_name and category and parse date_sold.
    # Skipping them leaves "Desk Chair" and "Desk  Chair" as two products.
    df = clean_text_columns(df)
    df = clean_date_column(df)

    rows_before = len(df)

    # WHAT: convert price and quantity to numeric, coercing errors to NaN.
    # WHY: the blank cells and the spaces around every value make pandas read
    # both columns as text. Comparing " -1 " to zero would never flag the bad
    # row; comparing -1 does.
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")

    # WHAT: drop any row where price or quantity is NaN.
    # WHY: a sale with no price or no quantity is not a real sale, so it should
    # not be counted in revenue totals.
    df = df.dropna(subset=["price", "quantity"])
    missing_removed = rows_before - len(df)

    # WHAT: store quantity as a whole number.
    # WHY: units sold are countable; "3.0 units" is noise in the output file.
    df["quantity"] = df["quantity"].astype(int)

    print(f"Removed {missing_removed} row(s) with missing price or quantity")
    return df




# Copilot-assisted function.
# Prompt comment used: "remove invalid rows and duplicates from the sales data"
def remove_invalid_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with a non-positive price or quantity, and remove duplicates."""
    df = df.copy()
    rows_before = len(df)

    # WHAT: keep only rows where price and quantity are greater than zero.
    # WHY: negative values are clearly data entry errors, but zero has to go
    # too. The 0.00 price on the laptop stand is the placeholder this system
    # writes when the cashier skips the field, not a free item, and a quantity
    # of 0 is not a transaction. Both would survive a >= 0 filter.
    df = df[(df["price"] > 0) & (df["quantity"] > 0)]
    invalid_removed = rows_before - len(df)

    # WHAT: drop duplicate rows based on all columns, then renumber.
    # WHY: the raw export has some rows entered twice. Keeping them would
    # double-count the revenue for those sales. Resetting the index afterwards
    # stops the surviving rows from looking like data is missing.
    df = df.drop_duplicates().reset_index(drop=True)
    duplicates_removed = rows_before - invalid_removed - len(df)


    print(f"Removed {invalid_removed} invalid row(s) and {duplicates_removed} duplicate(s)")
    return df 


if __name__ == "__main__":
    raw_path = "data/raw/sales_data_raw.csv"
    cleaned_path = "data/processed/sales_data_clean.csv"

    df_raw = load_data(raw_path)
    df_clean = clean_column_names(df_raw)
    df_clean = handle_missing_values(df_clean)
    df_clean = remove_invalid_rows(df_clean)
    df_clean.to_csv(cleaned_path, index=False)
    print("Cleaning complete. First few rows:")
    print(df_clean.head())
