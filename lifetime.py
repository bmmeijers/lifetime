from pprint import pprint
from math import hypot
import time
import os
import pqdict
from geompreds import incircle
from tri.delaunay.insert_kd import (
    kdsort,
    decorate,
    translate_new2old,
    ccw,
    Triangulation,
    KDOrderPointInserter,
)
from tri.delaunay.iter import StarEdgeIterator
from tri.delaunay.inout import output_triangles, output_vertices


def dist(va, vb):
    dx = va[0] - vb[0]
    dy = va[1] - vb[1]
    return hypot(dx, dy)


def is_valid_circumcircle(dt):
    """check empty circumcircle."""
    for t in dt.triangles:
        for v in dt.vertices:
            if v not in t.vertices:
                try:
                    result = incircle(t.vertices[0], t.vertices[1], t.vertices[2], v)
                    assert result < 0
                except AssertionError:
                    print(result)
                    print(t)
                    print(v)
                    raise (
                        "Found non-Delaunay triangle (its circumcircle is not empty)"
                    )


def is_valid_references(dt):
    """check that all internal references used are in-use."""
    for t in dt.triangles:
        for n in t.neighbours:
            if n is not None:
                assert n in dt.triangles
        for v in t.vertices:
            if v.is_finite:
                assert v in dt.vertices
    for v in dt.vertices:
        assert v.triangle in dt.triangles


def main():
    with open(os.path.join(os.path.dirname(__file__), "input/labels.csv"), "r") as fh:
        lines = fh.readlines()[1:]
        lines = [line.split("\t") for line in lines]
        lines = [
            [(float(line[1]), float(line[2])), (line[0].strip(), int(line[3]))]
            for line in lines
        ]
        pprint(lines)

    pts = [tup[0] for tup in lines]
    infos = [tup[1] for tup in lines]

    before = list(zip(pts, infos))

    start = time.perf_counter()
    pts = kdsort(decorate(pts))
    new2old_index = translate_new2old(pts)
    end = time.perf_counter()
    print("Sorting points: " + str(end - start) + " secs")

    start = time.perf_counter()
    dt = Triangulation()
    incremental = KDOrderPointInserter(dt)
    incremental.insert(pts)
    end = time.perf_counter()

    print("Triangulating took: " + str(end - start) + " secs")
    print("{} triangles".format(len(dt.triangles)))
    print("{} vertices".format(len(dt.vertices)))
    print("{} flips".format(incremental.flips))
    print("{} visits".format(incremental.visits))
    if len(dt.vertices) > 0:
        print(str(float(incremental.flips) / len(dt.vertices)) + " flips per insert")

    # insert the info (the number of inhabitants) into the vertices
    for new_idx, v in enumerate(dt.vertices, start=0):
        # translate index (after kD-sort)
        old_idx = new2old_index[new_idx]
        v.info = infos[old_idx]

    # check for maintaining info correctly
    after = [((v.x, v.y), v.info) for v in dt.vertices]
    before.sort()
    after.sort()
    assert before == after

    # print("output written to /tmp")
    with open(
        os.path.join(os.path.dirname(__file__), "output/tri__all_tris.wkt"), "w"
    ) as fh:
        output_triangles(dt.triangles, fh)
    with open(
        os.path.join(os.path.dirname(__file__), "output/tri__all_vertices.wkt"), "w"
    ) as fh:
        output_vertices(dt.vertices, fh)

    is_valid_circumcircle(dt)
    # is_valid_references(dt)
    # input("PAUSE")

    # create the priority queue
    # ordered by smallest distance of the distance to other labels
    oseq = pqdict.PQDict()
    for v in dt.vertices:
        dists = [
            dist(
                edge.triangle.vertices[edge.side],
                edge.triangle.vertices[ccw(edge.side)],
            )
            for edge in StarEdgeIterator(v)
        ]
        print((v.x, v.y), min(dists))
        oseq[(v.x, v.y)] = min(dists)

    # determine the order in which labels will be removed
    order = []
    while len(oseq) > 1:
        # walk to the label point
        pivot, D = oseq.popitem()
        tri = incremental.visibility_walk(dt.triangles[0], pivot)
        for v in tri.vertices:
            if v[0] == pivot[0] and v[1] == pivot[1]:
                break
        else:
            raise ValueError("point not found")

        print("***", pivot, D, "***", v, v.info)
        neighbours = [
            (
                dist(
                    edge.triangle.vertices[edge.side],
                    edge.triangle.vertices[ccw(edge.side)],
                ),
                edge.triangle.vertices[ccw(edge.side)],
            )
            for edge in StarEdgeIterator(v)
        ]
        neighbours.sort()
        for distance, neighbour in neighbours:
            print(" " * 3, distance, neighbour, neighbour.info)

        distance, neighbour = neighbours[0]
        print(neighbour, neighbour.info)

        # decide which of the two end points of the edge needs to be removed
        to_remove = None
        if v.info[1] < neighbour.info[1]:
            to_remove = v  # was already popped
            to_update = neighbour
            to_pop = to_update
        else:
            to_remove = neighbour
            to_update = v  # was already popped
            to_pop = to_remove

        order.append([(to_remove.x, to_remove.y), to_remove.info, int(D)])

        # remove from PQ
        oseq.pop((to_pop.x, to_pop.y))
        print("removal:  ", to_remove, to_remove.info)
        print("updating: ", to_update, to_update.info)

        # remove from DT
        neighbours = []
        for edge in StarEdgeIterator(to_remove):
            ngb_vertex = edge.triangle.vertices[ccw(edge.side)]
            if ngb_vertex.is_finite:
                neighbours.append(ngb_vertex)
        incremental.remove(to_remove, dt.triangles[0])

        # update the labels that stay (set their next dist)
        for ngb in neighbours:
            dists = [
                dist(
                    edge.triangle.vertices[edge.side],
                    edge.triangle.vertices[ccw(edge.side)],
                )
                for edge in StarEdgeIterator(ngb)
            ]
            edge = None
            oseq[(ngb.x, ngb.y)] = min(dists)

    pivot, D = oseq.popitem()
    tri = incremental.visibility_walk(dt.triangles[0], pivot)
    for v in tri.vertices:
        if v[0] == pivot[0] and v[1] == pivot[1]:
            break
    order.append([(v.x, v.y), v.info, int(D)])

    pprint(order)

    with open(
        os.path.join(os.path.dirname(__file__), "output/ordered_labels.wkt"), "w"
    ) as fh:
        fh.write(
            "\t".join(
                ["x", "y", "placename", "inhabitants", "sep_dist_m", "max_denominator"]
            )
        )
        fh.write("\n")
        for (x, y), (placename, inhabitants), dist_meter in order:
            fh.write(
                "\t".join(
                    map(
                        str,
                        [
                            x,
                            y,
                            placename,
                            inhabitants,
                            dist_meter,
                            dist_meter / 3.0 * 100.0,
                        ],
                    )
                )
            )
            fh.write("\n")


if __name__ == "__main__":
    main()
