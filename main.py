import math
import random
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
    delivery_order_shelves = get_two_layer_lifo_order(pickup_order, unassigned_shelf)
    
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
    delivery_order_shelves = get_two_layer_lifo_order(pickup_order, unassigned_shelf)
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
        b_zone_pos = (1999, current_pos[1])
        path_coords.append(b_zone_pos)

    return path_coords

def visualize_path(path_coords, shelf_locs, delivery_zones, start_pos):
    """使用matplotlib可视化路径"""
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.set_facecolor('#f0f0f0')

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
    
    # 绘制B区域
    ax.axvspan(0, 2000, alpha=0.2, color='orange', label='B区域（目标区域）')

    # 绘制路径
    x_coords, y_coords = zip(*path_coords)
    stacking_point_indices = [i for i, p in enumerate(path_coords) if i > 0 and p == path_coords[i-1]]

    for i in range(len(x_coords) - 1):
        is_stacking_move = (i+1) in stacking_point_indices
        if not is_stacking_move:
             ax.plot(x_coords[i:i+2], y_coords[i:i+2], color='red', linewidth=2, linestyle='-', alpha=0.8, label='路径' if i == 0 else "")

    # 单独标记码垛点，并确保图例只出现一次
    stacking_point_labeled = False
    for idx in stacking_point_indices:
        label_text = ""
        if not stacking_point_labeled:
            label_text = '码垛点'
            stacking_point_labeled = True
        ax.plot(x_coords[idx], y_coords[idx], marker='D', color='purple', markersize=8, label=label_text)

    # 标记路径终点
    ax.plot(x_coords[-1], y_coords[-1], marker='s', color='red', markersize=10, label='终点')

    # 设置图表属性
    ax.set_title('优化策略路径可视化', fontsize=16)
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

def run_fixed_strategy():
    """主函数：使用优化策略并可视化结果。"""
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
    # print(f"注意：已设定单次进入旋转区域(a/f)的惩罚值为 {ROTATION_COST}。")

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
    print(f"  - ★ {empty_zone} 是本轮的轮空区域 ★")

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
        print(f"  - ★ {unassigned_shelf} 的货箱是特殊任务，需码垛在其他箱子上。 ★")
    print("-" * 30)

    # --- 3. 优化路径策略计算 ---
    print("\n--- 正在根据轮空区域和特殊货箱位置优化路径... ---")

    # 步骤1: 根据用户指定的“派送顺序”来反推出“揽收顺序”
    pickup_zone_order = []
    strategy_reason = ""
    if empty_zone == '区域_a':
        # 用户要求派送顺序为 b,c,d,e,f
        # 根据LIFO原则，揽收顺序必须是其倒序 f,e,d,c,b
        delivery_zones_in_order = ['区域_b', '区域_c', '区域_d', '区域_e', '区域_f']
        pickup_zone_order = delivery_zones_in_order[::-1]
        strategy_reason = f"策略：轮空区域为 {empty_zone}, 目标派送顺序为 b->c->d->e->f。"

    elif empty_zone == '区域_f':
        # 用户要求派送顺序为 e,d,c,b,a
        # 根据LIFO原则，揽收顺序必须是其倒序 a,b,c,d,e
        delivery_zones_in_order = ['区域_e', '区域_d', '区域_c', '区域_b', '区域_a']
        pickup_zone_order = delivery_zones_in_order[::-1]
        strategy_reason = f"策略：轮空区域为 {empty_zone}, 目标派送顺序为 e->d->c->b->a。"

    else:
        # 用户要求默认派送顺序为 b,c,d,e,f,a
        # 根据LIFO原则，揽收顺序必须是其倒序 a,f,e,d,c,b
        delivery_zones_in_order = ['区域_b', '区域_c', '区域_d', '区域_e', '区域_f', '区域_a']
        # 移除轮空区域
        delivery_zones_in_order = [z for z in delivery_zones_in_order if z != empty_zone]
        pickup_zone_order = delivery_zones_in_order[::-1]
        strategy_reason = f"策略：轮空区域为 {empty_zone}, 采用默认派送顺序。"
    
    print(strategy_reason)

    reverse_task_mapping = {v: k for k, v in task_mapping.items()}
    base_pickup_shelves = [reverse_task_mapping[zone] for zone in pickup_zone_order if zone in reverse_task_mapping]

    # 步骤2: 规划特殊货箱的抓取时机
    final_pickup_order_list = []
    if unassigned_shelf:
        special_shelf_ap = shelf_to_access_point_map[unassigned_shelf]
        
        trigger_shelf = None
        for shelf in base_pickup_shelves:
            if shelf_to_access_point_map[shelf] == special_shelf_ap:
                trigger_shelf = shelf
                break
                
        if trigger_shelf:
            # 将特殊货箱插入到“顺路”的普通货箱之前
            temp_order = []
            for shelf in base_pickup_shelves:
                if shelf == trigger_shelf:
                    temp_order.append(unassigned_shelf) # 先抓特殊货箱
                temp_order.append(shelf) # 再抓普通货箱
            final_pickup_order_list = temp_order
        else:
            # 理论上此情况不会发生，但作为安全保障保留
            final_pickup_order_list = base_pickup_shelves + [unassigned_shelf]
            print("优化：未在基础路径上找到顺路机会，将在常规任务完成后最后抓取特殊货箱。")
    else:
        final_pickup_order_list = base_pickup_shelves
        print("优化：本轮无特殊码垛任务。")

    fixed_pickup_order = tuple(final_pickup_order_list)
    cost_fixed_strategy = calculate_total_cost(fixed_pickup_order, task_mapping, shelf_access_points, shelf_to_access_point_map, delivery_zones, start_point, ROTATION_COST, unassigned_shelf)
    # print("计算完成！")

    # --- 4. 输出结果 ---
    print("\n\n=============== 优化策略结果 ================")
    print(f"\n【优化策略】")
    print(f"  - 总成本 (路程+旋转): {cost_fixed_strategy:.2f}")
    print(f"  - 最终揽收顺序: {fixed_pickup_order}")
    
    # 输出简化的货架编号序列
    shelf_numbers = [shelf.replace('货架_', '') for shelf in fixed_pickup_order]
    print(f"  - 揽收编号序列: {','.join(shelf_numbers)}")
    
    # 获取派送顺序，并处理码垛逻辑冲突
    fixed_delivery_order = get_two_layer_lifo_order(fixed_pickup_order, unassigned_shelf)
    print(f"  - 派送顺序 (两层LIFO):")
    
    for i, shelf in enumerate(fixed_delivery_order):
        if shelf == unassigned_shelf:
            # 码垛任务的目标是它之前派送的那个货箱
            stacking_target_shelf = None
            current_unassigned_index = fixed_delivery_order.index(unassigned_shelf)
            if current_unassigned_index > 0:
                 stacking_target_shelf = fixed_delivery_order[current_unassigned_index - 1]
            target_info = f"特殊任务(码垛在来自 '{stacking_target_shelf}' 的货箱上)"
        else:
            target_info = task_mapping[shelf]
        print(f"    第 {i+1} 步: 将来自 {shelf} 的货箱放置到 {target_info}")
    print("=======================================================")

    # --- 5. 可视化 ---
    fixed_path_coords = get_path_coordinates(fixed_pickup_order, task_mapping, shelf_access_points, shelf_to_access_point_map, delivery_zones, start_point, unassigned_shelf)
    visualize_path(fixed_path_coords, shelf_access_points, delivery_zones, start_point)

def get_two_layer_lifo_order(pickup_order, unassigned_shelf):
    """
    根据两层LIFO逻辑计算派送顺序，并处理码垛逻辑冲突
    """
    pickup_list = list(pickup_order)
    
    layer1 = pickup_list[:3]
    layer2 = pickup_list[3:6] if len(pickup_list) > 3 else []
    
    layer1_delivery = layer1[::-1]
    layer2_delivery = layer2[::-1]
    
    delivery_order = layer2_delivery + layer1_delivery
    
    # 检查特殊货箱是否是第一个派送的，如果是，则与第二个交换
    # 这个修正逻辑主要用于处理“不顺路”时，特殊货箱被最后揽收的情况
    if unassigned_shelf and len(delivery_order) > 1 and delivery_order[0] == unassigned_shelf:
        print("修正：检测到码垛任务与LIFO规则冲突，自动调整派送顺序。")
        delivery_order[0], delivery_order[1] = delivery_order[1], delivery_order[0]
        
    return delivery_order

# 运行策略
if __name__ == '__main__':
    run_fixed_strategy()
