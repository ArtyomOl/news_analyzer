#!/usr/bin/env python3
"""Utility to detect MOEX.csv format and produce a cleaned UTF-8 CSV.

Heuristics:
- detect encoding (try utf-8 then cp1251)
- detect delimiter among common candidates by choosing the one with most consistent field counts
- determine expected field count as most common count in sample
- when a row has more fields than expected, join extras into the last field
- when fewer, pad with empty strings
"""
from pathlib import Path
import csv
from collections import Counter
import argparse


def detect_encoding(path: Path) -> str:
    b = path.open('rb').read(8192)
    try:
        b.decode('utf-8')
        return 'utf-8'
    except UnicodeDecodeError:
        return 'cp1251'


def detect_delimiter(path: Path, encoding: str) -> str:
    sample = path.read_bytes()[:32768].decode(encoding, errors='replace')
    candidates = [',', ';', '\t', '|']
    best = None
    best_score = -1.0
    for d in candidates:
        counts = [len(line.split(d)) for line in sample.splitlines() if line.strip()]
        if not counts:
            continue
        most_common_freq = Counter(counts).most_common(1)[0][1]
        score = most_common_freq / len(counts)
        if score > best_score:
            best_score = score
            best = d
    return best or ','


def clean(input_path: Path, output_path: Path, encoding: str | None = None, delimiter: str | None = None) -> None:
    if encoding is None:
        encoding = detect_encoding(input_path)
    if delimiter is None:
        delimiter = detect_delimiter(input_path, encoding)

    print(f"Detected encoding={encoding}, delimiter={repr(delimiter)}")

    # sample field count
    sample_text = input_path.read_text(encoding=encoding, errors='replace')[:65536]
    counts = Counter(len(line.split(delimiter)) for line in sample_text.splitlines() if line.strip())
    print('Field counts sample:', counts)
    expected = counts.most_common(1)[0][0] if counts else None
    if expected is None:
        raise SystemExit('Unable to determine expected field count')

    total = 0
    fixed = 0
    with input_path.open('r', encoding=encoding, errors='replace', newline='') as fin, \
         output_path.open('w', encoding='utf-8', newline='') as fout:
        reader = csv.reader(fin, delimiter=delimiter)
        writer = csv.writer(fout, delimiter=delimiter, quoting=csv.QUOTE_MINIMAL)
        for row in reader:
            total += 1
            if len(row) == expected:
                writer.writerow(row)
            elif len(row) > expected:
                new = row[: expected - 1] + [delimiter.join(row[expected - 1 :])]
                writer.writerow(new)
                fixed += 1
            else:
                new = row + [''] * (expected - len(row))
                writer.writerow(new)
                fixed += 1

    print(f'Wrote cleaned file: {output_path} (total={total}, fixed={fixed})')


def main() -> None:
    p = argparse.ArgumentParser(description='Clean MOEX CSV by detecting delimiter/encoding')
    p.add_argument('input', help='path to input CSV (MOEX.csv)')
    p.add_argument('-o', '--output', help='path to cleaned output CSV', default='MOEX.cleaned.csv')
    args = p.parse_args()
    inp = Path(args.input)
    out = Path(args.output)
    clean(inp, out)


if __name__ == '__main__':
    main()
