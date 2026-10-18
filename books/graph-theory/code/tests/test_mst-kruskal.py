import random
import networkx as nx

def check(ns):
    K = [(0,1,1),(0,2,2),(1,2,3),(3,4,4),(1,4,5),(1,3,6),(2,3,7),(2,4,8)]
    for UF in ("LabelUF", "HeightUF", "CompressUF", "SmallerHalfUF"):
        assert ns["kruskal"](5, K, ns[UF]) == [(0,1,1),(0,2,2),(3,4,4),(1,4,5)]
    uf = ns["HeightUF"](8)
    for x, y in [(0,1),(2,3),(0,2),(4,5),(6,7),(4,6),(1,5)]: uf.union(x, y)
    assert uf.parent == [-1,0,0,2,0,4,4,6] and uf.height == [3,0,1,0,2,0,1,0]
    uc = ns["CompressUF"](8)
    for x, y in [(0,1),(2,3),(0,2),(4,5),(6,7),(4,6),(1,5)]: uc.union(x, y)
    assert uc.parent == [-1,0,0,2,0,4,4,6]
    assert uc.find(7) == 0 and uc.parent == [-1,0,0,2,0,4,0,0] and uc.height[0] == 3
    u5 = ns["HeightUF"](5)
    for u, v, w in ns["kruskal"](5, K, ns["HeightUF"]): pass
    # A5 trace
    class Rec(ns["HeightUF"]):
        pass
    t = ns["kruskal"](5, K, Rec)
    # direct replay
    h = ns["HeightUF"](5)
    for u, v, w in [(0,1,1),(0,2,2),(3,4,4),(1,4,5)]: h.union(u, v)
    assert h.parent == [-1,0,0,0,3] and h.height == [2,0,0,1,0]
    # lecture bug demonstration
    B = [0,0,0,3,3]; u, v = 4, 1
    for k in range(5):
        if B[k] == B[v]: B[k] = B[u]
    assert B == [3,3,0,3,3]
    for _ in range(400):
        n = random.randint(1, 9); G = nx.gnp_random_graph(n, random.random())
        E = [(a, b, random.randint(1, 6)) for a, b in G.edges()]
        H = nx.Graph(); H.add_nodes_from(range(n)); H.add_weighted_edges_from(E)
        best = sum(d["weight"] for _, _, d in nx.minimum_spanning_edges(H, data=True))
        for UF in ("LabelUF", "HeightUF", "CompressUF", "SmallerHalfUF"):
            T = ns["kruskal"](n, E, ns[UF])
            assert sum(w for _, _, w in T) == best
            F = nx.Graph(); F.add_nodes_from(range(n)); F.add_edges_from((a, b) for a, b, _ in T)
            assert nx.is_forest(F) and nx.number_connected_components(F) == nx.number_connected_components(H)
    # random union-find sequences against a naive partition
    for _ in range(200):
        n = random.randint(1, 30); ufs = [ns[k](n) for k in ("LabelUF","HeightUF","CompressUF","SmallerHalfUF")]
        comp = list(range(n))
        for _ in range(60):
            x, y = random.randrange(n), random.randrange(n)
            if random.random() < 0.5:
                for uf in ufs: uf.union(x, y)
                a, b = comp[x], comp[y]; comp = [a if c == b else c for c in comp]
            else:
                for uf in ufs: assert (uf.find(x) == uf.find(y)) == (comp[x] == comp[y])
        for uf in ufs[1:3]:
            assert max(uf.height) <= max(1, n).bit_length()

def lecture_313(n, E):
    parent = [-1] * n; S = []
    for (x, y, w) in sorted(E, key=lambda e: e[2]):
        if len(S) == n - 1: break
        rx = x
        while parent[rx] != -1: rx = parent[rx]
        ry = y
        while parent[ry] != -1: ry = parent[ry]
        if rx != ry:
            S.append((x, y, w))
            while parent[x] != -1: t = parent[x]; parent[x] = rx; x = t
            while parent[y] != -1: t = parent[y]; parent[y] = rx; y = t
    return S

_check = check
def check(ns):
    _check(ns)
    E = [(0,1,1),(1,2,2),(0,2,3),(0,3,4),(1,3,5),(2,3,6)]
    assert lecture_313(4, E) == [(0,1,1),(1,2,2),(0,2,3)]          # the triangle
    assert ns["kruskal"](4, E, ns["CompressUF"]) == [(0,1,1),(1,2,2),(0,3,4)]
