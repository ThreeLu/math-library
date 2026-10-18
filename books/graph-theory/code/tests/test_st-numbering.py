import random
import networkx as nx

def is_st(adj, s, t, stn):
    n = len(adj)
    if sorted(stn) != list(range(1, n + 1)) or stn[s] != 1 or stn[t] != n: return False
    return all(any(stn[u] < stn[v] for u in adj[v]) and any(stn[u] > stn[v] for u in adj[v])
               for v in range(n) if v not in (s, t))

def check(ns):
    Z = [(0,1),(0,2),(1,2),(1,3),(2,4),(3,4),(3,5),(4,5),(5,0)]
    adj = ns["adjacency_list"](6, Z)
    assert adj == [[1,2,5],[0,2,3],[0,1,4],[1,4,5],[2,3,5],[3,4,0]]
    assert ns["dfn_low"](adj, 1, 0) == ([0,1,2,4,3,5],[-1,0,1,4,2,3],[0,0,0,0,0,0],[-1,0,0,5,3,0])
    assert ns["st_numbering"](adj, 1, 0) == [6,1,5,2,4,3]
    d, p, l, lf = ns["dfn_low"](adj, 0, 1)
    assert (d, p, l, lf) == ([1,0,2,4,3,5],[1,-1,0,4,2,3],[0,0,0,0,0,1],[1,-1,1,1,3,0])
    assert ns["st_numbering"](adj, 0, 1) == [1,6,5,3,4,2]
    two = ns["adjacency_list"](6, [(0,1),(1,2),(2,0),(2,3),(3,4),(4,5),(5,3)])
    assert ns["cut_vertices"](two) == {2, 3}
    tested = 0
    while tested < 1500:
        n = random.randint(3, 11); G = nx.gnp_random_graph(n, random.random())
        if nx.is_connected(G):
            a = [list(G[v]) for v in range(n)]
            for x in a: random.shuffle(x)
            assert ns["cut_vertices"](a, random.randrange(n)) == set(nx.articulation_points(G))
        if not nx.is_biconnected(G): continue
        a = [list(G[v]) for v in range(n)]
        for x in a: random.shuffle(x)
        s, t = random.choice(list(G.edges()))
        if random.random() < 0.5: s, t = t, s
        assert is_st(a, s, t, ns["st_numbering"](a, s, t))
        tested += 1
