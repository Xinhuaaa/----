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
        
        # 插入特殊货架（避免成为第一个放置的箱子）
        if self.special_shelf:
            # FIFO转换：delivery_shelves[3:] + delivery_shelves[:3]
            # 要避免特殊货架成为第一个放置的，需要避免它在delivery_shelves的位置0
            # 因为位置0经过FIFO后会变成位置3（第一个放置）
            available_positions = [1, 2, 3, 4, 5]  # 避免位置0
            insert_pos = random.choice(available_positions)
            delivery_shelves.insert(insert_pos, self.special_shelf)
        
        # FIFO机制：后进先出
        return delivery_shelves[3:] + delivery_shelves[:3]
    
    def get_optimized_pickup_sequence(self, pickup_order):
        """优化揽收序列：让同组货架在同一点连续抓取"""
        optimized_sequence = []
        remaining_shelves = pickup_order.copy()
        
        while remaining_shelves:
            next_shelf = remaining_shelves[0]
            current_position = SHELF_ACCESS_POINTS[next_shelf]
            
            # 找到当前位置的所有货架
            shelves_at_position = [s for s in remaining_shelves 
                                 if SHELF_ACCESS_POINTS[s] == current_position]
            
            # 如果特殊货架在此位置，优先处理特殊货架+同组货架
            if self.special_shelf in shelves_at_position:
                partner = SHELF_GROUPS.get(self.special_shelf)
                if partner and partner in shelves_at_position:
                    # 优化：连续抓取特殊货架和同组货架
                    optimized_sequence.extend([self.special_shelf, partner])
                    remaining_shelves.remove(self.special_shelf)
                    remaining_shelves.remove(partner)
                else:
                    # 只抓取下一个货架
                    optimized_sequence.append(next_shelf)
                    remaining_shelves.remove(next_shelf)
            else:
                # 正常抓取下一个货架
                optimized_sequence.append(next_shelf)
                remaining_shelves.remove(next_shelf)
        
        # 检查优化后的序列，确保特殊货架不在位置0（FIFO后会成为第一个放置的）
        if self.special_shelf and len(optimized_sequence) == 6:
            special_idx = optimized_sequence.index(self.special_shelf)
            if special_idx == 0:  # 如果特殊货架在位置0，FIFO后会成为第一个放置的
                # 将特殊货架移动到其他位置
                optimized_sequence.pop(special_idx)
                new_pos = random.choice([1, 2, 3, 4, 5])  # 避免位置0
                optimized_sequence.insert(new_pos, self.special_shelf)
        
        return optimized_sequence
    
    def print_pickup_optimization(self, pickup_order):
        """分析揽收优化情况"""
        # 静默处理，不打印优化信息
        pass
    
    def get_delivery_order(self, pickup_order):
        """根据FIFO机制获取放置顺序"""
        return pickup_order[3:] + pickup_order[:3]  # 后装先卸
    
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
    
    def print_results(self, basic_pickup_order, optimized_pickup_order):
        """打印所有结果"""
        # 使用基础顺序计算放置顺序
        delivery_order = self.get_delivery_order(basic_pickup_order)
        zone_order = self.get_zone_order()
        
        # 计算成本
        optimized_cost = self.calculate_cost(optimized_pickup_order)
        basic_cost = self.calculate_cost(basic_pickup_order)
        
        # 打印优化分析
        self.print_pickup_optimization(optimized_pickup_order)
        
        print(f"轮空区域: {self.empty_zone}")
        print(f"特殊货架: {self.special_shelf if self.special_shelf else '无'}")
        
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
    
    # 打印结果（使用基础顺序计算放置，优化顺序计算揽收成本）
    scheduler.print_results(basic_pickup_order, optimized_pickup_order)


if __name__ == '__main__':
    main()