import random
import networkx as nx
INF = float('inf')

def kids(h, v):
    out, c = [], h.child[v]
    if c != -1:
        x = c
        while True:
            out.append(x); x = h.right[x]
            if x == c: break
    return out

def shape(h, names):
    def rec(v):
        ks = kids(h, v); s = f"{names[v]}{h.key[v]}{'*' if h.flag[v] else ''}"
        return s + ("[" + ",".join(rec(u) for u in ks) + "]" if ks else "")
    return " ".join(f"{i}:{rec(r)}" for i, r in enumerate(h.B) if r != -1)

def invariants(h, alive):
    roots = [v for v in alive if h.parent[v] == -1]
    assert len({h.degree[r] for r in roots}) == len(roots)
    assert all(h.B[h.degree[r]] == r for r in roots) and sum(x != -1 for x in h.B) == len(roots)
    for v in alive:
        ks = kids(h, v); assert len(ks) == h.degree[v]
        assert all(h.parent[u] == v and h.key[u] >= h.key[v] for u in ks)
        vals = sorted(h.degree[u] + h.flag[u] for u in ks)
        assert all(val >= i for i, val in enumerate(vals))

def check(ns):
    K = [(0,1,1),(0,2,2),(1,2,3),(3,4,4),(1,4,5),(1,3,6),(2,3,7),(2,4,8)]
    adj = ns["weighted_adjacency"](5, K)
    assert adj == [[(1,1),(2,2)],[(0,1),(2,3),(4,5),(3,6)],[(0,2),(1,3),(3,7),(4,8)],[(4,4),(1,6),(2,7)],[(3,4),(1,5),(2,8)]]
    assert ns["prim_array"](adj) == [(0,1,1),(0,2,2),(1,4,5),(4,3,4)]
    names = "abcdefgh"; key = [7,3,9,5,8,2,6,4]
    bh = ns["BinaryHeap"](8, key)
    for v in range(8): bh.insert(v)
    assert [names[x] + str(key[x]) for x in bh.a] == ["f2","h4","b3","d5","e8","c9","g6","a7"]
    assert bh.delete_min() == 5 and [names[x] for x in bh.a] == list("bhgdeca")
    key[2] = 1; bh.decrease_key(2); assert [names[x] for x in bh.a] == list("chbdega")
    key = [7,3,9,5,8,2,6,4] + [INF, INF]; fh = ns["FibonacciHeap"](10, key)
    for v in range(8): fh.insert(v)
    assert shape(fh, names) == "3:f2[e8,b3[a7,d5[c9]],h4[g6]]"
    key[0] = 1; fh.decrease_key(0); assert shape(fh, names) == "0:a1 3:f2[e8,b3*[d5[c9]],h4[g6]]"
    key[3] = 0; fh.decrease_key(3); assert shape(fh, names) == "3:d0[c9,f2*[e8,h4[g6]],a1[b3]]"
    assert fh.delete_min() == 3 and shape(fh, names) == "0:c9 1:a1[b3] 2:f2*[e8,h4[g6]]"
    assert fh.delete_min() == 0 and shape(fh, names) == "1:b3[c9] 2:f2*[e8,h4[g6]]"
    key[6] = 1; fh.decrease_key(6); assert shape(fh, names) == "0:g1 1:b3[c9] 2:f2*[e8,h4*]"
    # random heap operations
    for Heap in (ns["BinaryHeap"], ns["FibonacciHeap"]):
        for _ in range(500):
            n = random.randint(1, 40); key = [INF] * n; h = Heap(n, key); alive, gone = set(), set()
            for _ in range(random.randint(1, 150)):
                r = random.random(); cand = [v for v in range(n) if v not in alive and v not in gone]
                if r < 0.4 and cand:
                    v = random.choice(cand); key[v] = random.randint(0, 100); h.insert(v); alive.add(v)
                elif r < 0.7 and alive:
                    v = random.choice(sorted(alive)); key[v] -= random.randint(0, 30); h.decrease_key(v)
                elif alive:
                    m = h.delete_min(); assert key[m] == min(key[v] for v in alive); alive.remove(m); gone.add(m)
                if Heap is ns["FibonacciHeap"]: invariants(h, alive)
    for _ in range(300):
        n = random.randint(1, 12); G = nx.gnp_random_graph(n, random.random())
        if not nx.is_connected(G): continue
        E = [(a, b, random.randint(1, 9)) for a, b in G.edges()]
        H = nx.Graph(); H.add_weighted_edges_from(E); H.add_nodes_from(range(n))
        best = sum(d["weight"] for _, _, d in nx.minimum_spanning_edges(H, data=True))
        adj = ns["weighted_adjacency"](n, E)
        for T in (ns["prim_array"](adj), ns["prim_heap"](adj), ns["prim_heap"](adj, 0, ns["FibonacciHeap"]), ns["prim_lazy"](adj)):
            assert len(T) == n - 1 and sum(w for _, _, w in T) == best
