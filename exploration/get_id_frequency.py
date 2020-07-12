#!/usr/bin/env python3

import argparse
import sys
import re

id_pattern= re.compile("[A-Z]+")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('infile')
    parser.add_argument('outfile')

    args = parser.parse_args(sys.argv[1:])

    with open(args.infile) as arff:
        ids = []
        for line in arff:
            try:
                id_ = id_pattern.match(line).group(0)
                ids.append(id_)
            except AttributeError:
                continue

    id_freq = {}
    for id_ in ids:
        if id_ in id_freq:
            id_freq[id_] += 1
        else:
            id_freq[id_] = 1

    with open(args.outfile, 'w+') as out:
        for id_, count in id_freq.items():
            out.write(f'{id_},{count}\n')

