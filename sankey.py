import networkx as nx
import json

#This class generate a sankey json format for the d3 sankey plugin
class Sankey(object):
    def __init__(self, universe=None):
        self.universe = universe
        self.universe_index = self.calc_index_universe()
        self.pipeline = []
        self.universe_nodes = None
        self.G = None

    def add_universe(self, universe):
        if self.universe is None:
            self.universe = set([])
        self.universe = self.universe.union(universe)

    def add_pipeline(self, pipeline):
        if self.universe_index is None:
            self.universe_index = self.calc_index_universe()

        links = [{
            "source": self.universe_index[uv["source"]], 
            "target": self.universe_index[uv["target"]], 
            "value": uv["value"]} for uv in pipeline]
        self.pipeline.append(links)

    def calc_index_universe(self):
        if self.universe is not None:
            node_index = {}
            self.universe_nodes = sorted(list(self.universe))
            for i, term in enumerate(self.universe_nodes):
                if not term in node_index:
                    node_index[term] = i
            return node_index

    def build_graph(self):
        self.G = nx.DiGraph()
        links = self.pipeline[0]
        for p1, p2 in zip(self.pipeline, self.pipeline[1:]):
            for v in self.join(p1, p2):
                links.append(v)
        edges = ((link["source"], link["target"], link["value"]) for link in links)
        self.G.add_weighted_edges_from(edges)

    def join(self, left, right):
        from collections import defaultdict
        join_data = []
        right_values = {right_value["source"]: right_value for right_value in right}
        for left_value in left:
            try:
                right_value = right_values[left_value["source"]]
                join_data.append({
                    "source": left_value["target"], 
                    "target": right_value["target"], 
                    "value": right_value["value"]})
            except KeyError:
                pass
                #join_data.append({
                #    "source": left_value["target"], 
                #    "target": node_index["UNKNOW"], 
                #    "value": left_value["value"]})
        return join_data

    #def only_paths_of_size(self, paths, length=3):
    #    return [edges for edges in paths if len(edges) >= 3]

    def paths(self, base, only_paths_of_size):
        self.build_graph()
        base_universe = set((self.universe_index[r] for r in base))
        linked = []
        uv_count = {}
        for source in base_universe:
            shorted = nx.shortest_path(self.G, source=source)
            paths = only_paths_of_size(shorted.values())
            for edges in paths:
                for u, v in zip(edges, edges[1:]):
                    key = "{}{}".format(u,v)
                    if not key in uv_count:
                        linked.append({
                            "source": u, 
                            "target": v, 
                            "value": None})
                        uv_count[key] = 0
                    uv_count[key] += 1

        for link in linked:
            u = link["source"]
            v = link["target"]
            key = "{}{}".format(u,v)
            link["value"] = uv_count.get(key, self.G[u][v]["weight"])
        return linked

    def clean_nodes_links(self, links):
        indexes = set([link["source"] for link in links])
        indexes = indexes.union(set([link["target"] for link in links]))
        n_nodes = []
        n_links = []
        other_index = {}
        for n_index, index in enumerate(indexes):
            other_index[index] = n_index
            n_nodes.append(self.universe_nodes[index])

        for values in links:
            r = {}
            try:
                s = {"source": other_index[values["source"]]}
            except KeyError:
                s = {"source": values["source"]}

            try:
                t = {"target": other_index[values["target"]]}
            except KeyError:
                s = {"target": values["target"]}

            r.update(s)
            r.update(t)
            r["value"] = values["value"]
            n_links.append(r)

        return n_nodes, n_links

    def json_sankey(self, n_nodes, n_links, type_="normal"):
        if type_ == "normal":
            result = {"nodes": [{"name": node} for node in n_nodes], "links": n_links}
        elif type_ == "colors":
            result = {"nodes": [{"name": node, "id": node.lower().replace(" ", "_") + "_score"} 
                        for node in n_nodes],
                    "links": n_links}
        return result

    def json(self, paths, name="sankey.json"):
        n_nodes, n_links = self.clean_nodes_links(paths)
        result = self.json_sankey(n_nodes, n_links)
        with open(name, "w") as f:
            f.write(json.dumps(result))

#### USE EXAMPLE
#def firma_molecular_graph(fm):
#    data = []
#    for i, row in fm.iterrows():
#        data.append({
#            "source": row["fm"], 
#            "target": row["fm_gene"], 
#            "value": 1})
#    return data

#def signature_graph(genes):
#    data = []
#    for i, row in genes.iterrows():
#        data.append({
#            "source": row["gene"], 
#            "target": str(abs(row["value"])), 
#            "value": 1})
#    return data
    
#def generate_sankey_json():
#    from sankey import Sankey
#    import pandas as pd

#    df = pd.read_csv(filepath_or_buffer="rdb_sankeys/lumb_rdb_regulon.sif", sep='\t')
#    df_signature = pd.read_csv(filepath_or_buffer="rdb_sankeys/lumb_rdb_signature.txt", sep='\t')
#    base = df[df["fm"].isin(df["fm_gene"])]

#    universe1 = set((r["fm"] for i, r in base.iterrows()))
#    universe2 = set(r["gene"] for i, r in df_signature.iterrows())
#    universe3 = set(str(abs(r["value"])) for i, r in df_signature.iterrows())
#    universe1_1 = set((r["fm_gene"] for i, r in base.iterrows()))

#    sankey = Sankey()
#    sankey.add_universe(universe1)
#    sankey.add_universe(universe2)
#    sankey.add_universe(universe3)
#    sankey.add_universe(universe1_1)

#    sankey.add_pipeline(firma_molecular_graph(base))
#    sankey.add_pipeline(signature_graph(df_signature))
    
#    last = set([sankey.universe_index[e] for e in universe3])
#    def only_paths_of_size(paths, length=3):
#        return [edges for edges in paths if edges[-1] in last and len(edges) == length]

#    paths = sankey.paths(base["fm"], only_paths_of_size)
#    sankey.json(paths, name="sankey.json")
