import math
import random

# ---------- 配置常量 ----------
START_POINT = (2000, 1000)
ROTATION_COST = 2000

# 货架到揽收点的映射
SHELF_ACCESS_POINTS = {
    '货架_1': (180, 1500), '货架_4': (180, 1500),  # 左
    '货架_2': (180, 1000), '货架_5': (180, 1000),  # 中
    '货架_3': (180, 500),  '货架_6': (180, 500),   # 右
}

# 配送区域坐标
DELIVERY_ZONES = {
    '区域_a': (3250, 1895), '区域_b': (3850, 1605), '区域_c': (3850, 1235),
    '区域_d': (3850, 845), '区域_e': (3850, 455), '区域_f': (3250, 105)
}

# 货架分组（同组货架优化顺序用）
SHELF_GROUPS = {'货架_1': '货架_4', '货架_4': '货架_1', '货架_2': '货架_5', 
                '货架_5': '货架_2', '货架_3': '货架_6', '货架_6': '货架_3'}

# ---------- 核心功能类 ----------
class VehicleScheduler:
    """车辆调度算法"""
    
    def __init__(self):
        self.task_map = {}          # 货架->区域映射
        self.special_shelf = None   # 特殊货架
        self.empty_zone = None      # 轮空区域
    
    def generate_tasks(self):
        """生成随机任务分配"""
        shelves = [f'货架_{i}' for i in range(1, 7)]
        boxes = [f'货箱_{i}' for i in range(1, 7)]
        stacks = [f'纸垛_{i}#' for i in range(1, 7)]
        zones = list(DELIVERY_ZONES.keys())
        
        # 随机分配货箱到货架
        random.shuffle(boxes)
        box_map = dict(zip(shelves, boxes))
        
        # 随机分配纸垛到区域（一个区域轮空）
        random.shuffle(zones)
        self.empty_zone = zones.pop()  # 轮空区域
        stack_map = dict(zip(stacks, zones))  # 只有5个纸垛对应5个区域
        
        # 打印分配结果
        self._print_assignments(box_map, stack_map)
        
        # 生成任务映射：只有那些货箱对应纸垛有区域的货架需要抓取
        for shelf, box in box_map.items():
            stack = box.replace('货箱_', '纸垛_') + '#'
            if stack in stack_map:
                # 这个货架上的货箱有对应的纸垛和区域，需要正常配送
                self.task_map[shelf] = stack_map[stack]
            else:
                # 这个货架上的货箱没有对应的纸垛（轮空），是特殊货架
                self.special_shelf = shelf
        
        print(f"\n【任务分析】")
        print(f"需要抓取的货架数量：{len(self.task_map)} + 1(特殊) = {len(self.task_map) + 1}")
        print(f"不需要抓取的货架数量：{6 - len(self.task_map) - 1}")
    
    def _print_assignments(self, box_map, stack_map):
        """打印分配结果"""
        print("\n【抽签结果 1: 货架 -> 货箱】")
        for shelf, box in box_map.items():
            print(f"  - {shelf} 上放置的是 {box}")
        print("\n【抽签结果 2: 纸垛 -> 区域】")
        for stack, zone in stack_map.items():
            print(f"  - {stack} 放置在 {zone}")
        print(f"  - ★ {self.empty_zone} 是本轮的轮空区域 ★")
    
    def get_zone_order(self):
        """获取配送区域顺序"""
        if self.empty_zone == '区域_f':
            return ['区域_e', '区域_d', '区域_c', '区域_b', '区域_a']
        else:
            all_zones = ['区域_b', '区域_c', '区域_d', '区域_e', '区域_f', '区域_a']
            return [z for z in all_zones if z != self.empty_zone]
    
    def get_pickup_order(self):
        """计算揽收顺序"""
        zone_order = self.get_zone_order()
        
        # 区域->货架映射
        zone_to_shelf = {v: k for k, v in self.task_map.items()}
        delivery_shelves = [zone_to_shelf[zone] for zone in zone_order if zone in zone_to_shelf]
        
        # 插入特殊货架（确保不会是第一个放置的箱子）
        if self.special_shelf and len(delivery_shelves) == 5:
            # FIFO机制：[0,1,2,3,4,5] -> [3,4,5,0,1,2]
            # 位置3会成为第一个放置的箱子，所以特殊货架不能插入位置3
            available_positions = [0, 1, 2, 4, 5]  # 排除位置3
            insert_pos = random.choice(available_positions)
            delivery_shelves.insert(insert_pos, self.special_shelf)
        
        # FIFO机制：后进先出
        first_half = delivery_shelves[:3]
        second_half = delivery_shelves[3:]
        pickup_order = second_half + first_half
        
        return pickup_order
    
    def _optimize_special_shelf_position(self, delivery_shelves):
        """优化特殊货架位置：让它与同组货架在揽收时能顺路抓取"""
        partner = SHELF_GROUPS.get(self.special_shelf)
        
        if partner and partner in delivery_shelves:
            partner_idx = delivery_shelves.index(partner)
            
            # 重新设计的插入策略：基于FIFO后的真实相邻位置
            # FIFO规则：[0,1,2,3,4,5] -> [3,4,5,0,1,2]
            # 相邻组合分析：
            # 要让FIFO后位置1-2相邻：需要插入前位置3-4相邻
            # 要让FIFO后位置2-3相邻：需要插入前位置4在后半部分，位置0在前半部分（跨界）
            # 要让FIFO后位置3-4相邻：需要插入前位置0-1相邻
            # 要让FIFO后位置4-5相邻：需要插入前位置1-2相邻
            # 要让FIFO后位置5-6相邻：需要插入前位置2-???（没有位置6）
            
            if partner_idx == 0:
                # partner在位置0，要相邻只能是位置0-1（FIFO后3-4）
                insert_pos = 1
                delivery_shelves.insert(insert_pos, self.special_shelf)
                print(f"\n【揽收优化】特殊货架 {self.special_shelf} 插入位置1，与位置0的同组货架 {partner} 在FIFO后相邻（位置3-4）")
            elif partner_idx == 1:
                # partner在位置1，可以选择位置0（FIFO后3-4）或位置2（FIFO后4-5）
                # 选择位置2更自然
                insert_pos = 2
                delivery_shelves.insert(insert_pos, self.special_shelf)
                print(f"\n【揽收优化】特殊货架 {self.special_shelf} 插入位置2，与位置1的同组货架 {partner} 在FIFO后相邻（位置4-5）")
            elif partner_idx == 2:
                # partner在位置2（前半部分最后位置），这是FIFO机制下最难优化的情况
                # 无论如何插入，FIFO后都很难让它们相邻
                # 选择相对较好的策略：插入位置1，让它们的距离不是最远
                insert_pos = 1
                delivery_shelves.insert(insert_pos, self.special_shelf)
                print(f"\n【揽收优化】特殊货架 {self.special_shelf} 插入位置1，由于FIFO限制无法实现最优相邻")
            elif partner_idx == 3:
                # partner在位置3（后半部分位置0），要相邻需要位置4（后半部分位置1）
                insert_pos = 4
                delivery_shelves.insert(insert_pos, self.special_shelf)
                print(f"\n【揽收优化】特殊货架 {self.special_shelf} 插入位置4，与位置3的同组货架 {partner} 在FIFO后相邻（位置0-1）")
            elif partner_idx == 4:
                # partner在位置4（后半部分位置1），可以选择位置3（位置0-1）或位置5（位置1-2）
                insert_pos = 5
                delivery_shelves.insert(insert_pos, self.special_shelf)
                print(f"\n【揽收优化】特殊货架 {self.special_shelf} 插入位置5，与位置4的同组货架 {partner} 在FIFO后相邻（位置1-2）")
            else:  # partner_idx >= 5，不应该出现，因为delivery_shelves只有5个元素
                insert_pos = partner_idx + 1
                delivery_shelves.insert(insert_pos, self.special_shelf)
                print(f"\n【揽收优化】特殊货架 {self.special_shelf} 插入到同组货架 {partner} 后面")
        else:
            # 如果同组货架不在配送列表中，随机插入
            insert_pos = random.randint(0, 5)
            delivery_shelves.insert(insert_pos, self.special_shelf)
        
        # FIFO机制：后进先出
        first_half = delivery_shelves[:3]
        second_half = delivery_shelves[3:]
        pickup_order = second_half + first_half
        
        return pickup_order
    
    def get_optimized_pickup_sequence(self, pickup_order):
        """获取优化后的实际抓取序列：智能安排特殊货架和同组货架的抓取顺序"""
        optimized_sequence = []
        remaining_shelves = pickup_order.copy()
        
        print(f"\n=== 智能揽收序列优化 ===")
        
        while remaining_shelves:
            # 获取下一个要抓取的货架
            next_shelf = remaining_shelves[0]
            current_position = SHELF_ACCESS_POINTS[next_shelf]
            
            print(f"移动到揽收点 {current_position}")
            
            # 查找在当前揽收点的所有剩余货架
            shelves_at_position = [shelf for shelf in remaining_shelves 
                                 if SHELF_ACCESS_POINTS[shelf] == current_position]
            
            # 检查是否有特殊货架在这个位置
            special_shelf_here = None
            normal_shelves_here = []
            
            for shelf in shelves_at_position:
                if shelf == self.special_shelf:
                    special_shelf_here = shelf
                else:
                    normal_shelves_here.append(shelf)
            
            # 如果特殊货架在这个位置，优先处理特殊货架和同组货架
            if special_shelf_here:
                partner = SHELF_GROUPS.get(special_shelf_here)
                if partner and partner in normal_shelves_here:
                    # 找到了特殊货架和同组货架，优先抓取它们
                    optimized_sequence.extend([special_shelf_here, partner])
                    remaining_shelves.remove(special_shelf_here)
                    remaining_shelves.remove(partner)
                    print(f"  🎯 优化抓取：先抓特殊货架 {special_shelf_here} 和同组货架 {partner}")
                    
                    # 抓取其余在此位置的货架
                    other_shelves = [s for s in normal_shelves_here if s != partner]
                    for shelf in other_shelves:
                        optimized_sequence.append(shelf)
                        remaining_shelves.remove(shelf)
                        print(f"  📦 继续抓取：{shelf}")
                else:
                    # 特殊货架在此，但同组货架不在此位置，按原顺序抓取
                    optimized_sequence.append(next_shelf)
                    remaining_shelves.remove(next_shelf)
                    if next_shelf == special_shelf_here:
                        print(f"  📦 抓取特殊货架：{next_shelf}")
                    else:
                        print(f"  📦 抓取：{next_shelf}")
            else:
                # 没有特殊货架，按原顺序抓取下一个货架
                optimized_sequence.append(next_shelf)
                remaining_shelves.remove(next_shelf)
                print(f"  📦 抓取：{next_shelf}")
        
        return optimized_sequence
    
    def print_pickup_optimization(self, pickup_order):
        """分析和打印揽收路径优化情况"""
        if not self.special_shelf:
            return
            
        partner = SHELF_GROUPS.get(self.special_shelf)
        if not partner or partner not in pickup_order:
            return
            
        special_idx = pickup_order.index(self.special_shelf)
        partner_idx = pickup_order.index(partner)
        
        # 检查是否在揽收序列中相邻
        if abs(special_idx - partner_idx) == 1:
            special_pos = SHELF_ACCESS_POINTS[self.special_shelf]
            partner_pos = SHELF_ACCESS_POINTS[partner]
            
            if special_pos == partner_pos:
                print(f"\n【揽收优化成功】同组货架 {self.special_shelf} 和 {partner} 在揽收序列中相邻")
                print(f"  - 揽收位置：{special_pos}")
                print(f"  - 可以在同一个揽收点连续抓取，节省移动时间")
                
                # 计算节省的距离
                other_points = set(SHELF_ACCESS_POINTS.values()) - {special_pos}
                if other_points:
                    min_distance_to_other = min(
                        math.sqrt((special_pos[0] - other[0])**2 + (special_pos[1] - other[1])**2) 
                        for other in other_points
                    )
                    print(f"  - 避免了约 {min_distance_to_other:.0f} 单位的额外移动距离")
            else:
                print(f"\n【揽收提醒】同组货架 {self.special_shelf} 和 {partner} 在揽收序列中相邻")
                print(f"  - 但不在同一揽收点：{self.special_shelf}在{special_pos}，{partner}在{partner_pos}")
        else:
            print(f"\n【揽收分析】同组货架 {self.special_shelf} 和 {partner} 未在揽收序列中相邻")
            print(f"  - 位置：{self.special_shelf}第{special_idx+1}个，{partner}第{partner_idx+1}个")
            print(f"  - 需要分别前往不同位置抓取")
    
    def get_delivery_order(self, pickup_order):
        """根据FIFO机制获取放置顺序"""
        if len(pickup_order) == 6:
            return pickup_order[3:] + pickup_order[:3]  # 后装先卸
        else:
            return list(reversed(pickup_order[3:])) + list(reversed(pickup_order[:3]))
    
    def calculate_cost(self, pickup_order):
        """计算总路径成本"""
        delivery_order = self.get_delivery_order(pickup_order)
        cost = 0
        pos = START_POINT
        
        # 揽收成本
        for shelf in pickup_order:
            ap_pos = SHELF_ACCESS_POINTS[shelf]
            if ap_pos != pos:
                cost += self._distance(pos, ap_pos)
                pos = ap_pos
        
        # 配送成本
        prev_zone = None
        for shelf in delivery_order:
            if shelf == self.special_shelf:
                continue
            
            zone = self.task_map[shelf]
            zone_pos = DELIVERY_ZONES[zone]
            cost += self._distance(pos, zone_pos)
            
            # 旋转成本
            if zone in ['区域_a', '区域_f'] and prev_zone not in ['区域_a', '区域_f']:
                cost += ROTATION_COST
            
            pos = zone_pos
            prev_zone = zone
        
        # 回到边界
        if pos[0] >= 2000:
            cost += self._distance(pos, (1999, pos[1]))
        
        return cost
    
    def _distance(self, a, b):
        """计算欧几里得距离"""
        return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)
    
    def ensure_special_shelf_not_first(self, pickup_order):
        """确保特殊货架不会是第一个放置的箱子"""
        if not self.special_shelf or self.special_shelf not in pickup_order:
            return pickup_order
            
        # 计算放置顺序
        delivery_order = self.get_delivery_order(pickup_order)
        
        # 如果特殊货架是第一个放置的，需要调整
        if delivery_order[0] == self.special_shelf:
            # FIFO机制：[0,1,2,3,4,5] -> [3,4,5,0,1,2]
            # 第一个放置的是位置3的货架，所以需要把特殊货架从位置3移走
            pickup_order = pickup_order.copy()
            special_idx = pickup_order.index(self.special_shelf)
            
            if special_idx == 3:  # 特殊货架在位置3
                # 将特殊货架移动到其他位置
                pickup_order.pop(special_idx)
                # 选择一个不会让它成为第一个的位置：0, 1, 2, 4, 5都可以
                new_pos = random.choice([0, 1, 2, 4, 5])
                pickup_order.insert(new_pos, self.special_shelf)
                print(f"【调整】特殊货架 {self.special_shelf} 从位置{special_idx}移动到位置{new_pos}，避免成为第一个放置的箱子")
        
        return pickup_order
    
    def print_results(self, basic_pickup_order, optimized_pickup_order):
        """打印所有结果"""
        # 确保特殊货架不会是第一个放置的箱子
        basic_pickup_order = self.ensure_special_shelf_not_first(basic_pickup_order)
        optimized_pickup_order = self.ensure_special_shelf_not_first(optimized_pickup_order)
        
        # 使用基础FIFO顺序计算放置顺序，保证FIFO一致性
        delivery_order = self.get_delivery_order(basic_pickup_order)
        zone_order = self.get_zone_order()
        
        # 使用优化后的顺序计算揽收成本
        optimized_cost = self.calculate_cost(optimized_pickup_order)
        basic_cost = self.calculate_cost(basic_pickup_order)
        
        # 打印揽收优化分析
        self.print_pickup_optimization(optimized_pickup_order)
        
        print("\n=== 任务与路径信息 ===")
        print(f"轮空区域: {self.empty_zone}")
        print(f"特殊货架: {self.special_shelf if self.special_shelf else '无'}")
        print(f"配送区域顺序: {zone_order}")
        print(f"揽收顺序(基础): {basic_pickup_order}")
        print(f"揽收顺序(优化): {optimized_pickup_order}")
        print(f"派送顺序: {delivery_order}")
        print(f"基础成本: {basic_cost:.2f}")
        print(f"优化成本: {optimized_cost:.2f}")
        print(f"节省成本: {basic_cost - optimized_cost:.2f}")
        
        print("\n任务映射:")
        for shelf, zone in self.task_map.items():
            print(f"  {shelf} -> {zone}")
        if self.special_shelf:
            print(f"  {self.special_shelf} -> 特殊货箱(需要码垛)")
        
        print(f"\n车辆存储(基于FIFO顺序):")
        print(f"第一层(前3个): {basic_pickup_order[:3]}")
        print(f"第二层(后3个): {basic_pickup_order[3:]}")
        
        self._print_delivery_steps(delivery_order)
        self._print_formatted_output(basic_pickup_order, delivery_order)
    
    def _print_delivery_steps(self, delivery_order):
        """打印配送步骤"""
        print(f"\n=== 车辆放置步骤 ===")
        for i, shelf in enumerate(delivery_order, 1):
            if shelf == self.special_shelf:
                print(f"第{i}步: 从车上取出 {shelf} 上的货箱，码垛在已放置的纸垛上")
            else:
                zone = self.task_map[shelf]
                print(f"第{i}步: 从车上取出 {shelf} 上的货箱，放置到 {zone}")
        print("完成所有放置任务！")
    
    def _print_formatted_output(self, pickup_order, delivery_order):
        """输出格式化信息"""
        pickup_numbers = [shelf.split('_')[1] for shelf in pickup_order]
        pickup_str = ','.join(pickup_numbers)
        
        special_position = delivery_order.index(self.special_shelf) if self.special_shelf else -1
        route_type = 2 if self.empty_zone == '区域_f' else 1
        
        print(f"\n=== 格式化输出 ===")
        print(f"揽收顺序({pickup_str}):特殊货箱在派送的顺序({special_position});路线({route_type})")
        print(f"{pickup_str}:{special_position};{route_type}")


# ---------- 主程序 ----------
def main():
    """主程序入口"""
    scheduler = VehicleScheduler()
    
    # 生成任务分配
    scheduler.generate_tasks()
    
    # 计算基础揽收顺序（FIFO后）
    basic_pickup_order = scheduler.get_pickup_order()
    
    # 实时优化揽收序列（智能抓取顺序）
    optimized_pickup_order = scheduler.get_optimized_pickup_sequence(basic_pickup_order)
    
    print(f"\n=== 优化对比 ===")
    print(f"FIFO基础顺序：{basic_pickup_order}")
    print(f"实时优化顺序：{optimized_pickup_order}")
    
    # 打印结果（使用基础顺序计算放置，优化顺序计算揽收成本）
    scheduler.print_results(basic_pickup_order, optimized_pickup_order)


if __name__ == '__main__':
    main()