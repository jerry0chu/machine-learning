import random
import numpy as np
import networkx as nx
from collections import defaultdict
import subprocess


def k_shell(G):
    k = 1
    kshell = {}
    while nx.nodes(G):
        kshell.setdefault(k, [])
        same_shell_nodes = [node_degree[0] for node_degree in nx.degree(G) if node_degree[1] <= k]
        if same_shell_nodes:
            G.remove_nodes_from(same_shell_nodes)
            kshell[k].extend(same_shell_nodes)
            continue
        else:
            k += 1
    kshell = {ks: n for ks, n in kshell.items() if n}  # 去除kshell中空节点
    core = max(kshell.items(), key=lambda x: x[0])[1]
    brink = min(kshell.items(), key=lambda x: x[0])[1]
    print('核心节点：')
    print(core)
    print('边缘节点：')
    print(brink)
    return kshell, brink


def influence(kshell, brink):
    process_kshell = {}
    for ks, nodes in kshell.items():
        for node in nodes:
            process_kshell[node] = ks
    # print(process_kshell)

    G = nx.read_gml('./dataset/karate.gml', label='id')
    G.remove_nodes_from(brink)
    # print(len(G.edges))
    print(len(G.nodes))
    nor_degree = {}
    max_degree_node, max_degree = max(nx.degree(G), key=lambda x: x[1])
    for node, degree in nx.degree(G):
        nor_degree[node] = degree / max_degree
    # print(nor_degree)

    IN = {}
    for node in G.nodes:
        IN[node] = process_kshell[node] + nor_degree[node]
    print('综合影响力：')
    print(IN)
    return IN, G


def find_communities(G, T, r, IN):
    """
    Speaker-Listener Label Propagation Algorithm (SLPA)
    see http://arxiv.org/abs/1109.5720
    """

    # Stage 1: Initialization
    memory = {i: {i: 1} for i in G.nodes()}
    print(memory)

    # Stage 2: Evolution
    # 开始遍历T次所有节点
    for t in range(T):
        # 随机排列遍历顺序
        listenersOrder = [n[0] for n in sorted(IN.items(), key=lambda x: x[1], reverse=False)]
        # 开始遍历节点
        # print(listenersOrder)
        # print(memory)
        for listener in listenersOrder:
            # 每个节点的key就是与他相连的节点标签名
            speakers = G[listener].keys()  # listener的邻居节点
            # print(list(nx.neighbors(G, listener)))
            if len(speakers) == 0:
                continue
            # 存放每个邻居节点出现次数最多的标签
            labels = defaultdict(int)  # key不存在时，返回的是工厂函数的默认值，比如list对应[ ]，str对应的是空字符串，set对应set( )，int对应0
            count = {}
            # 遍历所有与其相关联的节点
            for j, speaker in enumerate(speakers):
                # Speaker Rule
                total = float(sum(memory[speaker].values()))  # 计算speaker节点记忆标签总数
                # 论文中应该是随机选取一个，因为标签出现次数越多，相应地被选中的概率也就越大
                # 查看speaker中memory中出现频率最高的标签并记录，存在加1，不存在赋值1，key是标签名，value是Listener与speaker之间的权
                label = list(memory[speaker].keys())[
                    np.random.multinomial(1, [freq / total for freq in memory[speaker].values()]).argmax()]
                labels[label] += 1
                count[speaker] = label

            # Listener Rule
            # 选择标签影响力最大的一个
            # 计算邻居节点相同标签影响力之和
            neighbor_label_node = {}  # 邻居节点的{标签：[节点]}
            for neighbor_node, neighbor_label in count.items():
                if neighbor_label in neighbor_label_node.keys():
                    neighbor_label_node[neighbor_label].append(neighbor_node)
                else:
                    neighbor_label_node.setdefault(neighbor_label, [])
                    neighbor_label_node[neighbor_label].append(neighbor_node)
            label_influence = {}  # {标签：相同标签影响力之和}
            for label, nodes in neighbor_label_node.items():
                label_influence[label] = 0
                for n in nodes:
                    label_influence[label] += IN[n]
            max_label_IN = max(label_influence.items(), key=lambda x: x[1])[1]
            # print(label_influence)
            freq_max_labels = [(k, v) for k, v in label_influence.items() if v == max_label_IN]
            # print('候选标签：')
            # print(freq_max_labels)
            acceptedLabel = random.choice(freq_max_labels)[0]

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


def EQ(result):
    with open(r"/home/zm/桌面/copra/karate_detection.txt", 'a') as f:
        for label, nodes in result.items():
            str_nodes = [str(n) for n in nodes]
            content = " ".join(str_nodes)
            f.write(content+"\n")
    cmd1 = "cd /home/zm/桌面/copra"
    cmd2 = "java -cp copra.jar ModOverlap karate.txt karate_detection.txt"
    cmd = cmd1+"&&"+cmd2
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    output, _ = p.communicate()
    with open(r"/home/zm/桌面/copra/karate_detection.txt", 'w') as f:
        f.truncate()
    return float(output.decode('ascii').strip().split(' ')[-1])


if __name__ == '__main__':
    final = []
    R = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45]
    mean_com = []
    for r in R:
        EQs = []
        com = []
        for i in range(100):
            G = nx.read_gml(r'./dataset/karate.gml', label='id')
            kshell, brink = k_shell(G)
            IN, G = influence(kshell, brink)
            result = find_communities(G, 50, r, IN)
            print(result)
            G = nx.read_gml(r'./dataset/karate.gml', label='id')
            brink_node_label = {}
            node_label = {}  # 除边缘节点外的 节点：标签 键值对
            for label, nodes in result.items():
                for node in nodes:
                    node_label[node] = label
            for brink_node in brink:
                neighbors = nx.neighbors(G, brink_node)
                neighbors_influence = {}
                for neighbor in neighbors:
                    if neighbor:
                        neighbors_influence[neighbor] = IN[neighbor]
                max_neighbors_node, max_neighbor_IN = max(neighbors_influence.items(), key=lambda x: x[1])
                max_neighbors_label = [node_label[node] for node, IN in neighbors_influence.items() if IN == max_neighbor_IN]
                # print('节点{}最大邻居:{}'.format(brink_node, max_neighbors_node))
                # print(brink_node, max_neighbors_node)
                brink_node_label[brink_node] = random.choice(max_neighbors_label)
            # 后处理加入边缘节点
            for node, label in brink_node_label.items():
                # print(node, label)
                result[label].add(node)
            for k, v in result.items():
                result[k] = list(v)
            EQs.append(EQ(result))
            com.append(len(result.keys()))
        final.append(sum(EQs)/100)
        mean_com.append(sum(com)/100)
    print(final)
    print(mean_com)
