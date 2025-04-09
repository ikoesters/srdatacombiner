# %%
# Repair scope data that has been incorrectly formatted due to an error in Kollmorgen Workbench.
# The error is that field and decimal separators are both commas. Due to decimal places sometimes being omitted if they are zero,
# data gets misaligned in the csv file as well.
# Data before repair: 0,25,78,592,72,2,422,432,23,279,0,
# Data after repair: 0,25;78,592;72,2;422,432;23,279;0,0 (german locale: sep=";", decimal=",")

import csv
import pandas as pd
from pathlib import Path

parentfolder = "data/strikes_ATS_260724/1ms"


# %%
def repair_scope_data(file: str | Path) -> list:
    with open(file, "r", encoding="utf-8-sig") as infile:
        reader = csv.reader(infile)
        header = next(reader)[:6]
        proc_rows = [header]
        for row_nb, row in enumerate(reader):
            row = row[:13]
            if row_nb % 4 == 0:  # indices where time has no decimal values
                time = float(row.pop(0))
            else:
                time = float(f"{row.pop(0)}.{row.pop(0)}")
            if len([val for val in row if val]) != 9:  # remove empty values
                continue
            other_vals = [
                float(f"{row[i]}.{row[i+1]}")
                for i in range(0, len(row), 2)
                if row[i] != ""
            ]
            proc_rows.append([time] + other_vals)
    return pd.DataFrame(proc_rows[1:], columns=proc_rows[0])


def save_repaired_scope_data(filepath: str | Path, repaired_data: pd.DataFrame) -> None:
    repaired_data.to_csv(filepath, index=False, sep=";", decimal=",")


def find_all_files(directory: str | Path, glob_pattern: str) -> list[Path]:
    path = Path(directory) if isinstance(directory, str) else directory
    files = [p for p in path.rglob(glob_pattern)]
    sorted_files = sorted(files)
    return sorted_files


def find_repair_and_save_scope_data(directory: str | Path, glob_pattern: str) -> None:
    scope_files = find_all_files(directory, glob_pattern)
    for file in scope_files:
        repaired_data = repair_scope_data(file)
        file.rename(file.parent / ("faultyformat_" + file.stem + file.suffix))
        save_repaired_scope_data(
            filepath=file.parent / (file.stem + "_formatcorrected" + file.suffix),
            repaired_data=repaired_data,
        )


# %%
find_repair_and_save_scope_data(parentfolder, "[0-9][0-9][0-9][0-9]*csv")

# %%
