import math
import random
import copy
import matplotlib.pyplot as plt

# ================= 1. 全局数据定义 =================
locations = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
A_only_uav = list(range(1, 6))  # UAV Only: 1, 2, 3
S_only_usv = list(range(6, 8))  # USV Only: 4, 5, 6, 7
B_both = list(range(8, 12))  # Both: 8, 9, 10, 11
depot = 0
customers = A_only_uav + S_only_usv + B_both

# 车辆定义
drones = [0, 1, 2]  # 3 UAVs
usv = [0, 1]  # 3 USVs

coordinates = {
    0: (0, 0), 1: (20, 30), 2: (15, 40), 3: (40, 20),
    4: (25, 25), 5: (30, 35), 6: (35, 15), 7: (45, 30),
    8: (23, 29), 9: (20, 5), 10: (50, 34), 11: (34, 17),
}

drone_speed = 2.0
usv_speed = 1.0
flying_duration = 120

time_windows = {
    0: [0, 1000],
    1: [25, 90], 2: [0, 60], 3: [20, 90],
    4: [15, 80], 5: [15, 60], 6: [30, 70], 7: [0, 60],
    8: [25, 90], 9: [80, 130], 10: [40, 110], 11: [45, 95]
}

service_time = {
    1: 5, 2: 15, 3: 5, 4: 10, 5: 20, 6: 25, 7: 15,
    8: 20, 9: 5, 10: 30, 11: 15
}

# 预计算行驶时间矩阵
travel_time_d = {}
travel_time_k = {}


def euclidean_distance(coord1, coord2):
    return math.sqrt((coord1[0] - coord2[0]) ** 2 + (coord1[1] - coord2[1]) ** 2)


for i in locations:
    for j in locations:
        if i != j:
            dist = euclidean_distance(coordinates[i], coordinates[j])
            travel_time_d[(i, j)] = dist / drone_speed
            travel_time_k[(i, j)] = dist / usv_speed


# ================= 2. 核心辅助函数 =================

def get_travel_time(from_node, to_node, vehicle_type):
    """获取行驶时间"""
    if from_node == to_node: return 0
    if vehicle_type.startswith('uav'):
        return travel_time_d.get((from_node, to_node), float('inf'))
    else:
        return travel_time_k.get((from_node, to_node), float('inf'))


def calculate_route_cost(route, vehicle_type):
    """计算单条路线的成本（总行驶时间）"""
    cost = 0
    for i in range(len(route) - 1):
        cost += get_travel_time(route[i], route[i + 1], vehicle_type)
    return cost


def total_cost(routes):
    """计算所有车辆的总成本"""
    total = 0
    for v, r in routes.items():
        v_type = 'uav' if v.startswith('uav') else 'usv'
        total += calculate_route_cost(r, v_type)
    return total


def check_feasibility(route, vehicle_type):
    """
    严格检查路线可行性：
    1. 时间窗约束
    2. UAV 续航约束
    3. 必须以 0 开始和结束
    """
    if not route or route[0] != 0 or route[-1] != 0:
        return False

    current_time = 0
    for i in range(len(route) - 1):
        from_node = route[i]
        to_node = route[i + 1]

        t_travel = get_travel_time(from_node, to_node, vehicle_type)
        if t_travel == float('inf'): return False

        current_time += t_travel

        # 时间窗检查
        earliest, latest = time_windows[to_node]
        if current_time < earliest:
            current_time = earliest  # 等待
        if current_time > latest:
            return False  # 迟到，不可行

        # 服务时间
        current_time += service_time.get(to_node, 0)

        # UAV 续航检查 (仅在回到仓库或中间检查? 通常指总飞行时间不超过限制)
        # 这里假设 flying_duration 是单次任务的最大持续时间
        if vehicle_type.startswith('uav'):
            # 简单起见，检查从出发到当前的时间是否超过续航
            # 更严格的应该是累加飞行时间，但通常 VRPTW 中是指回到仓库的总时间
            pass

            # 最后检查回到仓库后的总时间是否满足 UAV 续航
    if vehicle_type.startswith('uav'):
        if current_time > flying_duration:
            return False

    return True


# ================= 3. ALNS 算子 =================

def initial_solution(drones, usv):
    """
    构建初始可行解。
    策略：对每个客户，寻找所有合法插入位置中成本增加最小的位置。
    如果找不到合法位置，重试随机顺序。
    """
    uav_vehicles = [f'uav{d}' for d in drones]
    usv_vehicles = [f'usv{k}' for k in usv]
    all_vehicles = uav_vehicles + usv_vehicles

    best_routes = None
    min_cost = float('inf')

    # 尝试多次以找到较好的初始解
    for attempt in range(500):
        routes = {v: [0, 0] for v in all_vehicles}
        temp_customers = customers[:]
        random.shuffle(temp_customers)

        is_feasible = True

        for customer in temp_customers:
            best_insert_v = None
            best_insert_idx = None
            min_added_cost = float('inf')

            # 确定可用车辆
            if customer in A_only_uav:
                candidates = uav_vehicles
            elif customer in S_only_usv:
                candidates = usv_vehicles
            else:
                candidates = all_vehicles

            found_pos = False

            for v in candidates:
                v_type = 'uav' if v.startswith('uav') else 'usv'
                rt = routes[v]

                # 尝试插入到 0 和 0 之间的所有位置
                # 范围: 1 到 len(rt)-1 (即在最后一个0之前插入)
                for i in range(1, len(rt)):
                    new_rt = rt[:i] + [customer] + rt[i:]

                    if check_feasibility(new_rt, v_type):
                        # 计算成本增量
                        old_cost = calculate_route_cost(rt, v_type)
                        new_cost = calculate_route_cost(new_rt, v_type)
                        added_cost = new_cost - old_cost

                        if added_cost < min_added_cost:
                            min_added_cost = added_cost
                            best_insert_v = v
                            best_insert_idx = i
                            found_pos = True

            if found_pos:
                rt = routes[best_insert_v]
                routes[best_insert_v] = rt[:best_insert_idx] + [customer] + rt[best_insert_idx:]
            else:
                is_feasible = False
                break  # 当前尝试失败，跳出客户循环

        if is_feasible:
            cost = total_cost(routes)
            if cost < min_cost:
                min_cost = cost
                best_routes = copy.deepcopy(routes)

    if best_routes is None:
        raise Exception("Could not generate a feasible initial solution. Constraints might be too tight.")

    return best_routes


def destroy(routes, num_remove=2):
    """随机移除节点"""
    new_routes = copy.deepcopy(routes)
    removed_nodes = []

    # 收集所有非仓库节点
    all_nodes_in_routes = []
    for v, r in new_routes.items():
        for i in range(1, len(r) - 1):  # 不包括首尾的0
            all_nodes_in_routes.append((v, i))

    if len(all_nodes_in_routes) < num_remove:
        return new_routes, []

    random.shuffle(all_nodes_in_routes)
    selected = all_nodes_in_routes[:num_remove]

    # 按索引降序排序，防止移除前面的元素影响后面元素的索引
    # 注意：不同车辆的索引互不影响，同车辆的才影响。
    # 简单做法：逐个移除，但需要重新获取索引，或者按车辆分组处理。
    # 这里采用更稳健的方法：先记录要移除的节点值，然后从副本中移除

    nodes_to_remove_vals = [new_routes[v][i] for v, i in selected]

    for node_val in nodes_to_remove_vals:
        for v in new_routes:
            if node_val in new_routes[v]:
                idx = new_routes[v].index(node_val)
                if 0 < idx < len(new_routes[v]) - 1:  # 确保不是仓库
                    new_routes[v].pop(idx)
                    removed_nodes.append(node_val)
                    break

    return new_routes, removed_nodes


def repair(routes, removed_nodes):
    """
    修复操作：将移除的节点重新插入。
    策略：寻找合法且成本增加最小的位置。
    """
    temp_routes = copy.deepcopy(routes)

    for node in removed_nodes:
        best_insert_v = None
        best_insert_idx = None
        min_added_cost = float('inf')

        if node in A_only_uav:
            candidates = [v for v in temp_routes if v.startswith('uav')]
        elif node in S_only_usv:
            candidates = [v for v in temp_routes if v.startswith('usv')]
        else:
            candidates = list(temp_routes.keys())

        found_pos = False

        for v in candidates:
            v_type = 'uav' if v.startswith('uav') else 'usv'
            rt = temp_routes[v]

            for i in range(1, len(rt)):
                new_rt = rt[:i] + [node] + rt[i:]
                if check_feasibility(new_rt, v_type):
                    old_cost = calculate_route_cost(rt, v_type)
                    new_cost = calculate_route_cost(new_rt, v_type)
                    added_cost = new_cost - old_cost

                    if added_cost < min_added_cost:
                        min_added_cost = added_cost
                        best_insert_v = v
                        best_insert_idx = i
                        found_pos = True

        if found_pos:
            rt = temp_routes[best_insert_v]
            temp_routes[best_insert_v] = rt[:best_insert_idx] + [node] + rt[best_insert_idx:]
        else:
            # 如果实在找不到合法位置，为了保持解的完整性，强行插入到最短路径
            # 但这会导致解不可行。在严格模式下，我们应该保留原状或报错。
            # 这里为了程序不崩，选择跳过该节点（这会导致节点丢失，但在ALNS中通常会通过多次迭代找回）
            # 更好的做法：允许轻微违反，这里暂不实现复杂惩罚函数
            pass

    return temp_routes


def alns(drones, usv, max_iter=5000):
    print("Generating initial solution...")
    current_solution = initial_solution(drones, usv)
    current_cost = total_cost(current_solution)

    best_solution = copy.deepcopy(current_solution)
    best_cost = current_cost

    T = 100.0
    alpha = 0.99

    print("Starting ALNS optimization...")
    for iter in range(max_iter):
        # 1. Destroy
        destroyed_sol, removed = destroy(current_solution, num_remove=2)

        # 2. Repair
        new_solution = repair(destroyed_sol, removed)

        # 检查新解是否完整（防止节点丢失）
        all_nodes_in_new = []
        for r in new_solution.values():
            all_nodes_in_new.extend(r)
        if set(customers).issubset(set(all_nodes_in_new)):
            new_cost = total_cost(new_solution)

            # 3. Acceptance Criterion
            delta = new_cost - current_cost
            if delta < 0 or random.random() < math.exp(-delta / T):
                current_solution = new_solution
                current_cost = new_cost

                if new_cost < best_cost:
                    best_solution = copy.deepcopy(new_solution)
                    best_cost = new_cost
                    # print(f"New Best Found at Iter {iter}: {best_cost:.2f}")

        T *= alpha

        if iter % 1000 == 0:
            print(f"Iter {iter}, Best Cost: {best_cost:.2f}")

    return best_solution, best_cost


# ================= 4. 结果展示与绘图 =================

def plot_results(best_routes):
    plt.figure(figsize=(12, 9))

    # 1. 绘制节点，区分类型
    # Depot
    plt.plot(coordinates[0][0], coordinates[0][1], 'k*', markersize=15, label='Depot', zorder=5)

    # A_only_uav (Red Triangle)
    xs_a = [coordinates[n][0] for n in A_only_uav]
    ys_a = [coordinates[n][1] for n in A_only_uav]
    plt.scatter(xs_a, ys_a, c='red', marker='^', s=100, label='UAV Only Nodes', zorder=4)

    # S_only_usv (Blue Circle)
    xs_s = [coordinates[n][0] for n in S_only_usv]
    ys_s = [coordinates[n][1] for n in S_only_usv]
    plt.scatter(xs_s, ys_s, c='blue', marker='o', s=100, label='USV Only Nodes', zorder=4)

    # B_both (Green Diamond)
    xs_b = [coordinates[n][0] for n in B_both]
    ys_b = [coordinates[n][1] for n in B_both]
    plt.scatter(xs_b, ys_b, c='green', marker='D', s=100, label='Shared Nodes', zorder=4)

    # 添加节点标签
    for node, (x, y) in coordinates.items():
        plt.text(x + 1.5, y + 1.5, str(node), fontsize=9, ha='center')

    # 2. 绘制路径
    colors = ['orange', 'purple', 'brown', 'cyan', 'magenta', 'lime']
    line_styles = ['-', '--']  # UAV solid, USV dashed? Or just different colors

    for idx, (vehicle, route) in enumerate(best_routes.items()):
        xs = [coordinates[n][0] for n in route]
        ys = [coordinates[n][1] for n in route]

        color = colors[idx % len(colors)]
        # UAV 用实线，USV 用虚线，以便区分车辆类型
        linestyle = '-' if vehicle.startswith('uav') else '--'
        linewidth = 2 if vehicle.startswith('uav') else 1.5

        plt.plot(xs, ys, color=color, linestyle=linestyle, linewidth=linewidth, label=f'{vehicle}', zorder=1)

        # 绘制方向箭头 (可选，简化起见省略，依靠线条连接)

    plt.title("ALNS Optimized Routes (Distinct Node Types & Vehicle Paths)", fontsize=14)
    plt.xlabel("X Coordinate")
    plt.ylabel("Y Coordinate")
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.show()


def print_details(best_routes):
    print("\n--- Detailed Route Schedule & Time Window Verification ---")

    all_visited_nodes = set()

    for vehicle, route in best_routes.items():
        v_type = 'uav' if vehicle.startswith('uav') else 'usv'
        cost = calculate_route_cost(route, v_type)

        print(f"\nVehicle: {vehicle} (Type: {v_type.upper()})")
        print(f"Route: {' -> '.join(map(str, route))}")
        print(f"Total Travel Cost: {cost:.2f}")
        print(
            f"{'Node':<6} | {'Arrival':<10} | {'Wait':<10} | {'Start Service':<12} | {'Departure':<10} | {'Time Window':<15} | {'Status'}")
        print("-" * 90)

        current_time = 0.0
        is_route_valid = True

        # 遍历路径中的每一段
        for i in range(len(route) - 1):
            from_node = route[i]
            to_node = route[i + 1]

            # 1. 行驶
            travel_t = get_travel_time(from_node, to_node, v_type)
            arrival_time = current_time + travel_t

            # 2. 检查时间窗
            earliest, latest = time_windows[to_node]

            # 等待时间
            wait_time = 0.0
            if arrival_time < earliest:
                wait_time = earliest - arrival_time
                start_service = earliest
            else:
                start_service = arrival_time

            # 3. 服务与离开
            svc_time = service_time.get(to_node, 0)
            departure_time = start_service + svc_time

            # 更新当前时间为离开时间，用于下一段计算
            current_time = departure_time

            # 4. 状态判断
            status = "OK"
            if to_node != 0:  # 仓库节点通常不检查迟到，只检查最终返回时间
                if arrival_time > latest:
                    status = "LATE (Violates TW)"
                    is_route_valid = False
                elif start_service > latest:  # 理论上不会发生，因为如果arrival>latest已经捕获
                    status = "LATE"
                    is_route_valid = False

            # 记录访问过的非仓库节点
            if to_node != 0:
                all_visited_nodes.add(to_node)

            # 打印该行信息 (仓库节点简化显示)
            if to_node == 0:
                print(
                    f"{to_node:<6} | {arrival_time:<10.2f} | {'-':<10} | {'-':<12} | {departure_time:<10.2f} | {'End of Route':<15} | {'Return'}")
            else:
                tw_str = f"[{earliest}, {latest}]"
                print(
                    f"{to_node:<6} | {arrival_time:<10.2f} | {wait_time:<10.2f} | {start_service:<12.2f} | {departure_time:<10.2f} | {tw_str:<15} | {status}")

        # 5. UAV 续航最终检查
        if v_type == 'uav':
            if current_time > flying_duration:
                print(f"\n*** WARNING: UAV {vehicle} violates flying duration constraint! "
                      f"Total time {current_time:.2f} > Limit {flying_duration} ***")
                is_route_valid = False
            else:
                print(f"\nUAV Duration Check: {current_time:.2f} / {flying_duration} (OK)")

        if is_route_valid and v_type != 'uav':  # USV 没有额外的续航打印
            print(f"Route Feasibility: VALID")
        elif not is_route_valid:
            print(f"Route Feasibility: INVALID")

    # 全局节点覆盖检查
    print("\n--- Global Coverage Check ---")
    missing = set(customers) - all_visited_nodes
    if missing:
        print(f"ERROR: The following nodes were NOT visited by any vehicle: {sorted(list(missing))}")
    else:
        print("SUCCESS: All customer nodes are visited exactly once (or more).")


if __name__ == "__main__":
    # 运行 ALNS
    best_routes, best_cost = alns(drones, usv, max_iter=5000)

    # 打印详情
    print_details(best_routes)

    # 绘图
    plot_results(best_routes)