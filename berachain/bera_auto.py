from web3 import Web3
import yaml
import time
import random
import os
import argparse

# 导入所有子脚本中的函数
from bera_swap import setup_web3, swap_bera_to_stgusdc
from bera_mint_honey import mint_honey
from bera_bend_supply import supply_honey
from bera_berps_deposit import deposit_honey
from bera_berps_stake import stake_bhoney

def load_account(config_path):
    """从配置文件加载账户信息"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            if 'berachain' not in config:
                raise ValueError("配置文件中缺少 berachain 配置")
            return {
                "private_key": config['berachain']['private_key'],
                "address": config['berachain']['address']
            }
    except Exception as e:
        print(f"加载配置文件失败: {str(e)}")
        return None

def random_delay(min_sec, max_sec):
    """随机延时"""
    delay = random.uniform(min_sec, max_sec)
    print(f"\n等待 {delay:.2f} 秒...")
    time.sleep(delay)

def execute_all_steps(w3, account, start_step=1):
    """
    执行所有步骤
    start_step: 从第几步开始执行（1-5）
    """
    try:
        print("\n=== 开始执行 Berachain 自动操作 ===")
        print(f"从第 {start_step} 步开始执行")
        
        steps = [
            ("Swap BERA 到 stgUSDC", lambda: swap_bera_to_stgusdc(w3, account)),
            ("将 stgUSDC 换成 HONEY", lambda: mint_honey(w3, account)),
            ("向 Bend 协议质押 HONEY", lambda: supply_honey(w3, account)),
            ("向 BERPS 协议质押 HONEY", lambda: deposit_honey(w3, account)),
            ("质押 bHONEY", lambda: stake_bhoney(w3, account))
        ]
        
        # 从指定步骤开始执行
        for i, (step_name, step_func) in enumerate(steps[start_step-1:], start=start_step):
            print(f"\n--- 步骤{i}: {step_name} ---")
            if not step_func():
                print(f"步骤{i} 失败，终止执行")
                return False
                
            # 最后一步不需要延时
            if i < len(steps):
                if i == 4:  # 最后一步之前
                    random_delay(1, 5)
                else:
                    random_delay(5, 10)
        
        print("\n=== 所有操作执行完成 ===")
        return True
        
    except Exception as e:
        print(f"\n执行过程中发生错误: {str(e)}")
        return False

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='Berachain 自动操作脚本')
    parser.add_argument('config', help='配置文件路径')
    parser.add_argument('--step', type=int, choices=range(1, 6), default=1,
                      help='从第几步开始执行 (1-5): 1=Swap, 2=Mint, 3=Bend, 4=BERPS, 5=Stake')
    return parser.parse_args()

def main():
    # 解析命令行参数
    args = parse_args()
    
    if not os.path.exists(args.config):
        print(f"找不到配置文件: {args.config}")
        return
    
    # 加载账户配置
    account = load_account(args.config)
    if not account:
        return
    
    # 设置 Web3
    w3 = setup_web3()
    if not w3.is_connected():
        print("无法连接到 Berachain 网络！")
        return
    
    # 执行所有步骤
    success = execute_all_steps(w3, account, args.step)
    
    if success:
        print("\n所有操作已成功完成！")
    else:
        print("\n操作执行失败！")

if __name__ == "__main__":
    main() 