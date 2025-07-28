import math
import random

# ---------- 参数数据 ----------
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

# ---------- 路径与成本计算 ----------
def calculate_distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def calculate_total_cost(pickup_order, task_map, shelf_aps, shelf2ap, zones, start, rot_cost, special):
    delivery_order = get_delivery_order(pickup_order, special)
    cost = 0
    pos = start
    for shelf in pickup_order:
        ap_pos = shelf_aps[shelf2ap[shelf]]
        if ap_pos != pos:
            cost += calculate_distance(pos, ap_pos)
            pos = ap_pos

    prev_zone = None
    for shelf in delivery_order:
        if shelf == special:
            continue
        zone = task_map[shelf]
        zone_pos = zones[zone]
        cost += calculate_distance(pos, zone_pos)
        if zone in ['区域_a', '区域_f'] and (prev_zone not in ['区域_a', '区域_f']):
            cost += rot_cost
        pos = zone_pos
        prev_zone = zone

    if pos[0] >= 2000:
        cost += calculate_distance(pos, (1999, pos[1]))
    return cost

def get_path_coordinates(pickup_order, task_map, shelf_aps, shelf2ap, zones, start, special):
    coords = [start]
    pos = start
    for shelf in pickup_order:
        ap_pos = shelf_aps[shelf2ap[shelf]]
        if ap_pos != pos:
            coords.append(ap_pos)
            pos = ap_pos
    delivery_order = get_delivery_order(pickup_order, special)
    for shelf in delivery_order:
        if shelf == special:
            coords.append(coords[-1])
        else:
            coords.append(zones[task_map[shelf]])
            pos = zones[task_map[shelf]]
    if pos[0] >= 2000:
        coords.append((1999, pos[1]))
    return coords

# ---------- 策略逻辑 ----------
def generate_task_mapping(shelves, boxes, stacks, zones):
    random.shuffle(boxes)
    random.shuffle(zones)
    box_map = dict(zip(shelves, boxes))
    unassigned_zone = zones.pop()
    stack_map = dict(zip(stacks, zones))

    task_map = {}
    special_shelf = None
    print("\n【抽签结果 1: 货架 -> 货箱】")
    for shelf, box in box_map.items():
        print(f"  - {shelf} 上放置的是 {box}")
    print("\n【抽签结果 2: 纸垛 -> 区域】")
    for stack, zone in stack_map.items():
        print(f"  - {stack} 放置在 {zone}")
    print(f"  - ★ {unassigned_zone} 是本轮的轮空区域 ★")

    for shelf, box in box_map.items():
        stack = box.replace('货箱_', '纸垛_') + '#'
        if stack in stack_map:
            task_map[shelf] = stack_map[stack]
        else:
            special_shelf = shelf
    return task_map, special_shelf, unassigned_zone

def get_delivery_zone_order(empty_zone):
    """
    根据轮空区域确定放置顺序
    - 如果轮空区域在 a,b,c,d,e 中 → 放置顺序：a,b,c,d,e,f（去掉轮空的）
    - 如果轮空区域为 f → 放置顺序：e,d,c,b,a
    """
    if empty_zone == '区域_f':
        # 轮空区域为f，放置顺序为：e,d,c,b,a
        return ['区域_e', '区域_d', '区域_c', '区域_b', '区域_a']
    else:
        # 轮空区域在a,b,c,d,e中，放置顺序为：a,b,c,d,e,f（去掉轮空的）
        default_order = ['区域_a', '区域_b', '区域_c', '区域_d', '区域_e', '区域_f']
        return [z for z in default_order if z != empty_zone]

def calculate_pickup_order_from_delivery_zones(zone_order, task_map, special_shelf):
    """
    根据配送区域顺序和车辆FIFO机制计算揽收顺序
    
    车辆机制：
    - 前3个货箱放第一层FIFO，后3个货箱放第二层FIFO
    - 放置时：先放第二层FIFO(4,5,6)，再放第一层FIFO(1,2,3)
    - 最终放置顺序：[4,5,6,1,2,3]
    
    Args:
        zone_order: 配送区域顺序 (如：['区域_e', '区域_d', '区域_c', '区域_b', '区域_a'])
        task_map: 货架到区域的映射
        special_shelf: 特殊货架
    
    Returns:
        pickup_order: 揽收顺序
    """
    # 从配送区域顺序获取对应的货架顺序（期望的放置顺序）
    zone_to_shelf = {v: k for k, v in task_map.items()}
    desired_delivery_order = [zone_to_shelf[zone] for zone in zone_order if zone in zone_to_shelf]
    
    # 如果有特殊货架，添加到期望放置顺序的末尾
    if special_shelf:
        desired_delivery_order.append(special_shelf)
    
    # 根据车辆FIFO机制反推揽收顺序
    # 期望放置顺序：[a, b, c, d, e, special] (6个货架)
    # 车辆放置机制：先放第二层[4,5,6]，再放第一层[1,2,3]
    # 所以：第二层FIFO = [a,b,c], 第一层FIFO = [d,e,special]
    # 揽收顺序应该是：[d,e,special,a,b,c]
    
    if len(desired_delivery_order) != 6:
        # 处理非标准情况
        return desired_delivery_order
    
    # 标准6个货箱的情况
    first_layer_shelves = desired_delivery_order[3:]  # [d,e,special] - 后放的3个
    second_layer_shelves = desired_delivery_order[:3]  # [a,b,c] - 先放的3个
    
    # 揽收顺序：先收第一层的货架，再收第二层的货架
    pickup_order = first_layer_shelves + second_layer_shelves
    
    return pickup_order

def get_optimized_pickup_order(zone_order, task_map, special_shelf, shelf_to_access_point_map):
    """
    获取优化的揽收顺序，考虑特殊货架的揽收点优化
    """
    # 首先根据配送顺序计算基础的揽收顺序
    pickup_order = calculate_pickup_order_from_delivery_zones(zone_order, task_map, special_shelf)
    
    # 如果有特殊货架，尝试优化其在揽收顺序中的位置（顺路原则）
    if special_shelf and special_shelf in pickup_order:
        # 移除特殊货架，然后根据揽收点就近原则重新插入
        pickup_order.remove(special_shelf)
        pickup_order = insert_special_shelf(pickup_order, special_shelf, shelf_to_access_point_map)
    
    return pickup_order

def insert_special_shelf(pickup_order, special, shelf2ap):
    if not special:
        return pickup_order
    special_ap = shelf2ap[special]
    for i, s in enumerate(pickup_order):
        if shelf2ap[s] == special_ap:
            return pickup_order[:i] + [special] + pickup_order[i:]
    return pickup_order + [special]

def get_delivery_order(pickup_order, special=None):
    """
    根据车辆的双层FIFO存储机制确定放置顺序
    车辆存储：前3个货箱放第一层，后3个货箱放第二层
    每层都是独立的先进先出(FIFO)队列
    放置时：先放第二层的FIFO(4,5,6)，再放第一层的FIFO(1,2,3)
    
    Args:
        pickup_order: 抓取顺序列表 [1,2,3,4,5,6]
        special: 特殊货架（对应轮空区域的货箱）
    
    Returns:
        delivery_order: 放置顺序列表 [4,5,6,1,2,3]
    """
    if len(pickup_order) != 6:
        # 如果不是6个货箱，按原逻辑处理
        l1, l2 = pickup_order[:3], pickup_order[3:]
        order = list(reversed(l2)) + list(reversed(l1))
    else:
        # 标准6个货箱：两层独立的FIFO
        # 第一层FIFO：前3个货箱 [1,2,3]
        # 第二层FIFO：后3个货箱 [4,5,6]  
        # 放置顺序：先放第二层FIFO，再放第一层FIFO
        first_layer_fifo = pickup_order[:3]   # [1,2,3]
        second_layer_fifo = pickup_order[3:]  # [4,5,6]
        order = second_layer_fifo + first_layer_fifo  # [4,5,6,1,2,3]
    
    # 如果有特殊货箱且它是第一个要放置的，需要调整顺序
    # 因为特殊货箱需要码垛在其他纸垛上，不能最先放置
    if special and len(order) > 1 and order[0] == special:
        order[0], order[1] = order[1], order[0]
    
    return order

def test_empty_zone_f():
    """测试轮空区域为f的情况"""
    shelves = [f'货架_{i}' for i in range(1, 7)]
    boxes = [f'货箱_{i}' for i in range(1, 7)]
    stacks = [f'纸垛_{i}#' for i in range(1, 7)]
    zones = list(delivery_zones.keys())
    
    # 手动设置轮空区域为f的情况
    empty_zone = '区域_f'
    remaining_zones = [z for z in zones if z != empty_zone]
    
    # 随机分配纸垛到剩余区域
    random.shuffle(remaining_zones)
    stack_map = dict(zip(stacks[:5], remaining_zones))  # 只有5个纸垛
    
    # 随机分配货箱到货架
    random.shuffle(boxes)
    box_map = dict(zip(shelves, boxes))
    
    # 创建任务映射
    task_map = {}
    special_shelf = None
    
    print(f"\n=== 测试轮空区域为f的情况 ===")
    print("【货架 -> 货箱】")
    for shelf, box in box_map.items():
        print(f"  - {shelf} 上放置的是 {box}")
    
    print("【纸垛 -> 区域】")
    for stack, zone in stack_map.items():
        print(f"  - {stack} 放置在 {zone}")
    print(f"  - ★ {empty_zone} 是本轮的轮空区域 ★")
    
    for shelf, box in box_map.items():
        stack = box.replace('货箱_', '纸垛_') + '#'
        if stack in stack_map:
            task_map[shelf] = stack_map[stack]
        else:
            special_shelf = shelf
    
    # 获取放置顺序
    zone_order = get_delivery_zone_order(empty_zone)
    pickup_order = get_optimized_pickup_order(zone_order, task_map, special_shelf, shelf_to_access_point_map)
    delivery_order = get_delivery_order(pickup_order, special_shelf)
    
    print(f"\n轮空区域: {empty_zone}")
    print(f"特殊货架: {special_shelf if special_shelf else '无'}")
    print("任务映射:")
    for shelf, zone in task_map.items():
        print(f"  {shelf} -> {zone}")
    if special_shelf:
        print(f"  {special_shelf} -> 特殊货箱(需要码垛)")
    
    print(f"配送区域顺序: {zone_order}")
    print(f"揽收顺序: {pickup_order}")
    print(f"派送顺序: {delivery_order}")
    
    print(f"\n车辆存储验证:")
    print(f"第一层(前3个): {pickup_order[:3]}")
    print(f"第二层(后3个): {pickup_order[3:]}")
    print(f"放置顺序(先放第二层,再放第一层): {delivery_order}")
    
    # 输出车辆每一步的放置步骤
    print_delivery_steps(delivery_order, task_map, special_shelf)

def print_delivery_steps(delivery_order, task_map, special_shelf):
    """输出车辆每一步的放置步骤"""
    print(f"\n=== 车辆放置步骤 ===")
    for i, shelf in enumerate(delivery_order, 1):
        if shelf == special_shelf:
            print(f"第{i}步: 从车上取出 {shelf} 上的货箱，码垛在已放置的纸垛上")
        else:
            zone = task_map[shelf]
            print(f"第{i}步: 从车上取出 {shelf} 上的货箱，放置到 {zone}")
    print("完成所有放置任务！")

# ---------- 主入口 ----------
def main():
    # 正常随机测试
    shelves = [f'货架_{i}' for i in range(1, 7)]
    boxes = [f'货箱_{i}' for i in range(1, 7)]
    stacks = [f'纸垛_{i}#' for i in range(1, 7)]
    zones = list(delivery_zones.keys())

    task_map, special_shelf, empty_zone = generate_task_mapping(shelves, boxes, stacks, zones)
    zone_order = get_delivery_zone_order(empty_zone)
    pickup_order = get_optimized_pickup_order(zone_order, task_map, special_shelf, shelf_to_access_point_map)
    delivery_order = get_delivery_order(pickup_order, special_shelf)

    cost = calculate_total_cost(pickup_order, task_map, shelf_access_points, shelf_to_access_point_map, delivery_zones, start_point, ROTATION_COST, special_shelf)

    print("\n=== 任务与路径信息 ===")
    print(f"轮空区域: {empty_zone}")
    print(f"特殊货架: {special_shelf if special_shelf else '无'}")
    print(f"揽收顺序: {pickup_order}")
    print(f"派送顺序: {delivery_order}")
    print(f"总成本: {cost:.2f}")
    
    # 调试信息
    print("\n=== 调试信息 ===")
    print("任务映射:")
    for shelf, zone in task_map.items():
        print(f"  {shelf} -> {zone}")
    
    print(f"\n配送区域顺序: {zone_order}")
    
    # 验证放置顺序逻辑
    print(f"\n车辆存储验证:")
    print(f"第一层(前3个): {pickup_order[:3]}")
    print(f"第二层(后3个): {pickup_order[3:]}")
    print(f"放置顺序(先放第二层,再放第一层): {delivery_order}")
    
    # 输出车辆每一步的放置步骤
    print_delivery_steps(delivery_order, task_map, special_shelf)
    
    # 测试轮空区域为f的情况
    test_empty_zone_f()

if __name__ == '__main__':
    main()
