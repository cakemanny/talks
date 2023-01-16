def show_map(m):
    def this_node():
        # n1[label="{{height}|{1}}|{{xs}|{<f0>|<f1>|<f2>|<f3>}}"]
        height = "{{height}|{%s}}" % m.height
        kindset = "{{kindset}|{%s}}" % bin(m.kindset)
        xs_parts = [
            # f"<f{i}> {x}" if m._is_leaf(i) else
            f"<f{i}>"
            for i, x in enumerate(m.xs)
        ]
        xs = "{{xs}|{%s}}" % ('|'.join(xs_parts))
        label = f"{xs}|{kindset}|{height}"
        return f'{id(m)}[label="{label}"]'
    yield this_node()

    def show_entry(entry):
        k, v = entry
        label = f"{k}|{v}"
        return f'{id(entry)}[label="{label}"]'

    for i, x in enumerate(m.xs):
        if x is not None:
            if m._is_leaf(i):
                yield show_entry(x)
            else:
                yield from show_map(x)
            # The edge between the cell in the map and it's entry
            # or other map
            yield f"{id(m)}:f{i} -> {id(x)}"


if __name__ == '__main__':
    from pack.interp import read_all_forms
    m = read_all_forms('{:these "maps" :are "strange" :they "look" :rather "empty"}')[0]
    print("digraph {")
    print("    node[shape=record]")
    for x in show_map(m):
        print("   ", x)
    print("}")
