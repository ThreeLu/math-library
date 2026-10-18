import random
import networkx as nx

def is_tour(tour, arcs, directed):
    used = list(zip(tour, tour[1:]))
    if tour[0] != tour[-1]: return False
    if directed: return sorted(used) == sorted(arcs)
    return sorted(tuple(sorted(e)) for e in used) == sorted(tuple(sorted(e)) for e in arcs)

def check(ns):
    adj = [[1],[2,3],[0,1],[4],[2]]
    assert ns["euler_tour_linked"](adj, 0) == [0,1,3,4,2,1,2,0]
    assert ns["euler_tour_stack"](adj, 0) == [0,1,2,1,3,4,2,0]
    assert ns["euler_tour_linked"](adj, 1) == [1,2,0,1,3,4,2,1]
    B = [(0,1),(1,2),(2,0),(2,3),(3,4),(4,2)]
    assert ns["euler_tour_undirected"](5, B, 0) == [0,1,2,3,4,2,0]
    assert ns["de_bruijn"](3) == [0,1,0,1,1,1,0,0]
    for k in range(1, 7):
        seq = ns["de_bruijn"](k); L = len(seq); assert L == 2 ** k
        subs = {tuple(seq[(i + j) % L] for j in range(k)) for i in range(L)}
        assert len(subs) == 2 ** k
    for _ in range(300):
        n = random.randint(2, 8)
        # random Eulerian digraph: union of random cycles on a connected support
        arcs = []
        for _ in range(random.randint(1, 4)):
            c = random.sample(range(n), random.randint(2, n))
            arcs += [(c[i], c[(i + 1) % len(c)]) for i in range(len(c))]
        D = nx.MultiDiGraph(); D.add_edges_from(arcs)
        if not nx.is_strongly_connected(D): continue
        adj = [[] for _ in range(n)]
        for u, v in arcs: adj[u].append(v)
        s = arcs[0][0]
        for f in (ns["euler_tour_linked"], ns["euler_tour_stack"]):
            t = f(adj, s); assert is_tour(t, arcs, True), (arcs, t)
        und = [(u, v) for u, v in arcs]   # undirected multigraph from cycles: even degrees
        t = ns["euler_tour_undirected"](n, und, s); assert is_tour(t, und, False)
        # trail: remove one edge
        tr_edges = und[1:]
        G = nx.MultiGraph(); G.add_edges_from(tr_edges)
        if tr_edges and nx.is_connected(G):
            t = ns["euler_trail_undirected"](n, tr_edges)
            used = list(zip(t, t[1:]))
            assert sorted(tuple(sorted(e)) for e in used) == sorted(tuple(sorted(e)) for e in tr_edges)
    # non-Eulerian detection in linked version
    assert ns["euler_tour_linked"]([[1],[2],[]], 0) is None
    assert ns["euler_tour_linked"]([[1],[0],[3],[2]], 0) is None
