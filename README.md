# ism2411-data-cleaning-copilot

A small Python project that cleans a messy sales export into an analysis-ready
CSV. Built for ISM 2411 (Muma College of Business, University of South Florida)
with GitHub Copilot used to draft part of the code.

## What it does

`src/data_cleaning.py` reads `data/raw/sales_data_raw.csv` — a point-of-sale
export with inconsistent headers, padded text, blank cells, negative numbers and
a duplicated row — and writes a tidy `data/processed/sales_data_clean.csv`.

The cleaning steps, in order:

1. **Standardize column names** — lowercase, trimmed, underscore-separated, and
   the shorthand headers renamed (`ProdName ` → `product_name`, `qty` →
   `quantity`).
2. **Clean the text columns** — strip padding, collapse repeated inner spaces,
   apply title case, and restore acronyms like `USB`, so `"usb  cable "` and
   `"USB Cable"` stop being two different products.
3. **Parse dates** — `date_sold` becomes a real datetime; rows with an unknown
   date are kept, since the sale still happened.
4. **Handle missing values** — `price` and `quantity` are coerced to numbers and
   rows missing either one are dropped rather than filled, so no revenue is
   invented.
5. **Remove invalid rows** — any row with a price or quantity of zero or less is
   dropped (negative price, `0.00` placeholder price, negative or zero quantity),
   then exact duplicate records are removed and the index is reset.

On the provided dataset this takes **20 raw rows down to 11 clean rows**: 3
dropped for a missing price or quantity, 5 for impossible values, 1 duplicate.

## How to run

Requires Python 3 and pandas:

```bash
pip install pandas
```

From the project root:

```bash
python src/data_cleaning.py
```

The script prints a summary of each step and a preview of the result:

```
Loaded 20 rows and 5 columns from data/raw/sales_data_raw.csv
Standardized column names: ['product_name', 'category', 'price', 'quantity', 'date_sold']
Note: 1 row(s) have no sale date; keeping them.
Dropped 3 row(s) with a missing price or quantity
Removed 5 invalid row(s) and 1 duplicate row(s)
Cleaning complete. First few rows:
     product_name     category  price  quantity  date_sold
0       USB Cable  Electronics   7.99         3 2024-01-02
1  Wireless Mouse  Electronics  15.99         1 2024-01-04
2      Coffee Mug      Kitchen   5.49        10 2024-01-05
3        Notebook       Office   3.25        25 2024-01-06
4      Desk Chair       Office  89.99         1        NaT
```

## Project structure

```
ism2411-data-cleaning-copilot/
├── data/
│   ├── raw/
│   │   └── sales_data_raw.csv       # untouched source export
│   └── processed/
│       └── sales_data_clean.csv     # created by the script
├── src/
│   └── data_cleaning.py             # the cleaning pipeline
├── README.md
└── reflection.md                    # how Copilot was used
```

The raw file is never modified — all cleaning happens in code, so the pipeline
can be re-run and every decision can be traced in the comments.

## Copilot

Four functions (`load_data`, `clean_column_names`, `handle_missing_values` and
`remove_invalid_rows`) were drafted with GitHub Copilot from comment prompts and
then reworked. See [reflection.md](reflection.md) for what was generated, what
was changed, and why.
