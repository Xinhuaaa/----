import math
import random
from itertools import permutations
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# 设置matplotlib以支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体
plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题

def calculate_distance(pos1, pos2):
    """计算两个坐标点之间的欧几里得距离"""
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

def calculate_total_cost(pickup_order, task_mapping, shelf_access_points, shelf_to_access_point_map, delivery_zones, start_pos, rotation_cost, unassigned_shelf):
    """为一个给定的揽收/派送顺序计算总行程成本。"""
    # 按照两层LIFO逻辑计算派送顺序
    delivery_order_shelves = get_two_layer_lifo_order(pickup_order)
    
    # --- 计算揽收成本 ---
    current_pos = start_pos
    pickup_cost = 0
    last_physical_pos = start_pos
    for shelf in pickup_order:
        access_point_name = shelf_to_access_point_map[shelf]
        access_point_pos = shelf_access_points[access_point_name]
        if access_point_pos != last_physical_pos:
            pickup_cost += calculate_distance(last_physical_pos, access_point_pos)
            last_physical_pos = access_point_pos
    current_pos = last_physical_pos

    # --- 计算派送成本 ---
    delivery_cost = 0
    previous_zone_name = None
    for shelf in delivery_order_shelves:
        if shelf == unassigned_shelf:
            continue
        target_zone_name = task_mapping[shelf]
        target_pos = delivery_zones[target_zone_name]
        delivery_cost += calculate_distance(current_pos, target_pos)
        current_pos = target_pos
        is_target_rotation_zone = target_zone_name in ['区域_a', '区域_f']
        was_previous_rotation_zone = previous_zone_name in ['区域_a', '区域_f']
        if is_target_rotation_zone and not was_previous_rotation_zone:
            delivery_cost += rotation_cost
        previous_zone_name = target_zone_name
            
    # --- 计算到达B区的成本 ---
    # 如果当前位置x坐标已经小于2000，则不需要移动
    if current_pos[0] >= 2000:
        # 直接向左移动到x=1999的位置
        b_zone_pos = (1999, current_pos[1])
        final_travel_cost = calculate_distance(current_pos, b_zone_pos)
    else:
        final_travel_cost = 0
    
    return pickup_cost + delivery_cost + final_travel_cost

def calculate_total_cost_with_optimization(pickup_order, task_mapping, shelf_access_points, shelf_to_access_point_map, delivery_zones, start_pos, rotation_cost, unassigned_shelf):
    """使用优化的派送顺序计算总成本"""
    # 使用优化的派送顺序
    delivery_order_shelves = calculate_optimized_delivery_order(pickup_order, task_mapping, unassigned_shelf)
    
    # --- 计算揽收成本 ---
    current_pos = start_pos
    pickup_cost = 0
    last_physical_pos = start_pos
    for shelf in pickup_order:
        access_point_name = shelf_to_access_point_map[shelf]
        access_point_pos = shelf_access_points[access_point_name]
        if access_point_pos != last_physical_pos:
            pickup_cost += calculate_distance(last_physical_pos, access_point_pos)
            last_physical_pos = access_point_pos
    current_pos = last_physical_pos

    # --- 计算派送成本 ---
    delivery_cost = 0
    previous_zone_name = None
    for shelf in delivery_order_shelves:
        if shelf == unassigned_shelf:
            continue
        target_zone_name = task_mapping[shelf]
        target_pos = delivery_zones[target_zone_name]
        delivery_cost += calculate_distance(current_pos, target_pos)
        current_pos = target_pos
        is_target_rotation_zone = target_zone_name in ['区域_a', '区域_f']
        was_previous_rotation_zone = previous_zone_name in ['区域_a', '区域_f']
        if is_target_rotation_zone and not was_previous_rotation_zone:
            delivery_cost += rotation_cost
        previous_zone_name = target_zone_name
            
    # --- 计算到达B区的成本 ---
    if current_pos[0] >= 2000:
        b_zone_pos = (1999, current_pos[1])
        final_travel_cost = calculate_distance(current_pos, b_zone_pos)
    else:
        final_travel_cost = 0
    
    return pickup_cost + delivery_cost + final_travel_cost

def get_path_coordinates(pickup_order, task_mapping, shelf_access_points, shelf_to_access_point_map, delivery_zones, start_pos, unassigned_shelf):
    """根据一个揽收顺序，生成完整的路径坐标点列表，用于绘图"""
    path_coords = [start_pos]
    
    # 揽收路径
    last_physical_pos = start_pos
    for shelf in pickup_order:
        access_point_name = shelf_to_access_point_map[shelf]
        access_point_pos = shelf_access_points[access_point_name]
        if access_point_pos != last_physical_pos:
            path_coords.append(access_point_pos)
            last_physical_pos = access_point_pos
    
    # 派送路径 - 使用两层LIFO逻辑
    delivery_order_shelves = get_two_layer_lifo_order(pickup_order)
    current_pos = last_physical_pos
    for shelf in delivery_order_shelves:
        if shelf == unassigned_shelf:
            # 码垛任务，位置不变，复制上一个点
            path_coords.append(path_coords[-1])
            continue
        target_zone_name = task_mapping[shelf]
        target_pos = delivery_zones[target_zone_name]
        path_coords.append(target_pos)
        current_pos = target_pos

    # 到达B区的路径
    if current_pos[0] >= 2000:
        # 直接向左移动到x=1999的位置
        b_zone_pos = (1999, current_pos[1])
        path_coords.append(b_zone_pos)

    return path_coords

def visualize_paths(optimal_path_coords, fixed_path_coords, shelf_locs, delivery_zones, start_pos):
    """使用matplotlib可视化两种策略的路径"""
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.set_facecolor('#f0f0f0') # 设置背景色

    # 绘制场地边界和中心线
    ax.add_patch(patches.Rectangle((0, 0), 4000, 2000, linewidth=2, edgecolor='black', facecolor='none'))
    ax.plot([2000, 2000], [0, 2000], 'k--', label='中心线')

    # 绘制货架和置物区
    for name, pos in shelf_locs.items():
        ax.plot(pos[0], pos[1], 'bs', markersize=10, label='揽收点' if '揽收点_左' in name else "")
        ax.text(pos[0] + 50, pos[1], name, fontsize=9)
    
    for name, pos in delivery_zones.items():
        ax.plot(pos[0], pos[1], 'go', markersize=10, label='置物区' if '区域_a' in name else "")
        ax.text(pos[0] + 50, pos[1], name, fontsize=9)

    # 绘制起始点
    ax.plot(start_pos[0], start_pos[1], 'y*', markersize=15, label='起始点')
    ax.text(start_pos[0] + 50, start_pos[1], 'Start', fontsize=12)
    
    # 绘制B区域（x<2000）
    ax.axvspan(0, 2000, alpha=0.2, color='orange', label='B区域（目标区域）')

    # 绘制路径
    def draw_path(path_coords, color, label, linestyle):
        x_coords, y_coords = zip(*path_coords)
        for i in range(len(x_coords) - 1):
            # 如果是码垛（坐标不变），则不画线
            if x_coords[i] == x_coords[i+1] and y_coords[i] == y_coords[i+1]:
                ax.plot(x_coords[i], y_coords[i], marker='D', color=color, markersize=8, label=f'{label}码垛点' if i==len(x_coords)-2 else "")
            else:
                 ax.plot(x_coords[i:i+2], y_coords[i:i+2], color=color, linewidth=2, linestyle=linestyle, alpha=0.8, label=label if i == 0 else "")
        
        # 标记路径终点
        ax.plot(x_coords[-1], y_coords[-1], marker='s', color=color, markersize=10, label=f'{label}终点' if x_coords[-1] < 2000 else "")

    draw_path(optimal_path_coords, 'blue', '最优策略路径', '-')
    draw_path(fixed_path_coords, 'red', '固定策略路径', '--')

    # 设置图表属性
    ax.set_title('最优策略 vs 固定策略 路径可视化对比', fontsize=16)
    ax.set_xlabel('X 坐标 (mm)')
    ax.set_ylabel('Y 坐标 (mm)')
    ax.set_xlim(-100, 4100)
    ax.set_ylim(-100, 2100)
    ax.set_aspect('equal', adjustable='box')
    ax.grid(True, linestyle=':', alpha=0.6)
    
    # 创建唯一的图例
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys())
    
    plt.show()

def run_comparison():
    """主函数：对比“全局最优”和“固定派送顺序”两种策略的效率，并可视化结果。"""
    # --- 1. 数据设定 ---
    shelf_access_points = {
        '揽收点_左': (180, 1500), '揽收点_中': (180, 1000), '揽收点_右': (180, 500),
    }
    shelf_to_access_point_map = {
        '货架_1': '揽收点_左', '货架_4': '揽收点_左',
        '货架_2': '揽收点_中', '货架_5': '揽收点_中',
        '货架_3': '揽收点_右', '货架_6': '揽收点_右',
    }
    delivery_zones = {
        '区域_a': (3250, 1895), '区域_b': (3850, 1605), '区域_c': (3850, 1235),
        '区域_d': (3850, 845), '区域_e': (3850, 455), '区域_f': (3250, 105)
    }
    start_point = (2000, 1000)
    ROTATION_COST = 2000
    print(f"注意：已设定单次进入旋转区域(a/f)的惩罚值为 {ROTATION_COST}。")

    # --- 2. 模拟抽签 ---
    print("\n--- 正在进行完整的随机抽签... ---")
    shelf_names = list(shelf_to_access_point_map.keys())
    box_numbers = [f'货箱_{i}' for i in range(1, 7)]
    random.shuffle(box_numbers)
    shelf_to_box_map = {shelf: box for shelf, box in zip(shelf_names, box_numbers)}
    print("\n【抽签结果 1: 货架 -> 货箱】")
    for shelf, box in shelf_to_box_map.items():
        print(f"  - {shelf} 上放置的是 {box}")

    stack_numbers = [f'纸垛_{i}#' for i in range(1, 7)]
    zone_names = list(delivery_zones.keys())
    random.shuffle(zone_names)
    empty_zone = zone_names.pop()
    stack_to_zone_map = {stack: zone for stack, zone in zip(stack_numbers, zone_names)}
    print("\n【抽签结果 2: 纸垛 -> 区域】")
    for stack, zone in stack_to_zone_map.items():
        print(f"  - {stack} 放置在 {zone}")
    print(f"  - {empty_zone} 是本轮的轮空区域")

    task_mapping = {}
    unassigned_shelf = None
    for shelf, box in shelf_to_box_map.items():
        corresponding_stack = box.replace('货箱_', '纸垛_') + '#'
        if corresponding_stack in stack_to_zone_map:
            task_mapping[shelf] = stack_to_zone_map[corresponding_stack]
        else:
            unassigned_shelf = shelf
    
    print("\n【最终任务地图 (货架 -> 目标区域)】")
    for shelf, zone in task_mapping.items():
        print(f"  - {shelf} 的货箱 -> {zone}")
    if unassigned_shelf:
        print(f"  - {unassigned_shelf} 的货箱是特殊任务，需码垛在其他箱子上。")
    print("-" * 30)

    # --- 3. 计算“全局最优”策略 ---
    print("--- 正在计算“全局最优”策略的成本... ---")
    best_pickup_order_optimal = None
    min_total_cost_optimal = float('inf')
    all_pickup_orders = list(permutations(shelf_names))
    for pickup_order in all_pickup_orders:
        cost = calculate_total_cost(pickup_order, task_mapping, shelf_access_points, shelf_to_access_point_map, delivery_zones, start_point, ROTATION_COST, unassigned_shelf)
        if cost < min_total_cost_optimal:
            min_total_cost_optimal = cost
            best_pickup_order_optimal = pickup_order
    print("计算完成！")

    # --- 4. 计算“固定派送顺序”策略 ---
    print("\n--- 正在计算“固定派送顺序”策略的成本... ---")
    fixed_delivery_zones_order = ['区域_b', '区域_c', '区域_d', '区域_e', '区域_f', '区域_a']
    reverse_task_mapping = {v: k for k, v in task_mapping.items()}
    delivery_shelves_in_order = []
    for zone in fixed_delivery_zones_order:
        if zone in reverse_task_mapping:
            delivery_shelves_in_order.append(reverse_task_mapping[zone])
    if unassigned_shelf and len(delivery_shelves_in_order) > 1:
        delivery_shelves_in_order.insert(-1, unassigned_shelf)
    fixed_delivery_order = delivery_shelves_in_order
    fixed_pickup_order = tuple(fixed_delivery_order[::-1])
    cost_fixed_strategy = calculate_total_cost(fixed_pickup_order, task_mapping, shelf_access_points, shelf_to_access_point_map, delivery_zones, start_point, ROTATION_COST, unassigned_shelf)
    print("计算完成！")

    # --- 5. 对比并输出结果 ---
    print("\n\n=============== 策略对比结果 (基于完整抽签逻辑) ================")
    optimal_delivery_order = calculate_optimized_delivery_order(best_pickup_order_optimal, task_mapping, unassigned_shelf)
    print(f"\n【方案一：全局最优策略】")
    print(f"  - 最短总成本 (路程+旋转): {min_total_cost_optimal:.2f}")
    print(f"  - 最优揽收顺序: {best_pickup_order_optimal}")
    print(f"  - 对应的最优派送顺序 (两层LIFO):")
    for i, shelf in enumerate(optimal_delivery_order):
        zone_info = task_mapping.get(shelf, f"特殊任务(码垛在'{task_mapping.get(optimal_delivery_order[i-1], 'N/A')}')")
        print(f"    第 {i+1} 步: 将来自 {shelf} 的货箱放置到 {zone_info}")

    print(f"\n【方案二：固定派送顺序策略】")
    print(f"  - 此方案的总成本 (路程+旋转): {cost_fixed_strategy:.2f}")
    print(f"  - 对应的揽收顺序: {fixed_pickup_order}")
    print(f"  - 固定的派送顺序 (两层LIFO):")
    fixed_delivery_order = get_two_layer_lifo_order(fixed_pickup_order)
    for i, shelf in enumerate(fixed_delivery_order):
        zone_info = task_mapping.get(shelf, f"特殊任务(码垛在'{task_mapping.get(fixed_delivery_order[i-1], 'N/A')}')")
        print(f"    第 {i+1} 步: 将来自 {shelf} 的货箱放置到 {zone_info}")

    print("\n----------------- 结论 -----------------")
    difference = cost_fixed_strategy - min_total_cost_optimal
    percentage_increase = (difference / min_total_cost_optimal) * 100
    print(f"相比于最优方案，您的固定顺序方案的总成本高了 {difference:.2f}。")
    print(f"这意味着总成本增加了 {percentage_increase:.2f}%。")
    print("==============================================================")

    # --- 6. 可视化 ---
    optimal_path_coords = get_path_coordinates(best_pickup_order_optimal, task_mapping, shelf_access_points, shelf_to_access_point_map, delivery_zones, start_point, unassigned_shelf)
    fixed_path_coords = get_path_coordinates(fixed_pickup_order, task_mapping, shelf_access_points, shelf_to_access_point_map, delivery_zones, start_point, unassigned_shelf)
    
    visualize_paths(optimal_path_coords, fixed_path_coords, shelf_access_points, delivery_zones, start_point)

def calculate_optimized_delivery_order(pickup_order, task_mapping, unassigned_shelf):
    """
    优化的派送顺序计算，考虑：
    1. 去同一个区域的货箱应该连续放置
    2. 特殊货箱（码垛）应该紧跟在其目标区域的最后一个货箱后面
    3. 特殊货箱不能第一个派送
    """
    # 获取两层LIFO的基本顺序
    base_order = get_two_layer_lifo_order(pickup_order)
    
    # 如果没有特殊货箱，直接返回基本顺序
    if not unassigned_shelf:
        return base_order
    
    # 按区域分组正常货箱
    zone_groups = {}
    for shelf in base_order:
        if shelf == unassigned_shelf:
            continue
        zone = task_mapping[shelf]
        if zone not in zone_groups:
            zone_groups[zone] = []
        zone_groups[zone].append(shelf)
    
    # 构建优化的派送顺序
    optimized_order = []
    processed_shelves = set()
    
    # 遍历基本顺序，但按区域分组处理
    for shelf in base_order:
        if shelf in processed_shelves or shelf == unassigned_shelf:
            continue
            
        current_zone = task_mapping[shelf]
        
        # 一次性处理该区域的所有货箱
        for zone_shelf in zone_groups[current_zone]:
            if zone_shelf not in processed_shelves:
                optimized_order.append(zone_shelf)
                processed_shelves.add(zone_shelf)
        
        # 如果是旋转区域（a或f），在该区域的最后一个货箱后面添加特殊货箱
        if current_zone in ['区域_a', '区域_f'] and unassigned_shelf not in processed_shelves:
            optimized_order.append(unassigned_shelf)
            processed_shelves.add(unassigned_shelf)
    
    # 如果特殊货箱还没被处理，添加到最后
    if unassigned_shelf not in processed_shelves:
        optimized_order.append(unassigned_shelf)
    
    return optimized_order

def get_two_layer_lifo_order(pickup_order):
    """
    根据两层LIFO逻辑计算派送顺序
    每层独立LIFO，第一层抓完才能放第二层，第二层从最后一个抓的开始放，然后才能放第一层
    """
    pickup_list = list(pickup_order)
    total_shelves = len(pickup_list)
    
    # 分成两层，每层最多3个
    layer1 = pickup_list[:3]  # 第一层：前3个
    layer2 = pickup_list[3:6] if total_shelves > 3 else []  # 第二层：后3个
    
    # 每层独立LIFO
    layer1_delivery = layer1[::-1]  # 第一层的放置顺序
    layer2_delivery = layer2[::-1]  # 第二层的放置顺序
    
    # 先放第二层，再放第一层
    delivery_order = layer2_delivery + layer1_delivery
    
    return delivery_order

def test_two_layer_lifo():
    """测试两层LIFO逻辑"""
    print("\n=== 测试两层LIFO逻辑 ===")
    
    # 测试用例：抓取顺序
    pickup_order = ('货架_3', '货架_6', '货架_5', '货架_2', '货架_1', '货架_4')
    delivery_order = get_two_layer_lifo_order(pickup_order)
    
    print(f"抓取顺序: {pickup_order}")
    print(f"第一层（前3个）: {pickup_order[:3]} -> 放置顺序: {pickup_order[:3][::-1]}")
    print(f"第二层（后3个）: {pickup_order[3:]} -> 放置顺序: {pickup_order[3:][::-1]}")
    print(f"总放置顺序: {delivery_order}")
    
    # 验证是否符合预期：'货架_4', '货架_1', '货架_2', '货架_5', '货架_6', '货架_3'
    expected = ['货架_4', '货架_1', '货架_2', '货架_5', '货架_6', '货架_3']
    if delivery_order == expected:
        print("✓ 测试通过！")
    else:
        print(f"✗ 测试失败！期望：{expected}")
    print("========================\n")

# 运行对比分析
if __name__ == '__main__':
    test_two_layer_lifo()  # 先测试LIFO逻辑
    run_comparison()
