import json
import csv
import os


def main():
    cities = []
    with open(os.path.join(os.path.dirname(__file__), "output/ordered_labels.wkt")) as fh:
        reader = csv.reader(fh, delimiter="\t")
        for i, line in enumerate(reader):
            if i == 0:
                continue
            cities.append(
                {
                    "x": float(line[0]),
                    "y": float(line[1]),
                    "label": line[2],
                    "inhabitants": int(line[3]),
                    "maxDenominator": int(float(line[5])),
                }
            )

    with open(os.path.join(os.path.dirname(__file__), "output/ordered_labels.json"), 'w') as fh:
        print(json.dumps(cities, indent=2), file=fh)


if __name__ == "__main__":
    main()