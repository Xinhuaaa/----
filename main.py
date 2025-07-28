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
        
        # 随机分配
        random.shuffle(boxes)
        random.shuffle(zones)
        
        box_map = dict(zip(shelves, boxes))
        self.empty_zone = zones.pop()
        stack_map = dict(zip(stacks, zones))
        
        # 打印分配结果
        self._print_assignments(box_map, stack_map)
        
        # 生成任务映射
        for shelf, box in box_map.items():
            stack = box.replace('货箱_', '纸垛_') + '#'
            if stack in stack_map:
                self.task_map[shelf] = stack_map[stack]
            else:
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
        
        # 插入特殊货架
        if self.special_shelf and len(delivery_shelves) == 5:
            insert_pos = random.randint(0, 5)
            delivery_shelves.insert(insert_pos, self.special_shelf)
        
        # FIFO机制：后进先出
        if len(delivery_shelves) == 6:
            first_half = delivery_shelves[:3]
            second_half = delivery_shelves[3:]
            pickup_order = second_half + first_half
        else:
            pickup_order = delivery_shelves
        
        # 同组货架优化
        return self._optimize_shelf_groups(pickup_order)
    
    def _optimize_shelf_groups(self, pickup_order):
        """优化同组货架顺序：特殊货架优先"""
        if not self.special_shelf or self.special_shelf not in pickup_order:
            return pickup_order
        
        partner = SHELF_GROUPS.get(self.special_shelf)
        if not partner or partner not in pickup_order:
            return pickup_order
        
        special_idx = pickup_order.index(self.special_shelf)
        partner_idx = pickup_order.index(partner)
        
        # 特殊货架排在同组货架前面
        if special_idx > partner_idx:
            pickup_order[special_idx], pickup_order[partner_idx] = pickup_order[partner_idx], pickup_order[special_idx]
        
        return pickup_order
    
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
    
    def print_results(self, pickup_order):
        """打印所有结果"""
        delivery_order = self.get_delivery_order(pickup_order)
        zone_order = self.get_zone_order()
        cost = self.calculate_cost(pickup_order)
        
        print("\n=== 任务与路径信息 ===")
        print(f"轮空区域: {self.empty_zone}")
        print(f"特殊货架: {self.special_shelf if self.special_shelf else '无'}")
        print(f"配送区域顺序: {zone_order}")
        print(f"揽收顺序: {pickup_order}")
        print(f"派送顺序: {delivery_order}")
        print(f"总成本: {cost:.2f}")
        
        print("\n任务映射:")
        for shelf, zone in self.task_map.items():
            print(f"  {shelf} -> {zone}")
        if self.special_shelf:
            print(f"  {self.special_shelf} -> 特殊货箱(需要码垛)")
        
        print(f"\n车辆存储:")
        print(f"第一层(前3个): {pickup_order[:3]}")
        print(f"第二层(后3个): {pickup_order[3:]}")
        
        self._print_delivery_steps(delivery_order)
        self._print_formatted_output(pickup_order, delivery_order)
    
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
    
    # 计算揽收顺序
    pickup_order = scheduler.get_pickup_order()
    
    # 打印结果
    scheduler.print_results(pickup_order)


if __name__ == '__main__':
    main()