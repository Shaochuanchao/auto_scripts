#humanity测试网每日自动领取奖励脚本
from web3 import Web3
import yaml
import time
import random
import json
import os
import argparse
import sys

# 固定配置
RPC_URL = "https://rpc.testnet.humanity.org"
CONTRACT_ADDRESS = "0xa18f6FCB2Fd4884436d10610E69DB7BFa1bFe8C7"

# 合约 ABI
ABI = [
    {
        "inputs": [],
        "name": "claimReward",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "user", "type": "address"},
            {"internalType": "uint256", "name": "epochID", "type": "uint256"}
        ],
        "name": "userClaimStatus",
        "outputs": [
            {
                "components": [
                    {"internalType": "bool", "name": "claimStatus", "type": "bool"},
                    {"internalType": "uint256", "name": "buffer", "type": "uint256"}
                ],
                "internalType": "struct IRewards.UserClaim",
                "name": "",
                "type": "tuple"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "currentEpoch",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "", "type": "address"}],
        "name": "userBuffer",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "claimBuffer",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

def load_config(config_path):
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"错误: 找不到配置文件 '{config_path}'")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"错误: 配置文件格式不正确 - {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"错误: 读取配置文件时出错 - {str(e)}")
        sys.exit(1)

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='Humanity测试网每日自动领取奖励脚本')
    parser.add_argument('config', help='配置文件路径 (yaml格式)')
    return parser.parse_args()

def setup_web3():
    """初始化 Web3"""
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    return w3

def check_claim_status(w3, account, contract):
    """检查是否可以领取奖励"""
    try:
        checksum_address = Web3.to_checksum_address(account['address'])
        
        # 获取当前周期
        current_epoch = contract.functions.currentEpoch().call()
        print(f"当前周期: {current_epoch}")
        
        # 获取用户在当前周期的领取状态
        claim_info = contract.functions.userClaimStatus(
            checksum_address,
            current_epoch
        ).call()
        
        # claim_info 是一个元组，根据 UserClaim 结构体定义：
        # [0] = buffer (uint256)
        # [1] = claimStatus (bool)
        buffer = claim_info[0]
        claim_status = not claim_info[1]  # 如果 claimStatus 为 False，表示可以领取
        
        print(f"账户 {account['name']} 在当前周期的状态:")
        print(f"- 领取状态: {'已领取' if not claim_status else '未领取'}")
        print(f"- Buffer: {buffer}")
        
        return claim_status
    except Exception as e:
        print(f"检查领取状态失败：{str(e)}")
        if hasattr(e, 'args'):
            print(f"错误详情: {e.args}")
        return False

def check_buffer(w3, account, contract):
    """检查用户buffer"""
    try:
        checksum_address = Web3.to_checksum_address(account['address'])
        buffer = contract.functions.userBuffer(checksum_address).call()
        return buffer > 0
    except Exception as e:
        print(f"检查buffer失败：{str(e)}")
        return False

def verify_account(w3, account):
    """验证账户地址与私钥是否匹配"""
    try:
        # 从私钥恢复地址
        acct = w3.eth.account.from_key(account['private_key'])
        expected_address = acct.address
        
        # 将配置中的地址转换为 checksum 格式
        provided_address = Web3.to_checksum_address(account['address'])
        
        if expected_address.lower() != provided_address.lower():
            print(f"地址验证失败:")
            print(f"配置文件中的地址: {provided_address}")
            print(f"私钥对应的地址: {expected_address}")
            return False
            
        return True
    except Exception as e:
        print(f"地址验证出错: {str(e)}")
        return False

def execute_transaction(w3, account, contract, func_name):
    """执行合约交易"""
    try:
        # 首先验证账户
        if not verify_account(w3, account):
            print("账户验证失败，终止交易")
            return False
            
        # 使用私钥对应的地址
        acct = w3.eth.account.from_key(account['private_key'])
        checksum_address = acct.address
        print(f"使用地址: {checksum_address}")
        
        # 获取合约函数
        contract_function = getattr(contract.functions, func_name)
        
        # 获取当前 gas 价格，设置最小值
        gas_price = int(w3.eth.gas_price * 1.2)
        print(f"当前 gas 价格: {w3.from_wei(gas_price, 'gwei')} gwei")
        
        max_attempts = 3  # 最大重试次数
        for attempt in range(max_attempts):
            try:
                # 获取当前 nonce
                nonce = w3.eth.get_transaction_count(checksum_address)
                
                # 构建交易
                transaction = contract_function().build_transaction({
                    'from': checksum_address,
                    'nonce': nonce,
                    'gas': 300000,
                    'gasPrice': gas_price
                })

                # 签名交易
                signed_txn = w3.eth.account.sign_transaction(
                    transaction,
                    account['private_key']
                )

                try:
                    # 发送交易
                    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                    print(f"交易已发送，哈希: {tx_hash.hex()}")
                except Exception as send_error:
                    if "already known" in str(send_error):
                        print("交易已在交易池中，等待确认...")
                        # 从错误信息中提取交易哈希
                        tx_hash = signed_txn.hash
                    else:
                        raise send_error
                
                # 等待交易确认，增加超时时间和检查间隔
                receipt = w3.eth.wait_for_transaction_receipt(
                    tx_hash,
                    timeout=120,  # 5分钟超时
                    poll_latency=10  # 每10秒检查一次
                )
                
                if receipt['status'] == 1:
                    print(f"账户 {account['name']} {func_name} 调用成功！交易哈希: {tx_hash.hex()}")
                    print(f"Gas 使用: {receipt['gasUsed']}")
                    return True
                else:
                    print(f"账户 {account['name']} {func_name} 调用失败！")
                    return False
                    
            except Exception as e:
                if "already known" in str(e):
                    print("交易已在交易池中，等待30秒后继续...")
                    time.sleep(5)
                    continue
                elif "not in the chain after" in str(e):
                    if attempt < max_attempts - 1:
                        # 增加 gas 价格 20%
                        gas_price = int(gas_price * 1.2)
                        print(f"交易超时，增加 gas 价格到 {w3.from_wei(gas_price, 'gwei')} gwei")
                        print(f"等待 5  秒后重试... (尝试 {attempt + 2}/{max_attempts})")
                        time.sleep(5)
                        continue
                print(f"账户 {account['name']} {func_name} 调用失败：{str(e)}")
                return False
            
    except Exception as e:
        error_msg = str(e)
        if "contract not active" in error_msg:
            print(f"账户 {account['name']} {func_name} 调用失败：合约当前未激活")
        elif "user not registered" in error_msg:
            print(f"账户 {account['name']} {func_name} 调用失败：用户未在 VC 合约中注册")
        elif "no rewards available" in error_msg:
            print(f"账户 {account['name']} {func_name} 调用失败：当前没有可领取的奖励")
        else:
            print(f"账户 {account['name']} {func_name} 调用失败：{error_msg}")
        return False

def process_account(w3, account, contract):
    """处理单个账户的所有操作"""
    print(f"\n开始处理账户 {account['name']}...")
    
    # 首先验证账户
    if not verify_account(w3, account):
        print(f"账户 {account['name']} 验证失败，跳过处理")
        return False
    
    # 检查是否可以领取奖励
    if not check_claim_status(w3, account, contract):
        print(f"账户 {account['name']} 当前无法领取奖励")
        return False
    
    # 执行 claimReward
    success = execute_transaction(w3, account, contract, 'claimReward')
    
    # 如果 claimReward 成功，检查并执行 claimBuffer
    if success and check_buffer(w3, account, contract):
        print(f"账户 {account['name']} 检测到buffer，执行claimBuffer...")
        success = execute_transaction(w3, account, contract, 'claimBuffer')
    
    return success

def main():
    # 解析命令行参数
    args = parse_arguments()
    
    # 加载配置
    config = load_config(args.config)
    
    # 设置 Web3
    w3 = setup_web3()
    
    # 检查连接
    if not w3.is_connected():
        print("无法连接到区块链网络！")
        return

    # 创建合约实例
    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)

    # 遍历所有账户
    for i, account in enumerate(config['accounts']):
        success = process_account(w3, account, contract)
        
        # 如果不是最后一个账户，根据调用结果决定等待时间
        if i < len(config['accounts']) - 1:
            if success:
                delay = random.randint(30, 50)
                print(f"调用成功，等待 {delay} 秒后继续...")
            else:
                delay = random.randint(3, 5)
                print(f"调用失败，等待 {delay} 秒后继续...")
            time.sleep(delay)

if __name__ == "__main__":
    main() 