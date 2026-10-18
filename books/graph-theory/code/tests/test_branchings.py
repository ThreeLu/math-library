import itertools, random
import networkx as nx

def brute(n, arcs, need=None):
    best = None
    for r in range(len(arcs) + 1):
        for S in itertools.combinations(arcs, r):
            if need is not None and r != need: continue
            D = nx.DiGraph(); D.add_nodes_from(range(n)); D.add_edges_from((a[0], a[1]) for a in S)
            if any(d > 1 for _, d in D.in_degree()) or not nx.is_directed_acyclic_graph(D): continue
            w = sum(a[2] for a in S)
            if best is None or w > best: best = w
    return best

def check(ns):
    E = [(0,1,3,'01'),(1,2,5,'12'),(2,3,6,'23'),(3,1,4,'31'),(0,3,2,'03'),(4,2,1,'42'),(2,4,7,'24')]
    assert sorted(ns["max_branching"](5, E)) == sorted(['01','24','12','23'])
    F = [(0,2,4,'02'),(0,3,7,'03'),(0,4,8,'04'),(1,0,1,'10'),(3,0,2,'30'),(3,1,7,'31')]
    assert sorted(ns["max_branching"](5, F)) == sorted(['02','04','31','03'])
    G3 = [(1,0,1,'yx'),(0,1,1,'xy'),(2,0,1,'zx')]
    assert len(ns["max_branching"](3, G3)) == 2
    for _ in range(600):
        n = random.randint(1, 5)
        arcs = [(u, v, random.randint(-3, 9), (u, v, k)) for k, (u, v) in
                enumerate((u, v) for u in range(n) for v in range(n) if u != v and random.random() < 0.5)]
        tags = {a[3]: a for a in arcs}
        S = [tags[t] for t in ns["max_branching"](n, arcs)]
        D = nx.DiGraph(); D.add_nodes_from(range(n)); D.add_edges_from((a[0], a[1]) for a in S)
        assert all(d <= 1 for _, d in D.in_degree()) and nx.is_directed_acyclic_graph(D)
        assert sum(a[2] for a in S) == (brute(n, arcs) or 0)
        r = random.randrange(n)
        T = ns["min_arborescence"](n, arcs, r)
        D2 = nx.DiGraph(); D2.add_nodes_from(range(n)); D2.add_edges_from((a[0], a[1]) for a in arcs)
        reach = len(nx.descendants(D2, r)) == n - 1
        if not reach:
            assert T is None
        else:
            T = [tags[t] for t in T]
            H = nx.DiGraph(); H.add_nodes_from(range(n)); H.add_edges_from((a[0], a[1]) for a in T)
            assert nx.is_arborescence(H) and H.in_degree(r) == 0
            into_r = [a for a in arcs if a[1] != r]
            neg = [(u, v, -w, t) for (u, v, w, t) in into_r]
            assert -sum(a[2] for a in T) == brute(n, neg, need=n - 1)
