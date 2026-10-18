import random
import networkx as nx

def rand_graph(n, p):
    return [(u, v) for u in range(n) for v in range(u + 1, n) if random.random() < p]

def check(ns):
    adj = ns["adjacency_list"](5, ns["G_edges"])
    assert ns["dfs"](adj, 0) == [-1, 0, 1, 2, 3]
    assert ns["bfs"](adj, 0) == ([-1, 0, 0, 0, 1], [0, 1, 1, 1, 2])
    A = ns["adjacency_matrix"](5, ns["G_edges"])
    assert ns["dfs_matrix"](A, 0) == [-1, 0, 1, 2, 3]
    H = [(0,1),(0,2),(1,3),(2,4),(3,4),(3,5),(4,5),(5,6)]
    adjH = ns["adjacency_list"](7, H)
    assert adjH == [[1,2],[0,3],[0,4],[1,4,5],[2,3,5],[3,4,6],[5]]
    assert ns["bfs"](adjH, 0)[1] == [0,1,1,2,2,3,4] and ns["bfs"](adjH, 0)[0] == [-1,0,0,1,2,3,5]
    assert ns["bipartite_or_odd_cycle"](adjH) == ('odd cycle', [3, 1, 0, 2, 4])
    H2 = [e for e in H if e != (3, 4)]
    assert ns["bipartite_or_odd_cycle"](ns["adjacency_list"](7, H2)) == ('bipartite', [0,1,1,0,0,1,0])
    assert ns["dfs"](adjH, 6) == [1,3,0,5,2,6,-1]
    assert ns["bfs"](adjH, 6) == ([1,3,4,5,5,6,-1], [4,3,3,2,2,1,0])
    for _ in range(200):
        n = random.randint(1, 10); E = rand_graph(n, random.random())
        adj = ns["adjacency_list"](n, E); G = nx.Graph(); G.add_nodes_from(range(n)); G.add_edges_from(E)
        s = random.randrange(n)
        reach = nx.node_connected_component(G, s)
        for f in (ns["dfs"], lambda a, s: ns["bfs"](a, s)[0], lambda a, s: ns["dfs_matrix"](ns["adjacency_matrix"](n, E), s),
                  ns["dfs_recursive"]):
            t = f(adj, s)
            assert {v for v in range(n) if t[v] != -2} == reach
            for v in reach - {s}:
                assert G.has_edge(t[v], v)
        tree, dist = ns["bfs"](adj, s)
        sp = nx.single_source_shortest_path_length(G, s)
        assert all(dist[v] == sp[v] for v in sp)
        t = random.randrange(n); p = ns["shortest_path"](adj, s, t)
        if t in reach:
            assert len(p) - 1 == sp[t] and p[0] == s and p[-1] == t and all(G.has_edge(a, b) for a, b in zip(p, p[1:]))
        else:
            assert p is None
        comp = ns["components"](adj)
        for C in nx.connected_components(G):
            assert len({comp[v] for v in C}) == 1
        assert len(set(comp)) == nx.number_connected_components(G)
        kind, data = ns["bipartite_or_odd_cycle"](adj)
        assert (kind == 'bipartite') == nx.is_bipartite(G)
        if kind == 'bipartite':
            assert all(data[u] != data[v] for u, v in E)
        else:
            c = data
            assert len(c) % 2 == 1 and len(set(c)) == len(c) and all(G.has_edge(c[i], c[(i + 1) % len(c)]) for i in range(len(c)))
