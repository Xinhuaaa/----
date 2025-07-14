import math
import random
from itertools import permutations

def calculate_distance(pos1, pos2):
    """计算两个坐标点之间的欧几里得距离"""
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

def calculate_total_cost(pickup_order, task_mapping, shelf_access_points, shelf_to_access_point_map, delivery_zones, start_pos, end_pos, rotation_cost, unassigned_shelf):
    """
    为一个给定的揽收/派送顺序计算总行程成本。
    此版本处理了“码垛”任务，即特殊箱子的派送路程成本为0。
    """
    delivery_order_shelves = pickup_order[::-1]

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

    # --- 计算派送成本（包含优化的旋转惩罚和码垛逻辑） ---
    delivery_cost = 0
    previous_zone_name = None
    for shelf in delivery_order_shelves:
        # 如果当前是特殊箱子，它的派送路程成本为0，因为它被码垛
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
            
    final_travel_cost = calculate_distance(current_pos, end_pos)
    
    return pickup_cost + delivery_cost + final_travel_cost

def run_comparison():
    """
    主函数：对比“全局最优”和“固定派送顺序”两种策略的效率。
    """
    # --- 1. 数据设定 (基于您的最终精确修正) ---
    shelf_access_points = {
        '揽收点_左': (180, 1500), # 对应货架1和4
        '揽收点_中': (180, 1000), # 对应货架2和5
        '揽收点_右': (180, 500),  # 对应货架3和6
    }
    shelf_to_access_point_map = {
        '货架_1': '揽收点_左', '货架_4': '揽收点_左',
        '货架_2': '揽收点_中', '货架_5': '揽收点_中',
        '货架_3': '揽收点_右', '货架_6': '揽收点_右',
    }
    delivery_zones = {
        '区域_a': (3250, 1895), 
        '区域_b': (3850, 1605),
        '区域_c': (3850, 1235),
        '区域_d': (3850, 845),
        '区域_e': (3850, 455),
        '区域_f': (3250, 105)
    }
    start_point = (2000, 1000)
    end_point_in_b_zone = (1000, 1000)
    ROTATION_COST = 500
    print(f"注意：已设定单次进入旋转区域(a/f)的惩罚值为 {ROTATION_COST}。")

    # --- 2. 模拟完整的两步随机抽签 ---
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
            target_zone = stack_to_zone_map[corresponding_stack]
            task_mapping[shelf] = target_zone
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
        cost = calculate_total_cost(pickup_order, task_mapping, shelf_access_points, shelf_to_access_point_map, delivery_zones, start_point, end_point_in_b_zone, ROTATION_COST, unassigned_shelf)
        if cost < min_total_cost_optimal:
            min_total_cost_optimal = cost
            best_pickup_order_optimal = pickup_order
    
    print("计算完成！")

    # --- 4. 计算“固定派送顺序”策略 ---
    print("\n--- 正在计算“固定派送顺序”策略的成本... ---")
    # *** 此处已按照您的要求修改 ***
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

    cost_fixed_strategy = calculate_total_cost(fixed_pickup_order, task_mapping, shelf_access_points, shelf_to_access_point_map, delivery_zones, start_point, end_point_in_b_zone, ROTATION_COST, unassigned_shelf)
    print("计算完成！")

    # --- 5. 对比并输出结果 ---
    print("\n\n=============== 策略对比结果 (基于完整抽签逻辑) ================")
    optimal_delivery_order = best_pickup_order_optimal[::-1]

    print(f"\n【方案一：全局最优策略】")
    print(f"  - 最短总成本 (路程+旋转): {min_total_cost_optimal:.2f}")
    print(f"  - 最优揽收顺序: {best_pickup_order_optimal}")
    print(f"  - 对应的最优派送顺序 (LIFO):")
    for i, shelf in enumerate(optimal_delivery_order):
        zone_info = task_mapping.get(shelf, f"特殊任务(码垛在'{task_mapping.get(optimal_delivery_order[i-1], 'N/A')}')")
        print(f"    第 {i+1} 步: 将来自 {shelf} 的货箱放置到 {zone_info}")

    print(f"\n【方案二：固定派送顺序策略】")
    print(f"  - 此方案的总成本 (路程+旋转): {cost_fixed_strategy:.2f}")
    print(f"  - 对应的揽收顺序: {fixed_pickup_order}")
    print(f"  - 固定的派送顺序 (LIFO):")
    for i, shelf in enumerate(fixed_delivery_order):
        zone_info = task_mapping.get(shelf, f"特殊任务(码垛在'{task_mapping.get(fixed_delivery_order[i-1], 'N/A')}')")
        print(f"    第 {i+1} 步: 将来自 {shelf} 的货箱放置到 {zone_info}")

    print("\n----------------- 结论 -----------------")
    difference = cost_fixed_strategy - min_total_cost_optimal
    percentage_increase = (difference / min_total_cost_optimal) * 100
    print(f"相比于最优方案，您的固定顺序方案的总成本高了 {difference:.2f}。")
    print(f"这意味着总成本增加了 {percentage_increase:.2f}%。")
    print("==============================================================")

# 运行对比分析
run_comparison()
