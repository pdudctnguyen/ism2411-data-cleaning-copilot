# Reflection

## What Copilot generated

Four of the functions in `src/data_cleaning.py` started as Copilot suggestions:
`load_data`, `clean_column_names`, `handle_missing_values` and
`remove_invalid_rows`. I used the same method for all four. I wrote a comment
saying what the function should do, then the `def` line with a type hint, then
put my cursor on an indented blank line and waited for the gray text to appear.
The comment I used is still in the file above each function so you can see what I
asked for. Before hitting Tab I pressed `Option + ]` to look at the other
suggestions, and that was the first thing that surprised me. Most of the time
they were not really different. For `load_data`, the second suggestion was just a
docstring repeating my own comment back at me with no code at all, and the third
one was exactly the same as the first. For `clean_column_names`, all three
suggestions were the same code with only a few words changed in the comments.
Copilot was good at the parts I would have had to look up. It knew
`pd.to_numeric(..., errors="coerce")` and `dropna(subset=[...])` right away, and
it noticed the words "NA-looking cells" in my comment and added a `na_values`
argument because of it. In `clean_column_names` it put a short comment on every
line of the chain without me asking. In `handle_missing_values` it even copied
the `# WHAT:` / `# WHY:` comment style I was using in the rest of the file. It
did not do that in `clean_column_names` though, and there it also left out the
`print` line that every other function in my file has, so I am not sure how much
it really looks at the rest of the file.

## What I modified

The change I learned the most from was in `load_data`. Copilot wrote
`pd.read_csv(file_path, na_values=["", "NA", "N/A"])`. I accepted it and ran the
script and nothing went wrong. No error, and a preview that looked normal at a
glance. The only reason I looked closer is that the category column in that
preview still had quote marks around every value. This CSV has a space after
every comma, so the quote mark is not the first character of the field anymore
and pandas stops treating it as a quote. Every category came out looking like
`"Electronics"` and `" Electronics"` with the quote marks still attached, so
counting them gave me 7 categories when the raw file only has 5. What confused me
for a while is that `product_name` was totally fine. It turns out that column is
first in the row, so its quote really is at the start and pandas handles it the
normal way. The same code gave me a different result just because of where the
column sits. I also assumed `.str.strip()` would clean it up later, but strip
only removes spaces and the first character here was a quote mark. Adding
`skipinitialspace=True` fixed it.

`clean_column_names` broke in the opposite way. The chain Copilot wrote,
`.str.strip().str.lower().str.replace(" ", "_")`, was fine, but it stopped there
and never renamed `prodname` to `product_name` or `qty` to `quantity`. My comment
only said "standardize", so that is all I got, and the script crashed on the next
function with `KeyError: 'product_name'`. I also changed the replace to
`.str.replace(r"\s+", "_", regex=True)`. I tested both on a made-up header
`Order  Date` with two spaces: Copilot's version gives `order__date` with two
underscores and the regex version gives `order_date`. My file does not have a
header like that, so I never would have seen this by just running the script.
For `handle_missing_values`, what was missing was two calls to my own helper
functions that are written right above it in the same file. Without them the text
cleaning never ran, and my "clean" file ended up with 11 different product names
in 11 rows, because `Desk Chair` and `Desk  Chair` were counted as two products.
It looked like nothing in the store had ever sold twice. There was no error
message. That same function also came with a comment saying "the raw export has a
few cells with text in them," so I opened the raw CSV to check and there is no
text in the price or quantity columns at all, only empty cells. The code was
right but the reason it gave was made up.

I also made a mistake in how I was testing this, and I think it is worth writing
down. For `handle_missing_values` and my first try at `remove_invalid_rows`, my
prompt comments already gave away the answer. One of them said "drop the rows
where either one is missing" and the other said "remove rows with negative or
zero price or quantity, and reset the index." Copilot gave me `dropna` and `> 0`
and for a minute I thought that meant it understood my data. It did not. It was
just doing what I told it. So I rewrote the comment to something neutral,
"remove invalid rows and duplicates from the sales data," and triggered it again.
This time it wrote `df[(df["price"] >= 0) & (df["quantity"] >= 0)]` and dropped
`reset_index` completely. So when Copilot decides for itself what "invalid"
means, it means negative. It has no way of knowing that the `0.00` price on the
laptop stand is what the system puts there when the cashier skips the field, or
that selling 0 of something is not a sale. You only know that if you open the raw
file and look at it. Losing `reset_index` as soon as I stopped asking for it was
the same thing that happened in `clean_column_names`. If I leave something out of
the comment, it gets left out of the code.

## What I learned

The biggest thing I learned is that I was checking my work the wrong way. My
whole idea of "did that work" was to look at the row count and the messages
printed to the terminal. Three of the four bugs above changed neither one. The
script said 11 rows before I fixed it and 11 rows after, with the same progress
messages word for word, so I could have signed off on any of them. What actually
caught them was counting how many different values ended up in each column and
comparing that against the raw CSV: 7 categories when the file only has 5, and 11
different product names in 11 rows when several of those products clearly show up
more than once. Then the fourth bug went the other way. The `>= 0` filter let two
rows through and the output jumped to 13 rows, so this time the row count caught
it right away. But the revenue total came to `889.32` before the fix and `889.32`
after it, because a row priced `0.00` and a row with quantity `0` both multiply
out to nothing. A revenue check would have looked perfect while there were two
fake transactions sitting in the file. If someone used it to work out average
order value they would get `$68.41` instead of `$80.85`, and the revenue total
would still add up exactly. Every check I tried caught some things and missed
others, and I had no way of knowing in advance which one I was going to need.
The other thing I learned is that none of the mistakes I had to fix were mistakes
about pandas. Everything Copilot wrote was valid Python. The errors were all
about my data: what a space after a comma does to this particular file, what
`0.00` means here, which helper functions I had already written twenty lines up.
It also sounds equally sure of itself either way, since the made-up explanation
about "cells with text" is written in the same calm tone as the comment about
revenue totals that was completely correct, so I cannot go by how confident it
sounds. And the comment I write above the function matters more than I expected.
It is closer to a set of instructions than a hint, and Copilot will not add
anything I forget to put in it. Getting code out of Copilot was the fast part of
this assignment. Checking it took most of the time.
