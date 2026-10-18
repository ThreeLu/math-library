import random

def check(ns):
    A = ns["adjacency_matrix"](5, ns["G_edges"])
    assert A == [[0,1,1,1,0],[1,0,1,0,1],[1,1,0,1,1],[1,0,1,0,1],[0,1,1,1,0]]
    assert ns["adjacency_matrix"](4, ns["D_arcs"], True) == [[0,1,1,0],[1,0,1,1],[0,1,0,0],[0,0,1,0]]
    INF = ns["INF"]
    assert ns["weighted_matrix"](5, ns["N_edges"])[0] == [INF, 1, 2, INF, INF]
    assert ns["adjacency_list"](5, ns["G_edges"]) == [[1,2,3],[0,2,4],[0,1,3,4],[0,2,4],[1,2,3]]
    head, data, nxt = ns["linked_adjacency"](4, ns["D_arcs"])
    assert (head, data, nxt) == ([1,4,5,6], [1,2,0,2,3,1,2], [-1,0,-1,2,3,-1,-1])
    assert ns["neighbours_linked"](head, data, nxt, 1) == [3, 2, 0]
    V, E = ns["csr"](5, ns["G_edges"])
    assert V == [0,3,6,10,13,16] and E == [1,2,3,0,2,4,0,1,3,4,0,2,4,1,2,3]
    assert ns["reverse_adjacency"](4, ns["D_arcs"]) == [[1],[0,2],[0,1,3],[1]]
    L = ns["orthogonal_list"](4, ns["O_arcs"])
    assert L[0] == [1,-1,3,6] and L[1] == [4,5,6,3]
    assert L[5] == [-1,0,-1,2,-1,4,5] and L[6] == [-1,-1,-1,-1,2,0,1]
    assert ns["out_arcs"](L, 3) == [(2,9),(1,6),(0,5)] and ns["in_arcs"](L, 0) == [(3,5),(2,6)]
    M = ns["multilist"](5, ns["N_edges"])
    assert M[0] == [1,4,6,7,7] and M[4] == [-1,0,0,2,3,2,5,5] and M[5] == [-1,-1,1,-1,-1,3,4,6]
    assert ns["edges_at"](M, 2) == [6,5,2,1]
    B = ns["incidence_matrix"](5, ns["G_edges"])
    assert B[2] == [0,1,0,1,0,1,1,0]
    # exercises, on random graphs
    for _ in range(50):
        n = random.randint(1, 8)
        arcs = list({(random.randrange(n), random.randrange(n)) for _ in range(12)})
        arcs = [(u, v) for u, v in arcs if u != v]
        adj = ns["adjacency_list"](n, arcs, True)
        assert ns["matrix_to_list"](ns["list_to_matrix"](adj)) == [sorted(a) for a in adj]
        assert ns["reverse_of"](adj) == ns["reverse_adjacency"](n, arcs) or \
            [sorted(x) for x in ns["reverse_of"](adj)] == [sorted(x) for x in ns["reverse_adjacency"](n, arcs)]
        und = list({tuple(sorted(e)) for e in arcs})
        V, E = ns["csr"](n, und); ns["sort_csr"](V, E)
        S = {frozenset(e) for e in und}
        for u in range(n):
            for v in range(n):
                assert ns["adjacent_csr"](V, E, u, v) == (frozenset((u, v)) in S and u != v)
