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

# ---------- 核心算法 ----------
def generate_task_mapping(shelves, boxes, stacks, zones):
    """生成任务映射和轮空区域"""
    random.shuffle(boxes)
    random.shuffle(zones)
    box_map = dict(zip(shelves, boxes))
    empty_zone = zones.pop()
    stack_map = dict(zip(stacks, zones))

    task_map = {}
    special_shelf = None
    
    print("\n【抽签结果 1: 货架 -> 货箱】")
    for shelf, box in box_map.items():
        print(f"  - {shelf} 上放置的是 {box}")
    print("\n【抽签结果 2: 纸垛 -> 区域】")
    for stack, zone in stack_map.items():
        print(f"  - {stack} 放置在 {zone}")
    print(f"  - ★ {empty_zone} 是本轮的轮空区域 ★")

    for shelf, box in box_map.items():
        stack = box.replace('货箱_', '纸垛_') + '#'
        if stack in stack_map:
            task_map[shelf] = stack_map[stack]
        else:
            special_shelf = shelf
    
    return task_map, special_shelf, empty_zone

def get_pickup_order(empty_zone, task_map, special_shelf):
    """根据轮空区域和车辆FIFO机制计算揽收顺序"""
    # 1. 确定配送区域顺序
    if empty_zone == '区域_f':
        zone_order = ['区域_e', '区域_d', '区域_c', '区域_b', '区域_a']
    else:
        # 轮空区域不是f时，顺序为：b,c,d,e,f,a（去掉轮空的）
        all_zones = ['区域_b', '区域_c', '区域_d', '区域_e', '区域_f', '区域_a']
        zone_order = [z for z in all_zones if z != empty_zone]
    
    # 2. 将配送区域顺序转换为货架顺序（不包含特殊货架）
    zone_to_shelf = {v: k for k, v in task_map.items()}
    delivery_shelves = [zone_to_shelf[zone] for zone in zone_order if zone in zone_to_shelf]
    
    # 3. 根据车辆双层FIFO机制反推揽收顺序
    if len(delivery_shelves) == 5:  # 5个普通货架 + 1个特殊货架
        # 特殊货架可以插入到任何位置，包括最后一位
        # 这样可以让特殊货架出现在揽收顺序的任何位置(0-5)
        possible_positions = list(range(len(delivery_shelves) + 1))  # 0到5的位置
        insert_pos = random.choice(possible_positions)
        delivery_shelves.insert(insert_pos, special_shelf)
    
    # 现在有6个货架的完整放置顺序
    if len(delivery_shelves) == 6:
        first_to_deliver = delivery_shelves[:3]  # 前3个要放置的
        last_to_deliver = delivery_shelves[3:]   # 后3个要放置的
        pickup_order = last_to_deliver + first_to_deliver  # 先收后放的，再收先放的
    else:
        pickup_order = delivery_shelves
    
    # 4. 特殊货架顺路优化：同组先抓特殊货架
    if special_shelf and special_shelf in pickup_order:
        pickup_order = optimize_special_shelf_same_group(pickup_order, special_shelf)
    
    return pickup_order, zone_order

def optimize_special_shelf_same_group(pickup_order, special_shelf):
    """优化特殊货架：同组货架中，特殊货架先抓"""
    # 货架分组：1和4、2和5、3和6
    shelf_groups = {
        '货架_1': '货架_4', '货架_4': '货架_1',
        '货架_2': '货架_5', '货架_5': '货架_2', 
        '货架_3': '货架_6', '货架_6': '货架_3'
    }
    
    if special_shelf in shelf_groups:
        partner_shelf = shelf_groups[special_shelf]
        
        # 如果同组货架也在揽收顺序中，调整顺序
        if partner_shelf in pickup_order:
            special_idx = pickup_order.index(special_shelf)
            partner_idx = pickup_order.index(partner_shelf)
            
            # 如果特殊货架在同组货架之后，则交换位置
            if special_idx > partner_idx:
                pickup_order[special_idx], pickup_order[partner_idx] = pickup_order[partner_idx], pickup_order[special_idx]
    
    return pickup_order

def get_delivery_order(pickup_order):
    """根据车辆双层FIFO机制获取放置顺序"""
    if len(pickup_order) == 6:
        # 标准情况：前3个放第一层，后3个放第二层，先放第二层再放第一层
        first_layer = pickup_order[:3]
        second_layer = pickup_order[3:]
        return second_layer + first_layer
    else:
        # 非标准情况
        l1, l2 = pickup_order[:3], pickup_order[3:]
        return list(reversed(l2)) + list(reversed(l1))

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

# ---------- 成本计算 ----------
def calculate_distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def calculate_total_cost(pickup_order, task_map, special_shelf):
    """计算总路径成本"""
    delivery_order = get_delivery_order(pickup_order)
    cost = 0
    pos = start_point
    
    # 揽收阶段成本
    for shelf in pickup_order:
        ap_pos = shelf_access_points[shelf_to_access_point_map[shelf]]
        if ap_pos != pos:
            cost += calculate_distance(pos, ap_pos)
            pos = ap_pos

    # 配送阶段成本
    prev_zone = None
    for shelf in delivery_order:
        if shelf == special_shelf:
            continue
        zone = task_map[shelf]
        zone_pos = delivery_zones[zone]
        cost += calculate_distance(pos, zone_pos)
        if zone in ['区域_a', '区域_f'] and (prev_zone not in ['区域_a', '区域_f']):
            cost += ROTATION_COST
        pos = zone_pos
        prev_zone = zone

    # 回到边界线
    if pos[0] >= 2000:
        cost += calculate_distance(pos, (1999, pos[1]))
    return cost

# ---------- 主程序 ----------
def main():
    shelves = [f'货架_{i}' for i in range(1, 7)]
    boxes = [f'货箱_{i}' for i in range(1, 7)]
    stacks = [f'纸垛_{i}#' for i in range(1, 7)]
    zones = list(delivery_zones.keys())

    # 生成任务映射
    task_map, special_shelf, empty_zone = generate_task_mapping(shelves, boxes, stacks, zones)
    
    # 计算揽收和放置顺序
    pickup_order, zone_order = get_pickup_order(empty_zone, task_map, special_shelf)
    delivery_order = get_delivery_order(pickup_order)
    
    # 计算成本
    cost = calculate_total_cost(pickup_order, task_map, special_shelf)

    # 输出结果
    print("\n=== 任务与路径信息 ===")
    print(f"轮空区域: {empty_zone}")
    print(f"特殊货架: {special_shelf if special_shelf else '无'}")
    print(f"配送区域顺序: {zone_order}")
    print(f"揽收顺序: {pickup_order}")
    print(f"派送顺序: {delivery_order}")
    print(f"总成本: {cost:.2f}")
    
    print("\n任务映射:")
    for shelf, zone in task_map.items():
        print(f"  {shelf} -> {zone}")
    if special_shelf:
        print(f"  {special_shelf} -> 特殊货箱(需要码垛)")
    
    print(f"\n车辆存储:")
    print(f"第一层(前3个): {pickup_order[:3]}")
    print(f"第二层(后3个): {pickup_order[3:]}")
    
    print_delivery_steps(delivery_order, task_map, special_shelf)
    
    # 额外输出格式化信息
    print_formatted_output(pickup_order, special_shelf, empty_zone)

def print_formatted_output(pickup_order, special_shelf, empty_zone):
    """输出格式化的关键信息"""
    # 1. 揽收顺序：提取货架编号
    pickup_numbers = [shelf.split('_')[1] for shelf in pickup_order]
    pickup_str = ','.join(pickup_numbers)
    
    # 2. 特殊货架在派送顺序中的位置（从0开始）
    if special_shelf:
        delivery_order = get_delivery_order(pickup_order)
        special_position = delivery_order.index(special_shelf)
    else:
        special_position = -1  # 无特殊货架
    
    # 3. 路线类型：1为正常路线，2为f轮空路线
    route_type = 2 if empty_zone == '区域_f' else 1
    
    print(f"\n=== 格式化输出 ===")
    print(f"揽收顺序({pickup_str}):特殊货箱在派送的顺序({special_position});路线({route_type})")
    print(f"{pickup_str}:{special_position};{route_type}")

if __name__ == '__main__':
    main()