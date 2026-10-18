import random
import networkx as nx

def check(ns):
    S = [(5,6),(6,7),(7,5),(7,2),(2,3),(3,4),(4,2),(3,0),(0,1),(1,0),(6,1)]
    adj = ns["adjacency_list"](8, S, True)
    assert adj == [[1],[0],[3],[4,0],[2],[6],[7,1],[5,2]]
    assert ns["finishing_order"](adj) == [1,0,4,3,2,7,6,5]
    assert ns["strongly_connected_components"](adj) == [2,2,1,1,1,0,0,0]
    assert ns["condensation"](adj) == ([2,2,1,1,1,0,0,0], [[1,2],[2],[]])
    T = [(0,1),(0,2),(1,3),(2,3),(3,4),(2,5),(5,4)]
    tadj = ns["adjacency_list"](6, T, True)
    assert ns["topological_sort"](tadj) == [0,2,5,1,3,4]
    assert ns["finishing_order"](tadj) == [4,3,1,5,2,0]
    assert ns["finishing_order"]([[1,2],[0],[]]) == [1,2,0]
    for _ in range(300):
        n = random.randint(1, 9)
        arcs = list({(random.randrange(n), random.randrange(n)) for _ in range(random.randint(0, 20))})
        arcs = [(u, v) for u, v in arcs if u != v]
        adj = ns["adjacency_list"](n, arcs, True)
        D = nx.DiGraph(); D.add_nodes_from(range(n)); D.add_edges_from(arcs)
        comp = ns["strongly_connected_components"](adj)
        mine = {frozenset(v for v in range(n) if comp[v] == c) for c in set(comp)}
        assert mine == {frozenset(c) for c in nx.strongly_connected_components(D)}
        comp, cadj = ns["condensation"](adj)
        for c in range(len(cadj)):
            assert all(c < d for d in cadj[c])
        order = ns["topological_sort"](adj)
        if nx.is_directed_acyclic_graph(D):
            pos = {v: i for i, v in enumerate(order)}
            assert all(pos[u] < pos[v] for u, v in arcs)
            assert ns["find_cycle_if_any"](adj) is None
            rev = ns["finishing_order"](adj)[::-1]; pos = {v: i for i, v in enumerate(rev)}
            assert all(pos[u] < pos[v] for u, v in arcs)
        else:
            assert order is None
            c = ns["find_cycle_if_any"](adj)
            assert len(c) >= 2 and len(set(c)) == len(c) and all(D.has_edge(c[i], c[(i+1) % len(c)]) for i in range(len(c)))
