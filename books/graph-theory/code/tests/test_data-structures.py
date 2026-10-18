def check(ns):
    lst = ns["new_list"]()
    ns["push_front"](lst, 5); b = ns["push_front"](lst, 3); ns["push_front"](lst, 7)
    assert (lst["data"], lst["nxt"], lst["head"]) == ([5, 3, 7], [-1, 0, 1], 2)
    ns["insert_after"](lst, b, 9)
    assert lst["nxt"] == [-1, 3, 1, 0] and ns["to_python_list"](lst) == [7, 3, 9, 5]
    ns["delete_after"](lst, b)
    assert lst["nxt"] == [-1, 0, 1, 0] and ns["to_python_list"](lst) == [7, 3, 5]
    ns["reverse"](lst)
    assert ns["to_python_list"](lst) == [5, 3, 7] and lst["head"] == 0
    parent = [-1, 0, 0, 1, 1, 2]
    assert ns["root_of"](parent, 4) == 0 and ns["depth_of"](parent, 4) == 2
