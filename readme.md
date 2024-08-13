## Purpose

Determine the lifetime for labels to be shown on a vario-scale web map


## Install

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install git+https://github.com/bmmeijers/predicates#egg=geompreds
python3 -m pip install git+https://github.com/bmmeijers/tri#egg=tri
```


## Run

Prepare `input/labels.csv`, with per line:

```
name            city name
x, y            coordinates of the anchor point
inhabitant_ct   number of inhabitants (determines priority of labels)
```

Note, to obtain an anchor point inside polygons, the [QGIS processing tool: Pole of inaccessibility](https://docs.qgis.org/latest/en/docs/user_manual/processing_algs/qgis/vectorgeometry.html#pole-of-inaccessibility) can be used.

Then run:

```bash
source venv/bin/activate
python3 lifetime.py
python3 labels_as_json.py 
```

The `output` folder now contains:
- `ordered_labels.wkt` and 
- `ordered_labels.json`

The `.wkt` file can be read in QGIS by `Add Delimited Text Layer`.
The `.json` file can be used in sscview.