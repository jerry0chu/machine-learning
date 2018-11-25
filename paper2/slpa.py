import numpy as np
import networkx as nx
from collections import defaultdict


def find_communities(G, T, r):
    """
    Speaker-Listener Label Propagation Algorithm (SLPA)
    see http://arxiv.org/abs/1109.5720
    """

    # Stage 1: Initialization
    memory = {i: {i: 1} for i in G.nodes()}

    # Stage 2: Evolution
    # 开始遍历T次所有节点
    for t in range(T):
        # 随机排列遍历顺序
        listenersOrder = list(G.nodes())
        np.random.shuffle(listenersOrder)
        # 开始遍历节点
        for listener in listenersOrder:
            # 每个节点的key就是与他相连的节点标签名
            speakers = G[listener].keys()
            if len(speakers) == 0:
                continue

            labels = defaultdict(int)
            # 遍历所有与其相关联的节点
            for j, speaker in enumerate(speakers):
                # Speaker Rule
                total = float(sum(memory[speaker].values()))
                # 查看speaker中memory中出现概率最大的标签并记录，key是标签名，value是Listener与speaker之间的权
                labels[list(memory[speaker].keys())[
                    np.random.multinomial(1, [freq / total for freq in memory[speaker].values()]).argmax()]] += 1

            # Listener Rule
            # 查看labels中值最大的标签，让其成为当前listener的一个记录
            acceptedLabel = max(labels, key=labels.get)

            # Update listener memory
            if acceptedLabel in memory[listener]:
                memory[listener][acceptedLabel] += 1
            else:
                memory[listener][acceptedLabel] = 1

    # Stage 3:
    for node, mem in memory.items():
        # print(node, mem)
        flag = []
        for label, freq in mem.items():
            if freq / float(T + 1) < r:
                flag.append(label)
        for f in flag:
            del mem[f]
        # print(mem)
        # print('--------------')

    # Find nodes membership
    # 扫描memory中的记录标签，相同标签的节点加入同一个社区中
    communities = {}
    for node, mem in memory.items():
        for label in mem.keys():
            if label in communities:
                communities[label].add(node)
            else:
                communities[label] = set([node])

    # Remove nested communities
    nestedCommunities = set()
    keys = list(communities.keys())
    for i, label0 in enumerate(keys[:-1]):
        comm0 = communities[label0]
        for label1 in keys[i + 1:]:
            comm1 = communities[label1]
            if comm0.issubset(comm1):
                nestedCommunities.add(label0)
            elif comm0.issuperset(comm1):
                nestedCommunities.add(label1)

    for comm in nestedCommunities:
        del communities[comm]
    return communities


if __name__ == '__main__':

    data = [(1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9), (1, 11), (1, 12), (1, 13), (1, 14), (1, 18), (1, 20), (1, 22), (1, 32),(2, 3), (2, 4), (2, 8), (2, 14), (2, 18), (2, 20), (2, 22), (2, 31), (3, 4), (3, 8), (3, 9), (3,10), (3, 14), (3, 28), (3, 29), (3, 33), (4, 8), (4, 13), (4, 14), (5, 7), (5, 11), (6, 7), (6, 11), (6, 17), (7, 17), (9, 31), (9, 33), (9, 34), (10, 34), (14, 34), (15, 33), (15, 34), (16, 33), (16, 34), (19, 33), (19, 34), (20, 34), (21, 33), (21, 34), (23, 33), (23, 34), (24, 26), (24, 28), (24, 30), (24, 33), (24, 34), (25, 26), (25, 28), (25, 32), (26, 32), (27, 30), (27, 34), (28, 34), (29, 32), (29, 34), (30, 33), (30, 34), (31, 33), (31, 34), (32, 33), (32, 34), (33, 34)]
    G = nx.Graph()
    G.add_edges_from(data)
    """
    G = nx.read_gml(r'dataset\dolphins.gml', label='id')
    for i in range(100):
            result = find_communities(G, 20, 0.45)
            # print(result)
            count = []
            for k, v in result.items():
                count.append(len(result[k]))
            if sum(count) > 34:
                print(sum(count))
    """
    result = find_communities(G, 20, 0.1)
    print(result)
    count = []
    for k, v in result.items():
        print(len(result[k]))
