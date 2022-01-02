import os

with open("vnames.txt", "r") as f:
    lines = f.readlines()
    lines = [line.strip() for line in lines]

for index, i in enumerate(range(0, len(lines), 4950)):
    sep = lines[i: i + 4950]
    with open(f"vnames_part{index + 1}.txt", "w") as f:
        for line in sep:
            f.write(line + "\n")