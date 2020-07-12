#!/usr/bin/env python3
import argparse
import sys
import csv
import re
from itertools import takewhile, tee
from collections import namedtuple, defaultdict, Counter
from dataclasses import dataclass, field, astuple
from collections.abc import Iterable

def id_keep_strategy(pos_freq, neg_freq):
    """Determines strategy for ID records with multiple instances

    Two questions are answered:
    1. Should a single instance of the ID be kept at all?
    2. What class should a single record instance of the ID have?
    """
    if pos_freq == neg_freq:
        return None
    elif pos_freq > neg_freq:
        return 'Positive'
    elif neg_freq > pos_freq:
        return 'Negative'
    else:
        raise ValueError(f"{pos_freq} positives and {neg_freq} negatives makes no sense!")

def parse_arff(arff):
    """Parses arff file"""
    r_datatag = re.compile('^@data', flags=re.IGNORECASE)
    header = list(takewhile(lambda line: not r_datatag.match(line), arff))
    data = csv.reader(arff)

    return header, parse_data(header, data)

def parse_data(header, data):
    """Generates a namedtuple schema which goes to represent the records"""
    r_attrname = re.compile('^@attribute\s([\w.]+)\s.*', flags=re.IGNORECASE)
    attrnames = []
    for line in header:
        try:
            name = r_attrname.match(line).group(1)
        except AttributeError:
            continue
        name = name.replace('.', '_') # dots make fieldnames invalid
        attrnames.append(name)

    Record = namedtuple('Record', attrnames)
    data = (Record._make(record) for record in data)

    return data

@dataclass
class ValueOccurences:
    missing: int = 0
    present: int = 0
    value: str = '?'

@dataclass
class Analysis:
    total_freq: int = 0
    pos_freq: int = 0
    neg_freq: int = 0
    KF9_1: ValueOccurences = field(default_factory=ValueOccurences)
    BLOSUM2_1: ValueOccurences = field(default_factory=ValueOccurences)

def analyse_data(data):
    """Generates table that stores desired analysis of each ID instance(s)"""
    analysis_results = defaultdict(Analysis)
    for record in data:
        analysis = analysis_results[record.ID]
        analysis.total_freq += 1

        if record.Class == "Positive":
            analysis.pos_freq += 1
        elif record.Class == "Negative":
            analysis.neg_freq += 1
        else:
            print(f"An instance of {record.ID} has Class {record.Class}...?")

        for attr in ['KF9_1', 'BLOSUM2_1']:
            value = getattr(record, attr)
            occurences = getattr(analysis, attr)
            if value == '?':
                occurences.missing += 1
            else:
                if occurences.value != '?' and value != occurences.value:
                    print(f"{record.ID} instances have different {attr} values...?")
                occurences.present += 1
                occurences.value = value
    return analysis_results

def all_attrs_missing(record):
    """Checks if all attributes have missing values, excluding ID and Class"""
    return all(value == '?' for value in record[1:-1])

def reduce_data(outfile, data, analysis_results):
    """Reduces duplicates in the data using desired strategy"""
    writer = csv.writer(outfile, lineterminator='\n')

    dupe_decisions = {}
    for record in data:
        id_ = record.ID
        analysis = analysis_results[id_]

        if id_ in dupe_decisions.keys():
            continue
        elif analysis.total_freq == 1:
            writer.writerow(list(record))
        elif analysis.total_freq > 1:
            class_ = id_keep_strategy(analysis.pos_freq, analysis.neg_freq)
            if class_ is not None:
               reduced_record = record._replace(
                   Class = class_,
                   KF9_1 = analysis.KF9_1.value,
                   BLOSUM2_1 = analysis.BLOSUM2_1.value
               )
               writer.writerow(list(reduced_record))
            dupe_decisions[id_] = class_
        else:
            print(f"{id_} has a total frequency of {analysis.total_freq}...?")

    decision_counts = Counter(dupe_decisions.values())
    print(f"{decision_counts['Positive']} sets of ID duplicates reduced with Positive class\n"
          f"{decision_counts['Negative']} sets of ID duplicates reduced with Negative class\n"
          f"{decision_counts[None]} sets of ID duplicates completely removed")

def store_analysis(outfile, table):
    """Write out analysis table nicely"""
    writer = csv.writer(outfile, lineterminator='\n')
    writer.writerow([
        'total_freq',
        'pos_freq', 'neg_freq',
        'KF9.1_miss', 'KF9.1_present', 'KF9.1_value',
        'BLOSUM2.1_miss', 'BLOSUM2.1_present', 'BLOSUM2.1_value'
    ])
    for id_, analysis in table.items():
        writer.writerow([id_] + list(flatten(astuple(analysis))))

def flatten(t):
    """Generator flattening a nested structure

    Credit to:
    - https://gist.github.com/shaxbee/0ada767debf9eefbdb6e
    - https://gist.github.com/ma-ric/451ce328c4c84d18c8af
    """
    for x in t:
        if isinstance(x, str) or not isinstance(x, Iterable):
            yield x
        else:
            yield from flatten(x)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('arff_in')
    parser.add_argument('--analysis_out')
    parser.add_argument('--arff_out')
    args = parser.parse_args(sys.argv[1:])

    if not args.analysis_out and not args.arff_out:
        parser.error("No action requested")
        parser.print_usage()

    with open(args.arff_in) as arff_in:
        header, data = parse_arff(arff_in)
        data, data_ = tee(data)  # Duplicate for reducing step later
        analysis_results = analyse_data(data)

        if args.arff_out:
            data_ = (record for record in data_ if not all_attrs_missing(record))
            with open(args.arff_out, 'w') as arff_out:
                arff_out.writelines(header)
                arff_out.write('@data\n')
                reduce_data(arff_out, data_, analysis_results)

    if args.analysis_out:
        with open(args.analysis_out, 'w') as analysis_out:
            store_analysis(analysis_out, analysis_results)
