# Reflection

## What Copilot generated

Four functions in `src/data_cleaning.py` started as Copilot suggestions:
`load_data`, `clean_column_names`, `handle_missing_values` and
`remove_invalid_rows`. I prompted it the same way every time — I wrote a comment
describing what the function should do, then the `def` line with a type hint,
then put the cursor on an indented blank line and waited for the ghost text. The
prompt comment I used is still sitting above each of those functions in the file.
Before accepting anything I cycled through the alternatives with `Option + ]`,
and that turned out to be worth doing for a reason I did not expect: the
alternatives are mostly not alternatives. For `load_data`, suggestion #2 was
nothing but a docstring restating my own comment back to me, and suggestion #3
was character-for-character identical to #1. For `clean_column_names` the toolbar
said `1/3`, and all three were the same code with a couple of words changed in
the inline comments. Three choices, one idea.

Where Copilot was genuinely good was syntax and local detail. It knew
`pd.to_numeric(..., errors="coerce")` and `dropna(subset=[...])` without me
looking anything up, it picked `na_values` out of the phrase "NA-looking cells"
in my comment, and in `clean_column_names` it added an explanatory comment to
every line of the method chain without being asked. In `handle_missing_values` it
even matched the `# WHAT:` / `# WHY:` comment style used elsewhere in the file —
though it did not do that in `clean_column_names`, where it also silently
dropped the `print` line that every other function in the file has. It reads the
surrounding file, but not consistently.

## What I modified

The change that taught me the most was in `load_data`. Copilot generated a plain
`pd.read_csv(file_path, na_values=["", "NA", "N/A"])`. I accepted it, ran the
script, and it worked — no error, and exactly 11 rows in the output, the same
count the corrected version produces. The damage was inside the data. Because
this export puts a space after every comma, the quote character is no longer the
first character of the field, so pandas treats it as ordinary text instead of
quoting. Every category came out as `"Electronics"` and `" Electronics"` with the
quote marks baked in, which made 7 distinct categories out of 5. The
`product_name` column escaped this because it is the first column, where the
quote does sit at the start of the field — same file, same data type, same
cleaning code, different result. `.str.strip()` could not repair it either, since
it only removes whitespace and the leading character here was `"`. Adding
`skipinitialspace=True` fixed all of it.

`clean_column_names` failed the opposite way. Copilot's chain of
`.str.strip().str.lower().str.replace(" ", "_")` was correct as far as it went,
but it stopped there — no `.rename()` turning `prodname` into `product_name` and
`qty` into `quantity`. My prompt comment only said "standardize", so that is
exactly what I got. The script crashed on the next function with
`KeyError: 'product_name'`. I also swapped the literal replace for
`.str.replace(r"\s+", "_", regex=True)`; on a header like `Order  Date` Copilot's
version produces `order__date` and the regex version produces `order_date`. This
dataset has no such header, so that weakness would never have shown up here. In
`handle_missing_values` the missing piece was two calls to my own helper
functions sitting directly above it in the same file. Without them the text
normalization never ran, and the cleaned file ended up with 11 distinct product
names across 11 rows — a sales table that looks like no product ever sold twice,
because `Desk Chair` and `Desk  Chair` were counted separately. Again, no error.
That same function also came with a confident WHY comment claiming "the raw
export has a few cells with text in them." I opened the raw CSV to check, and
there is no text in the price or quantity columns at all — only blank cells. The
code was right and the explanation of it was wrong, which is the kind of comment
someone would later trust.

I made one methodology mistake worth recording. For `handle_missing_values` and
my first pass at `remove_invalid_rows`, my prompt comments already contained the
answer — one said "drop the rows where either one is missing," the other said
"remove rows with negative **or zero** price or quantity, and reset the index."
Copilot produced `dropna` and `> 0` and I briefly took that as evidence it
understood the data. It was not; it was following instructions I had written.
I rewrote the prompt to a neutral "remove invalid rows and duplicates from the
sales data" and triggered it again, and the suggestion changed to
`df[(df["price"] >= 0) & (df["quantity"] >= 0)]` with no `reset_index` at all.
Left to its own reading of the word "invalid", Copilot means *negative*. It has
no way to know that the `0.00` price on the laptop stand is the placeholder this
system writes when a cashier skips the field rather than a free item, or that a
quantity of `0` is not a transaction. That knowledge only exists for someone who
has opened the raw file and looked. Dropping `reset_index` when I stopped asking
for it also confirmed a pattern from `clean_column_names`: whatever the prompt
leaves out, the code leaves out.

## What I learned

The single most useful thing I learned is that my instinct for how to verify a
cleaning script was wrong. Three of the four broken versions produced **exactly
11 rows**, with progress messages identical word for word to the correct run —
row count could not distinguish them at all. What exposed those was counting
distinct values per column: 7 categories instead of 5, 11 product names instead
of 9. Then the fourth one inverted it. The `>= 0` filter let two rows through and
the output jumped to 13 rows, so row count caught it immediately — but total
revenue came to `889.32` in **both** versions, because a row priced `0.00` and a
row with quantity `0` each multiply out to nothing. A revenue check would have
passed cleanly while the transaction count was off by two, which is enough to
report average order value as `$68.41` instead of `$80.85`, a 15% error sitting
behind a revenue total that reconciles perfectly. No single check caught
everything, and I could not have known in advance which check I needed, because
that depends on the bug.

On Copilot specifically: every suggestion it made was valid Python, and none of
the ones I had to fix were wrong about pandas. They were wrong about *this
dataset* — about what a space after a comma does to this particular export, about
what `0.00` means to whoever entered it, about which helper functions already
existed twenty lines up in the file. Its confidence is also flat: the invented
justification about "cells with text" is written in exactly the same steady tone
as the argument about revenue totals that was completely correct, so tone gives
me nothing to go on. What I would take into the next project is that the prompt
comment is doing more work than I realized — it is not a hint, it is the spec,
and Copilot will fill in nothing I forget to ask for and change its answer when
I change the wording. Reviewing what it wrote is not the last step of using it.
It is the whole job.
