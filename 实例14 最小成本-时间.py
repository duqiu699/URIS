import gurobipy as gp
from gurobipy import GRB


def minimize_cost():      #当一段逻辑 “可能重复调用” 或 “代码超过 50 行、步骤分 3 步以上” 时，建议写函数

    # 1. 定义问题数据                    #大规模问题无需全部列举 可以优化
    locations = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]           # 配送点：0表示起点（仓库），1-3表示客户
    drones = [0, 1, 2, 3, 4]                   #两个无人机
    usv = [0]
    travel_time_d = {

        (0, 1): 25, (0, 2): 18, (0, 3): 32, (0, 4): 10, (0, 5): 38, (0, 6): 22, (0, 7): 40, (0, 8): 15, (0, 9): 28,
        (0, 10): 35, (0, 11): 12, (0, 12): 30, (0, 13): 19, (0, 14): 37, (0, 15): 21,
        # 从节点1到其他节点
        (1, 0): 25, (1, 2): 10, (1, 3): 36, (1, 4): 29, (1, 5): 16, (1, 6): 39, (1, 7): 23, (1, 8): 31, (1, 9): 17,
        (1, 10): 34, (1, 11): 20, (1, 12): 38, (1, 13): 19, (1, 14): 30, (1, 15): 26,
        # 从节点2到其他节点
        (2, 0): 18, (2, 1): 10, (2, 3): 22, (2, 4): 37, (2, 5): 19, (2, 6): 33, (2, 7): 28, (2, 8): 14, (2, 9): 39,
        (2, 10): 24, (2, 11): 31, (2, 12): 16, (2, 13): 35, (2, 14): 21, (2, 15): 40,
        # 从节点3到其他节点
        (3, 0): 32, (3, 1): 36, (3, 2): 22, (3, 4): 10, (3, 5): 38, (3, 6): 25, (3, 7): 18, (3, 8): 34, (3, 9): 21,
        (3, 10): 30, (3, 11): 15, (3, 12): 37, (3, 13): 29, (3, 14): 19, (3, 15): 33,
        # 从节点4到其他节点
        (4, 0): 10, (4, 1): 29, (4, 2): 37, (4, 3): 10, (4, 5): 24, (4, 6): 31, (4, 7): 16, (4, 8): 39, (4, 9): 20,
        (4, 10): 35, (4, 11): 26, (4, 12): 13, (4, 13): 38, (4, 14): 22, (4, 15): 33,
        # 从节点5到其他节点
        (5, 0): 38, (5, 1): 16, (5, 2): 19, (5, 3): 38, (5, 4): 24, (5, 6): 10, (5, 7): 36, (5, 8): 21, (5, 9): 32,
        (5, 10): 17, (5, 11): 30, (5, 12): 25, (5, 13): 14, (5, 14): 39, (5, 15): 27,
        # 从节点6到其他节点
        (6, 0): 22, (6, 1): 39, (6, 2): 33, (6, 3): 25, (6, 4): 31, (6, 5): 10, (6, 7): 29, (6, 8): 15, (6, 9): 37,
        (6, 10): 23, (6, 11): 40, (6, 12): 19, (6, 13): 35, (6, 14): 26, (6, 15): 16,
        # 从节点7到其他节点
        (7, 0): 40, (7, 1): 23, (7, 2): 28, (7, 3): 18, (7, 4): 16, (7, 5): 36, (7, 6): 29, (7, 8): 33, (7, 9): 10,
        (7, 10): 38, (7, 11): 24, (7, 12): 31, (7, 13): 17, (7, 14): 35, (7, 15): 20,
        # 从节点8到其他节点
        (8, 0): 15, (8, 1): 31, (8, 2): 14, (8, 3): 34, (8, 4): 39, (8, 5): 21, (8, 6): 15, (8, 7): 33, (8, 9): 27,
        (8, 10): 10, (8, 11): 36, (8, 12): 22, (8, 13): 38, (8, 14): 19, (8, 15): 30,
        # 从节点9到其他节点
        (9, 0): 28, (9, 1): 17, (9, 2): 39, (9, 3): 21, (9, 4): 20, (9, 5): 32, (9, 6): 37, (9, 7): 10, (9, 8): 27,
        (9, 10): 34, (9, 11): 16, (9, 12): 31, (9, 13): 23, (9, 14): 40, (9, 15): 19,
        # 从节点10到其他节点
        (10, 0): 35, (10, 1): 34, (10, 2): 24, (10, 3): 30, (10, 4): 35, (10, 5): 17, (10, 6): 23, (10, 7): 38,
        (10, 8): 10, (10, 9): 34, (10, 11): 29, (10, 12): 15, (10, 13): 36, (10, 14): 21, (10, 15): 39,

        # 从节点11到其他节点
        (11, 0): 12, (11, 1): 20, (11, 2): 31, (11, 3): 15, (11, 4): 26, (11, 5): 30, (11, 6): 40, (11, 7): 24,
        (11, 8): 36, (11, 9): 16, (11, 10): 29, (11, 12): 10, (11, 13): 33, (11, 14): 27, (11, 15): 38,
        # 从节点12到其他节点
        (12, 0): 30, (12, 1): 38, (12, 2): 16, (12, 3): 37, (12, 4): 13, (12, 5): 25, (12, 6): 19, (12, 7): 31,
        (12, 8): 22, (12, 9): 31, (12, 10): 15, (12, 11): 10, (12, 13): 39, (12, 14): 23, (12, 15): 34,
        # 从节点13到其他节点
        (13, 0): 19, (13, 1): 19, (13, 2): 35, (13, 3): 29, (13, 4): 38, (13, 5): 14, (13, 6): 35, (13, 7): 17,
        (13, 8): 38, (13, 9): 23, (13, 10): 36, (13, 11): 33, (13, 12): 39, (13, 14): 10, (13, 15): 32,
        # 从节点14到其他节点
        (14, 0): 37, (14, 1): 30, (14, 2): 21, (14, 3): 19, (14, 4): 22, (14, 5): 39, (14, 6): 26, (14, 7): 35,
        (14, 8): 19, (14, 9): 40, (14, 10): 21, (14, 11): 27, (14, 12): 23, (14, 13): 10, (14, 15): 36,
        # 从节点15到其他节点
        (15, 0): 21, (15, 1): 26, (15, 2): 40, (15, 3): 33, (15, 4): 33, (15, 5): 27, (15, 6): 16, (15, 7): 20,
        (15, 8): 30, (15, 9): 19, (15, 10): 39, (15, 11): 38, (15, 12): 34, (15, 13): 32, (15, 14): 36
    }


    travel_time_k = {k: v*2 for k, v in travel_time_d.items()}

    time_windows = {                   # 客户时间窗 [最早可送达时间, 最晚必须送达时间]（分钟）
        0: [0, 1000],                     # 起点（仓库）：必须在0时刻出发
        1: [25, 90],                   # 客户1：最早10点，最晚30点送达
        2: [0, 60],                   # 客户2：最早20点，最晚50点送达
        3: [20, 90],                   # 客户3：最早15点，最晚40点送达
        4: [15, 80],
        5: [15, 60],
        6: [30, 70],
        7: [0, 60],
        8: [25, 90],
        9: [80, 130],
        10: [40, 110],
        11: [45, 95],
        12: [90, 160],
        13: [110, 160],
        14: [150, 200],
        15: [110, 280]
    }
    service_time = {1: 5, 2: 15, 3: 5, 4: 10, 5: 20, 6: 25, 7: 15, 8: 20, 9: 5, 10: 30,
                    11: 15, 12: 20, 13: 20, 14: 5, 15: 15
                    }  # 每个客户的服务时间（分钟）
    drones_cost = 8
    usv_cost = 10
    flying_duration = 120

    # 2. 创建模型
    model = gp.Model("TwoDronesVRTPW")

    # 3. 定义变量
    # x[d,i,j] = 1 表示无人机d从位置i直接前往位置j，0表示不走该弧
    x1 = model.addVars(drones, [(i,j) for i in locations for j in locations if i != j], vtype=GRB.BINARY, name="x")  #locations:[0,1,2,3]
    x2 = model.addVars(usv, [(i,j) for i in locations for j in locations if i != j], vtype=GRB.BINARY, name="x")

    # ta1[d,i] = 无人机d leave位置i的时间。结果：t[0]...t[3]
    ta1 = model.addVars(drones, locations, vtype=GRB.CONTINUOUS, lb=0, name="t_leave_a")
    # ta2 arrive
    ta2 = model.addVars(drones, locations, vtype=GRB.CONTINUOUS, lb=0, name="t_arrive_a")

    # ts1[d,i] = USV leave位置i的时间。结果：t[0]...t[3]
    ts1 = model.addVars(usv, locations, vtype=GRB.CONTINUOUS, lb=0, name="t_leave_s")
    # ts2 arrive
    ts2 = model.addVars(usv, locations, vtype=GRB.CONTINUOUS, lb=0, name="t_arrive_s")

    #辅助变量 max_time
    max_time = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name="max_time")

    # 4. 定义约束条件
    # 4.1 从depot（除终点，这里以返回仓库为终点）
    for d in drones:
       #无人机只能从depot离开一次
        model.addConstr(gp.quicksum(x1[d, 0, j]for j in locations if j != 0) <= 1,
                        name = f"drone{d}_leave_depot"
        )
       #无人机离开depot次数=回到次数
        model.addConstr(gp.quicksum(x1[d, i, 0]for i in locations if i != 0) ==
                        gp.quicksum(x1[d, 0, j]for j in locations if j != 0),
                            name = f"drone_{d}_return_depot"
                        )
    for k in usv:
        #无人船只能从depot离开一次
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
                model.addConstr(gp.quicksum(x1[d, i, j]for j in locations if i != j) ==
                            gp.quicksum(x1[d, j, i]for j in locations if i != j),
                            name=f"node_{i}_flow_d")
    for k in usv:
        for i in locations:
            if i != 0:
                model.addConstr(gp.quicksum(x2[k, i, j]for j in locations if i != j) ==
                            gp.quicksum(x2[k, j, i]for j in locations if i != j),
                            name=f"node_{i}_flow_k")


    # 4.4 时间逻辑约束
    M = 1000  # 大M常数，用于线性化

    #无人机到达j>=离开i+ij
    for d in drones:
        for i in locations:
            for j in locations:
                if j != i:
                    model.addConstr(ta2[d, j] >= ta1[d, i] + travel_time_d[i, j] * x1[d, i, j]- M * (1 - x1[d, i, j]),
                                    name=f"arrive_{j}_{d}")
    #无人船到达j>=离开i+ij
    for k in usv:
        for i in locations:
            for j in locations:
                if j != i:
                    model.addConstr(ts2[k, j] >= ts1[k, i] + travel_time_k[i, j] * x2[k, i, j]- M * (1 - x2[k, i, j]),
                                    name=f"arrive_{j}_{k}")

    #无人机离开i>=i任务开始+服务
    #无人机离开i>=到达+服务
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
                        #到达depot>=离开j+ij
                        model.addConstr(ta2[d, i] >= ta1[d, j] + travel_time_d[j, i]
                                            - M * (1 - x1[d, j, i]), name=f"return_depot_uav_{d}")#改！！！


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
                        #离开depot>=0
                        model.addConstr(ts1[k, i] >= 0, name=f"leave_depot_usv_{k}")
                        #到达depot>=离开j+ij
                        model.addConstr(ts2[k, i] >= ts1[k, j] + travel_time_k[j, i]
                                            - M * (1 - x2[k, j, i]), name=f"return_depot_usv_{k}")#改！！！


    # 到达时间必须早于时间窗
    for d in drones:
        for i in locations:
            if i != 0:
                model.addConstr(ta2[d, i] <= time_windows[i][1], name=f"drone_{d}_tw_low_{i}")  #严格要求到达时间大于时间窗下界 应优化

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
    cost_drones = gp.quicksum(drones_cost * travel_time_d[i, j] * x1[d, i, j]
                              for d in drones for i in locations for j in locations if i != j)
    cost_usv = gp.quicksum(usv_cost * travel_time_k[i, j] * x2[k, i, j]
                           for k in usv for i in locations for j in locations if i != j)

    model.setObjective(cost_drones + cost_usv, GRB.MINIMIZE)


    # 6. 求解模型
    model.optimize()
    optimal_cost = model.objVal

    # 7. 输出结果
    if model.status == GRB.OPTIMAL:
        print("-"*100)
        #最小配送成本
        print(f"最优配送成本: {model.objVal:.2f} HKD")
        print('-'*50)


    # 8. 求解二阶段模型

    model.addConstr(cost_drones + cost_usv <= optimal_cost + 1e-6)
    model.setObjective(max_time, GRB.MINIMIZE)
    model.optimize()



    # 9. 输出结果
    if model.status == GRB.OPTIMAL:
        print("-"*100)
        #最晚到达时间
        print(f"最晚回到仓库时间: {model.objVal:.2f} 分钟")

        #定义函数：使输出结果为从depot到depot的路线环
        def extract_route_from_depot(xvar, vehicle, nodes, tol=1e-6):
            used = sum(
                xvar.get((vehicle, 0, j), None).X if xvar.get((vehicle, 0, j), None) else 0.0
                for j in nodes if j != 0
            ) > 0.5
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
                route.append(next_node)
                current = next_node
                if current == 0:
                    return route, True
            return route, True


        #输出无人机路线结果
        for d in drones:
            route, used = extract_route_from_depot(x1, d, locations)
            print(f"\n无人机{d}配送路线:")
            print(" → ".join(map(str, route)))
            if used:
                print(f"无人机{d}的到达时间：")
                for i in route:
                    print(f"位置 {i}到达：{ta2[d, i].X:.2f} 分钟")
                    print(f"位置 {i}离开：{ta1[d, i].X:.2f} 分钟")

        # 输出无人船路线结果
        for k in usv:
            route, used = extract_route_from_depot(x2, k, locations)
            print(f"\n无人船{k}配送路线:")
            print(' → '.join(map(str, route)))

            if used:
                print(f"无人船{k}的到达时间：")
                for i in route:
                    print(f"位置 {i}到达：{ts2[k, i].X:.2f} 分钟")
                    print(f"位置 {i}离开：{ts1[k, i].X:.2f} 分钟")


        #检查节点是否全部被访问1次
        print("\n各节点访问情况:")
        for j in locations:
            if j != 0:
                visit_sum = (sum(x1[d, i, j].X for d in drones for i in locations if i != j) +
                             sum(x2[k, i, j].X for k in usv for i in locations if i != j))
                print(f"节点 {j}: 被访问次数 = {visit_sum}")

        #检查节点被哪个vehicle访问
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








if __name__ == "__main__":        #被其他文件import（导入作为模块）时，不会执行这个代码（只在原代码文件中执行）
    minimize_cost()



"""
发现：
1.当无人机和无人船的cost接近时，由于无人船的耗时较高，路线偏向于选择无人机去服务节点
2.当无人机的cost略高于无人船时，没有明显的偏向
3.最小化运行成本和最小化运行时间的结果完全不同 最短时间是80min时 当设定了运行成本 时间将会达到100min或以上
4.增加了最大运行时间后，无人机可能为了减少在节点的等待时间而延迟从depot出发的时间 因此离开节点0的时间>0
  增大过多的话 可能导致无解？时间窗过于小 导致即使无人船也无法访问全部节点
"""