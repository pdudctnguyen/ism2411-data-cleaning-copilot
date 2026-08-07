# Reflection

## What Copilot generated

Four of the functions in `src/data_cleaning.py` started as Copilot suggestions:
`load_data`, `clean_column_names`, `handle_missing_values` and
`remove_invalid_rows`. I prompted it the same way each time — I wrote the
comment describing what the function should do, then the `def` line with a type
hint, and let Copilot fill in the body. For example, typing
`# read a CSV into a DataFrame, treat blank/NA-looking cells as missing, and print how many rows and columns were loaded`
followed by `def load_data(file_path: str) -> pd.DataFrame:` produced a working
`pd.read_csv` call and a print statement on the first suggestion. The prompt
comments I used are still in the file above each of those functions, so it is
clear which parts of the code began as generated code. Copilot was strongest on
the mechanical parts: it knew `pd.to_numeric(..., errors="coerce")` and
`df.drop_duplicates()` without me having to look up the arguments, and it
suggested the `.str.strip().str.lower().str.replace(...)` chain for headers
almost exactly as I wanted it.

## What I modified

Very little of the generated code survived unchanged. In `load_data`, Copilot's
version was a plain `pd.read_csv(file_path)`. That silently broke on this file,
because the export writes a space after every comma, so quoted values loaded as
`' "USB Cable"'` with the padding baked in. I added `skipinitialspace=True` and
an explicit `na_values` list so that blank and whitespace-only cells register as
missing instead of as the string `" "`. In `clean_column_names` Copilot stopped
after lowercasing and replacing spaces; I added the `.rename()` step, because
`prodname` and `qty` are readable to the system that exported them and to nobody
else. The biggest change was in `handle_missing_values`: Copilot's first
suggestion filled missing prices with the column mean and missing quantities
with `0`. That is fine for a general dataset and wrong for this one — filling a
mean price invents revenue that never happened, and a quantity of 0 is not a
sale. I replaced the fill with `dropna(subset=["price", "quantity"])` and wrote
the reasoning into the comment. I also moved the numeric conversion ahead of the
missing-value check, since the values arrive as text and Copilot's version was
comparing strings.

In `remove_invalid_rows`, Copilot generated exactly what the prompt asked for:
`df[df["price"] >= 0]` and `df[df["quantity"] >= 0]`. That is a reasonable
reading of "remove negative values", but it left two bad rows in the data — the
laptop stand priced at `0.00`, which is the placeholder this system writes when
the cashier skips the field, and a notebook row with a quantity of `0`. I
tightened both filters to `> 0` and explained in the comment why zero is being
treated like a negative here. I also split the removal counts into invalid rows
versus duplicate rows in the print output, because during testing I could not
tell which filter was dropping what.

## What I learned

The main lesson about data cleaning is that the order of operations matters as
much as the operations themselves. My first working version removed duplicates
before normalizing the text, and it caught nothing: `"Pen Set"` and `"Pen Set "`
are different strings, so `drop_duplicates()` saw two distinct rows. Once the
whitespace stripping and title casing ran first, the same call found the
duplicate immediately. The same ordering problem showed up with the numeric
columns — `" -1 "` is not less than zero, it is text, and the negative-quantity
filter did nothing until `pd.to_numeric` ran ahead of it. Neither bug threw an
error; the script ran fine and quietly produced dirty output, which is why I
added a print line to every step so I could see the row counts change.

About Copilot: it is fast and accurate on syntax and genuinely good at
remembering pandas arguments I would otherwise have to search for, but it has no
idea what my data actually contains. It cannot know that `0.00` is a placeholder
rather than a free item, or that filling missing prices with the mean would
misstate sales. Every one of its suggestions was plausible Python; the ones I
had to change were wrong about *this dataset*, not about pandas. The concrete
example I keep coming back to is the mean-fill suggestion — it would have run
without complaint, produced a clean-looking CSV, and added revenue that does not
exist. That is the failure mode worth watching for: the tool is confident in
exactly the same tone whether it is right or wrong, so the judgment about what
the data means still has to come from me.
