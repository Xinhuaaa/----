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
        """获取配送区域顺序，路线1严格为bcdefa（轮空在bcdef），路线2为edcba（轮空在f）"""
        if self.empty_zone == '区域_f':
            # 路线2：edcba
            return ['区域_e', '区域_d', '区域_c', '区域_b', '区域_a']
        else:
            # 路线1：bcdefa，轮空在bcdef
            all_zones = ['区域_b', '区域_c', '区域_d', '区域_e', '区域_f', '区域_a']
            return [z for z in all_zones if z != self.empty_zone]
    
    def get_pickup_order(self):
        """计算揽收顺序：普通货架严格区域顺序+FIFO，特殊货架可插入任意非轮空区域，实现顺路抓取最大化"""
        zone_order = self.get_zone_order()
        # 区域->货架映射
        zone_to_shelf = {v: k for k, v in self.task_map.items()}
        # 只生成普通货架顺序
        delivery_shelves = [zone_to_shelf[zone] for zone in zone_order if zone in zone_to_shelf]
        # FIFO机制：后进先出
        pickup_order = delivery_shelves[3:] + delivery_shelves[:3]
        # 特殊货架插入时，只能插入第一层（pickup_order[:3]）末尾或中间，绝不插入pickup_order[3:]（第二层）
        if self.special_shelf:
            partner = SHELF_GROUPS.get(self.special_shelf)
            sp_pos = SHELF_ACCESS_POINTS[self.special_shelf]
            inserted = False
            if partner and partner in pickup_order:
                partner_pos = SHELF_ACCESS_POINTS[partner]
                idx = pickup_order.index(partner)
                if sp_pos == partner_pos:
                    # partner在第一层，插在partner后且不越界
                    if idx < 3:
                        insert_pos = min(idx + 1, 3)
                        pickup_order.insert(insert_pos, self.special_shelf)
                        inserted = True
            if not inserted:
                # 只能插在第一层末尾
                pickup_order.insert(3, self.special_shelf)
        return pickup_order
    
    def get_optimized_pickup_sequence(self, pickup_order):
        """优化揽收序列：保证delivery_order中同pickup点的特殊货架和同组货架在optimized_pickup_order中相邻"""
        seq = pickup_order.copy()
        # 以delivery_order为基准，找到所有同pickup点的特殊货架-同组货架对
        delivery_order = self.get_delivery_order(pickup_order)
        handled = set()
        for i, shelf in enumerate(delivery_order):
            if shelf in handled:
                continue
            if shelf == self.special_shelf:
                partner = SHELF_GROUPS.get(self.special_shelf)
                if partner and partner in delivery_order:
                    sp_pos = SHELF_ACCESS_POINTS[self.special_shelf]
                    partner_pos = SHELF_ACCESS_POINTS[partner]
                    if sp_pos == partner_pos:
                        # 在seq中强制相邻
                        idx1 = seq.index(self.special_shelf)
                        idx2 = seq.index(partner)
                        if abs(idx1 - idx2) != 1:
                            # 保持原顺序，特殊货架在前
                            first, second = (self.special_shelf, partner) if idx1 < idx2 else (partner, self.special_shelf)
                            seq = [s for s in seq if s != first and s != second]
                            # 插入到原first位置
                            insert_pos = min(idx1, idx2)
                            seq.insert(insert_pos, first)
                            seq.insert(insert_pos + 1, second)
                        handled.add(self.special_shelf)
                        handled.add(partner)
        return seq
    
    def print_pickup_optimization(self, pickup_order):
        """分析揽收优化情况"""
        # 静默处理，不打印优化信息
        pass
    
    def get_delivery_order(self, pickup_order):
        """放置顺序严格等于zone_order（bcdefa或edcba），特殊货架不参与放置"""
        zone_order = self.get_zone_order()
        # 区域->货架映射
        zone_to_shelf = {v: k for k, v in self.task_map.items()}
        return [zone_to_shelf[zone] for zone in zone_order if zone in zone_to_shelf]
    
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
        # 特殊货架不在delivery_order时，special_position为-1
        if self.special_shelf and self.special_shelf in delivery_order:
            special_position = delivery_order.index(self.special_shelf)
        else:
            special_position = -1
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