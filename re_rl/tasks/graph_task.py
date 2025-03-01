# re_rl/tasks/graph_task.py

import random
import networkx as nx
from re_rl.tasks.base_task import BaseMathTask
from re_rl.tasks.prompts import PROMPT_TEMPLATES

class GraphTask(BaseMathTask):
    """
    Генерирует и решает графовые задачи.
    Поддерживаемые типы: "shortest_path", "minimum_spanning_tree", "diameter", "clustering_coefficient".
    detail_level управляет количеством шагов решения.
    """
    def __init__(self, task_type="shortest_path", num_nodes=10, edge_prob=0.5, language: str = "ru", detail_level: int = 3):
        self.task_type = task_type.lower()
        self.num_nodes = num_nodes
        self.edge_prob = edge_prob
        self.graph = None
        self.start = None
        self.end = None
        super().__init__("", language, detail_level)

    def generate_graph(self):
        self.graph = nx.gnp_random_graph(self.num_nodes, self.edge_prob, seed=random.randint(1, 1000), directed=False)
        if not nx.is_connected(self.graph):
            largest_cc = max(nx.connected_components(self.graph), key=len)
            self.graph = self.graph.subgraph(largest_cc).copy()

    def _create_problem_description(self):
        self.generate_graph()
        if self.task_type == "shortest_path":
            nodes = list(self.graph.nodes())
            self.start = random.choice(nodes)
            self.end = random.choice(nodes)
            while self.end == self.start:
                self.end = random.choice(nodes)
            task_description = f"кратчайший путь между узлами {self.start} и {self.end}"
            return PROMPT_TEMPLATES["graph"]["problem"][self.language].format(task_description=task_description)
        # Остальные типы остаются без изменений
        elif self.task_type == "minimum_spanning_tree":
            for (u, v) in self.graph.edges():
                self.graph[u][v]['weight'] = random.randint(1, 10)
            task_description = "минимальное остовное дерево данного графа"
            return PROMPT_TEMPLATES["graph"]["problem"][self.language].format(task_description=task_description)
        elif self.task_type == "diameter":
            task_description = "диаметр данного графа"
            return PROMPT_TEMPLATES["graph"]["problem"][self.language].format(task_description=task_description)
        elif self.task_type == "clustering_coefficient":
            task_description = "средний коэффициент кластеризации данного графа"
            return PROMPT_TEMPLATES["graph"]["problem"][self.language].format(task_description=task_description)
        else:
            return PROMPT_TEMPLATES["default"]["no_solution"].get(self.language, PROMPT_TEMPLATES["default"]["no_solution"]["en"])

    def solve(self):
        self.description = self._create_problem_description()
        steps = []
        if self.task_type == "shortest_path":
            try:
                # Реализуем простой алгоритм Дейкстры
                nodes = list(self.graph.nodes())
                dist = {v: float('inf') for v in nodes}
                prev = {v: None for v in nodes}
                dist[self.start] = 0
                Q = set(nodes)
                iteration = 1
                while Q:
                    u = min(Q, key=lambda v: dist[v])
                    # Записываем шаг итерации
                    updates = []
                    for v in self.graph.neighbors(u):
                        if v in Q:
                            weight = self.graph[u][v].get('weight', 1)
                            if dist[u] + weight < dist[v]:
                                old_val = dist[v]
                                dist[v] = dist[u] + weight
                                prev[v] = u
                                updates.append(f"{v}: {old_val}→{dist[v]}")
                    iter_template = PROMPT_TEMPLATES["graph"]["shortest_path_iter"].get(self.language, "Step {iter}: Selected {u} with distance {d}. Updates: {updates}.")
                    steps.append(iter_template.format(iter=iteration, u=u, d=dist[u], updates=", ".join(updates) if updates else "None"))
                    Q.remove(u)
                    if u == self.end:
                        break
                    iteration += 1
                # Восстанавливаем путь
                path = []
                u = self.end
                while u is not None:
                    path.insert(0, u)
                    u = prev[u]
                final_template = PROMPT_TEMPLATES["graph"]["shortest_path_final"].get(self.language, "Final path: {path}.")
                steps.append(final_template.format(path=path))
                self.solution_steps.extend(steps)
                self.final_answer = str(path)
            except Exception as e:
                error_msg = PROMPT_TEMPLATES["default"]["error"].get(self.language, PROMPT_TEMPLATES["default"]["error"]["en"]).format(error=str(e))
                steps.append(error_msg)
                self.solution_steps.extend(steps)
                self.final_answer = error_msg
        else:
            # Остальные типы остаются как раньше
            if self.task_type == "minimum_spanning_tree":
                try:
                    mst = nx.minimum_spanning_tree(self.graph)
                    edges = list(mst.edges(data=True))
                    step_template = PROMPT_TEMPLATES["graph"]["mst_step"].get(self.language, "Step: {edges}")
                    steps.append(step_template.format(edges=edges))
                    self.final_answer = str(edges)
                except Exception as e:
                    error_msg = PROMPT_TEMPLATES["default"]["error"].get(self.language, PROMPT_TEMPLATES["default"]["error"]["en"]).format(error=str(e))
                    steps.append(error_msg)
                    self.final_answer = error_msg
            elif self.task_type == "diameter":
                try:
                    diam = nx.diameter(self.graph)
                    step_template = PROMPT_TEMPLATES["graph"]["diameter_step"].get(self.language, "Step: {diameter}")
                    steps.append(step_template.format(diameter=diam))
                    self.final_answer = str(diam)
                except Exception as e:
                    error_msg = PROMPT_TEMPLATES["default"]["error"].get(self.language, PROMPT_TEMPLATES["default"]["error"]["en"]).format(error=str(e))
                    steps.append(error_msg)
                    self.final_answer = error_msg
            elif self.task_type == "clustering_coefficient":
                try:
                    avg_coeff = nx.average_clustering(self.graph)
                    step_template = PROMPT_TEMPLATES["graph"]["clustering_step"].get(self.language, "Step: {avg_coeff}")
                    steps.append(step_template.format(avg_coeff=avg_coeff))
                    self.final_answer = str(avg_coeff)
                except Exception as e:
                    error_msg = PROMPT_TEMPLATES["default"]["error"].get(self.language, PROMPT_TEMPLATES["default"]["error"]["en"]).format(error=str(e))
                    steps.append(error_msg)
                    self.final_answer = error_msg
            else:
                error_msg = PROMPT_TEMPLATES["default"]["no_solution"].get(self.language, PROMPT_TEMPLATES["default"]["no_solution"]["en"])
                steps.append(error_msg)
                self.final_answer = error_msg
            self.solution_steps.extend(steps)

    def get_task_type(self):
        return "graph"

    @classmethod
    def generate_random_task(cls, only_valid=False, num_nodes=10, edge_prob=0.5, language: str = "ru", detail_level: int = 3):
        task_types = ["shortest_path", "minimum_spanning_tree", "diameter", "clustering_coefficient"]
        task_type = random.choice(task_types)
        task = cls(task_type=task_type, num_nodes=num_nodes, edge_prob=edge_prob, language=language, detail_level=detail_level)
        task.solve()
        no_solution_str = PROMPT_TEMPLATES["default"]["no_solution"].get(language, PROMPT_TEMPLATES["default"]["no_solution"]["en"])
        if only_valid and task.final_answer == no_solution_str:
            return cls.generate_random_task(only_valid=only_valid, num_nodes=num_nodes, edge_prob=edge_prob, language=language, detail_level=detail_level)
        return task
