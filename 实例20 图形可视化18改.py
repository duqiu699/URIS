import gurobipy as gp
from gurobipy import GRB
import math
import matplotlib.pyplot as plt




def euclidean_distance(coord1, coord2):
    return math.sqrt((coord1[0] - coord2[0]) ** 2 + (coord1[1] - coord2[1]) ** 2)


def minimize_cost():  # 当一段逻辑 “可能重复调用” 或 “代码超过 50 行、步骤分 3 步以上” 时，建议写函数

    # 1. 定义问题数据                    #大规模问题无需全部列举 可以优化
    locations = [0, 1, 2, 3, 4, 5, 6, 7,8,9,10,11]  # 配送点：0表示起点（仓库），1-3表示客户
    drones = [0, 1, 2]  # 两个无人机
    usv = [0, 1]

    # 节点坐标
    coordinates = {
        0: (0, 0), 1: (20, 30), 2: (15, 40), 3: (40, 20),
        4: (25, 25), 5: (30, 35), 6: (35, 15), 7: (45, 30),
        8: (23, 29), 9: (20, 5), 10: (50, 34), 11: (34, 17),
    }

    # 计算无人机和无人船之间的运行时间
    drone_speed = 2.0  # 单位距离/分钟
    usv_speed = 1.0  # 单位距离/分钟

    travel_time_d = {}
    travel_time_k = {}

    for i in locations:
        for j in locations:
            if i != j:
                dist = euclidean_distance(coordinates[i], coordinates[j])
                travel_time_d[i, j] = dist / drone_speed
                travel_time_k[i, j] = dist / usv_speed

    travel_time_k = {k: v * 2 for k, v in travel_time_d.items()}

    time_windows = {  # 客户时间窗 [最早可送达时间, 最晚必须送达时间]（分钟）
        0: [0, 1000],  # 起点（仓库）：必须在0时刻出发
        1: [25, 90],  # 客户1：最早10点，最晚30点送达
        2: [0, 60],  # 客户2：最早20点，最晚50点送达
        3: [20, 90],  # 客户3：最早15点，最晚40点送达
        4: [15, 80],
        5: [15, 60],
        6: [30, 70],
        7: [0, 60],
        8: [25, 90],
        9: [80, 130],
        10: [40, 110],
        11: [45, 95]

    }
    service_time = {1: 5, 2: 15, 3: 5, 4: 10, 5: 20, 6: 25, 7: 15, 8: 20, 9: 5, 10: 30,
                    11: 15, 12: 20, 13: 20, 14: 5, 15: 15
                    }  # 每个客户的服务时间（分钟）

    flying_duration = 120

    # 2. 创建模型
    model = gp.Model("TwoDronesVRTPW")

    # 3. 定义变量
    # x[d,i,j] = 1 表示无人机d从位置i直接前往位置j，0表示不走该弧
    x1 = model.addVars(drones, [(i, j) for i in locations for j in locations if i != j], vtype=GRB.BINARY,
                       name="x")  # locations:[0,1,2,3]
    x2 = model.addVars(usv, [(i, j) for i in locations for j in locations if i != j], vtype=GRB.BINARY, name="x")

    # ta1[d,i] = 无人机d leave位置i的时间。结果：t[0]...t[3]
    ta1 = model.addVars(drones, locations, vtype=GRB.CONTINUOUS, lb=0, name="t_leave_a")
    # ta2 arrive
    ta2 = model.addVars(drones, locations, vtype=GRB.CONTINUOUS, lb=0, name="t_arrive_a")

    # ts1[d,i] = USV leave位置i的时间。结果：t[0]...t[3]
    ts1 = model.addVars(usv, locations, vtype=GRB.CONTINUOUS, lb=0, name="t_leave_s")
    # ts2 arrive
    ts2 = model.addVars(usv, locations, vtype=GRB.CONTINUOUS, lb=0, name="t_arrive_s")

    # 辅助变量 max_time
    max_time = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name="max_time")

    # 4. 定义约束条件
    # 4.1 从depot（除终点，这里以返回仓库为终点）
    for d in drones:
        # 无人机只能从depot离开一次
        model.addConstr(gp.quicksum(x1[d, 0, j] for j in locations if j != 0) <= 1,
                        name=f"drone{d}_leave_depot"
                        )
        # 无人机离开depot次数=回到次数
        model.addConstr(gp.quicksum(x1[d, i, 0] for i in locations if i != 0) ==
                        gp.quicksum(x1[d, 0, j] for j in locations if j != 0),
                        name=f"drone_{d}_return_depot"
                        )
    for k in usv:
        # 无人船只能从depot离开一次
        model.addConstr(gp.quicksum(x2[k, 0, j] for j in locations if j != 0) <= 1,
                        name=f"USV_{k}_leave_depot"
                        )
        # 无人船离开depot次数=回到次数
        model.addConstr(gp.quicksum(x2[k, i, 0] for i in locations if i != 0) ==
                        gp.quicksum(x2[k, 0, j] for j in locations if j != 0),
                        name=f"USV_{k}_return_depot"
                        )

    # 4.2 每个节点j必须被访问一次（除起点）
    for j in locations:
        if j != 0:
            visit_in = (gp.quicksum(x1[d, i, j] for d in drones for i in locations if i != j) +
                        gp.quicksum(x2[k, i, j] for k in usv for i in locations if i != j))
            model.addConstr(visit_in == 1, name=f"visit_once{j}")

    # 4.3 节点i离开=到达
    for d in drones:
        for i in locations:
            if i != 0:
                model.addConstr(gp.quicksum(x1[d, i, j] for j in locations if i != j) ==
                                gp.quicksum(x1[d, j, i] for j in locations if i != j),
                                name=f"node_{i}_flow_d")
    for k in usv:
        for i in locations:
            if i != 0:
                model.addConstr(gp.quicksum(x2[k, i, j] for j in locations if i != j) ==
                                gp.quicksum(x2[k, j, i] for j in locations if i != j),
                                name=f"node_{i}_flow_k")

    # 4.4 时间逻辑约束
    M = 1000  # 大M常数，用于线性化

    # 无人机到达j>=离开i+ij
    for d in drones:
        for i in locations:
            for j in locations:
                if j != i:
                    model.addConstr(ta2[d, j] >= ta1[d, i] + travel_time_d[i, j] * x1[d, i, j] - M * (1 - x1[d, i, j]),
                                    name=f"arrive_{j}_{d}")
    # 无人船到达j>=离开i+ij
    for k in usv:
        for i in locations:
            for j in locations:
                if j != i:
                    model.addConstr(ts2[k, j] >= ts1[k, i] + travel_time_k[i, j] * x2[k, i, j] - M * (1 - x2[k, i, j]),
                                    name=f"arrive_{j}_{k}")

    # 无人机离开i>=i任务开始+服务
    # 无人机离开i>=到达+服务
    for d in drones:
        for i in locations:
            if i != 0:
                model.addConstr(ta1[d, i] >= time_windows[i][0] + service_time.get(i, 0),
                                name=f"leave_uav_{i}_{d}")
                model.addConstr(ta1[d, i] >= ta2[d, i] + service_time.get(i, 0),
                                name=f"leave_uav_{i}_{d}_2")
            if i == 0:
                for j in locations:
                    if j != 0:
                        # 离开depot>=0
                        model.addConstr(ta1[d, i] >= 0, name=f"leave_depot_uav_{d}")
                        # 到达depot>=离开j+ij
                        model.addConstr(ta2[d, i] >= ta1[d, j] + travel_time_d[j, i]
                                        - M * (1 - x1[d, j, i]), name=f"return_depot_uav_{d}")  # 改！！！

    for k in usv:
        for i in locations:
            if i != 0:
                model.addConstr(ts1[k, i] >= time_windows[i][0] + service_time.get(i, 0),
                                name=f"leave_usv_{i}_{k}")
                model.addConstr(ts1[k, i] >= ts2[k, i] + service_time.get(i, 0),
                                name=f"leave_usv_{i}_{k}_2")
            if i == 0:
                for j in locations:
                    if j != 0:
                        # 离开depot>=0
                        model.addConstr(ts1[k, i] >= 0, name=f"leave_depot_usv_{k}")
                        # 到达depot>=离开j+ij
                        model.addConstr(ts2[k, i] >= ts1[k, j] + travel_time_k[j, i]
                                        - M * (1 - x2[k, j, i]), name=f"return_depot_usv_{k}")  # 改！！！

    # 到达时间必须早于时间窗
    for d in drones:
        for i in locations:
            if i != 0:
                model.addConstr(ta2[d, i] <= time_windows[i][1], name=f"drone_{d}_tw_low_{i}")  # 严格要求到达时间大于时间窗下界 应优化

    for k in usv:
        for i in locations:
            if i != 0:
                model.addConstr(ts2[k, i] <= time_windows[i][1], name=f"USV_{k}_tw_low_{i}")

    # 4.5 最快回到depot的时间 大于等于每个无人机返回时间
    for d in drones:
        model.addConstr(max_time >= ta2[d, 0], name=f"max_time_{d}")
    for k in usv:
        model.addConstr(max_time >= ts2[k, 0], name=f"max_time_{k}")

    # 4.6 uav每次飞行不超过最大飞行时间

    for d in drones:
        model.addConstr(ta2[d, 0] - ta1[d, 0] <= flying_duration, name=f"{d}_flying_duration")

    # 4.6破解冗余性

    D = len(drones)
    used_d = model.addVars(D, vtype=GRB.BINARY, name="used_d")
    for d in range(D):
        model.addConstr(used_d[d] == gp.quicksum(x1[d, 0, i] for i in locations if i != 0), name=f"used_d_{d}")

    for d in range(D - 1):
        model.addConstr(used_d[d] >= used_d[d + 1], name=f"priority_dispatch_{d}")

    M = 1e5
    for d in range(D - 1):
        model.addConstr(ta2[d, 0] >= ta2[d + 1, 0] - M * (2 - used_d[d] - used_d[d + 1]), name=f"time_order_{d}")

    # 无人船
    K = len(usv)
    used_k = model.addVars(K, vtype=GRB.BINARY, name="used_k")
    for k in range(K):
        model.addConstr(used_k[k] == gp.quicksum(x2[k, 0, i] for i in locations if i != 0), name=f"used_k_{k}")

    for k in range(K - 1):
        model.addConstr(used_k[k] >= used_k[k + 1], name=f"priority_dispatch_{k}")

    M = 1e5
    for k in range(K - 1):
        model.addConstr(ts2[k, 0] >= ts2[k + 1, 0] - M * (2 - used_k[k] - used_k[k + 1]), name=f"time_order_{k}")

    # 5. 设置目标函数：最小化总配送时间（返回仓库的时间）
    total_time = gp.quicksum(ta2[d, 0] for d in drones) + gp.quicksum(ts2[k, 0] for k in usv)
    model.setObjective(total_time, GRB.MINIMIZE)

    # 6. 求解模型
    model.optimize()

    # 7. 输出结果
    if model.status == GRB.OPTIMAL:
        print("-" * 100)
        # 最晚到达时间
        print(f"最优路径总时间: {model.objVal:.2f} 分钟")
        print(f"最晚回到仓库时间:{max_time.X}")

        def extract_route(xvar, vehicle, nodes, tol=1e-6):
            used = sum(xvar.get((vehicle, 0, j), None).X if xvar.get((vehicle, 0, j), None) else 0.0 for j in nodes if
                       j != 0) > 0.5
            if not used:
                return [0], False
            route = [0]
            current = 0
            max_steps = len(nodes) + 5
            for _ in range(max_steps):
                next_node = None
                for j in nodes:
                    if j != current:
                        arc = xvar.get((vehicle, current, j), None)
                        if arc is not None and arc.X > 0.5 - tol:
                            next_node = j
                            break
                if next_node is None:
                    if current != 0:
                        back_arc = xvar.get((vehicle, current, 0), None)
                        if back_arc is not None and back_arc.X > 0.5 - tol:
                            route.append(0)
                            return route, True
                    break
                route.append(next_node)
                current = next_node
                if current == 0:
                    break
            return route, True

        routes = {}
        for d in drones:
            route, used = extract_route(x1, d, locations)
            if used:
                routes[f"无人机{d}"] = route
                print(f"\n无人机{d}配送路线: {' → '.join(map(str, route))}")
        for k in usv:
            route, used = extract_route(x2, k, locations)
            if used:
                routes[f"无人船{k}"] = route
                print(f"\n无人船{k}配送路线: {' → '.join(map(str, route))}")

        # 绘图
        plt.figure(figsize=(12, 8))
        colors = ['r', 'g', 'b', 'c', 'm', 'y']
        # 画节点
        for node, (x, y) in coordinates.items():
            plt.plot(x, y, 'ko')
            plt.text(x + 0.5, y + 0.5, str(node), fontsize=9)
        # 画路径
        for idx, (vehicle, route) in enumerate(routes.items()):
            xs = [coordinates[n][0] for n in route]
            ys = [coordinates[n][1] for n in route]
            plt.plot(xs, ys, marker='o', color=colors[idx % len(colors)], label=vehicle)

        plt.title("route")
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.legend(loc='best', fontsize=10)
        plt.grid(True)
        plt.show()

        # 检查节点是否全部被访问1次
        print("\n各节点访问情况:")
        for j in locations:
            if j != 0:
                visit_sum = (sum(x1[d, i, j].X for d in drones for i in locations if i != j) +
                             sum(x2[k, i, j].X for k in usv for i in locations if i != j))
                print(f"节点 {j}: 被访问次数 = {visit_sum}")

        # 检查节点被哪个vehicle访问
        print("\n节点访问详情:")
        for j in locations:
            if j != 0:
                visiting_drones = []
                visiting_usv = []
                for d in drones:
                    for i in locations:
                        if i != j and x1[d, i, j].X > 0.5:
                            visiting_drones.append(d)
                for k in usv:
                    for i in locations:
                        if i != j and x2[k, i, j].X > 0.5:
                            visiting_usv.append(k)
                if visiting_drones:
                    print(f"节点 {j} 被无人机 {visiting_drones} 访问")
                elif visiting_usv:
                    print(f"节点 {j} 被无人船 {visiting_usv} 访问")
                else:
                    print(f"节点 {j} 未被访问")

        for var in model.getVars():
            if var.VarName.startswith("x1[") or var.VarName.startswith("x2["):
                print(var.VarName)


    else:
        print("未找到可行解，可能时间窗约束过紧")
        model.computeIIS()  # 计算不可行性来源
        model.write("conflict.ilp")  # 将冲突约束写入文件
        print("冲突约束已保存到 conflict.ilp，请检查该文件")

        for var in model.getVars():
            if var.VarName.startswith("x1[") or var.VarName.startswith("x2["):
                print(var.VarName)


if __name__ == "__main__":  # 被其他文件import（导入作为模块）时，不会执行这个代码（只在原代码文件中执行）
    minimize_cost()

"""
发现：
1.当无人机和无人船的cost接近时，由于无人船的耗时较高，路线偏向于选择无人机去服务节点
2.当无人机的cost略高于无人船时，没有明显的偏向
3.最小化运行成本和最小化运行时间的结果完全不同 最短时间是80min时 当设定了运行成本 时间将会达到100min或以上
4.增加了最大运行时间后，无人机可能为了减少在节点的等待时间而延迟从depot出发的时间 因此离开节点0的时间>0
  增大过多的话 可能导致无解？时间窗过于小 导致即使无人船也无法访问全部节点
"""