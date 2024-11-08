from web3 import Web3
import json
import time
import random

# 固定配置
RPC_URL = "https://bartio.rpc.berachain.com/"
HONEY_ADDRESS = "0x0E4aaF1351de4c0264C5c7056Ef3777b41BD8e03"
BERPS_CONTRACT = "0x1306D3c36eC7E38dd2c128fBe3097C2C2449af64"

# Honey Token ABI
HONEY_ABI = [
    {
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "result", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "result", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# BERPS 合约 ABI
BERPS_ABI = [
    {
        "inputs": [
            {"name": "assets", "type": "uint256"},
            {"name": "receiver", "type": "address"}
        ],
        "name": "deposit",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

def get_honey_balance(w3, account, honey_contract):
    """获取账户的 Honey 余额"""
    balance = honey_contract.functions.balanceOf(account['address']).call()
    print(f"Honey 余额: {w3.from_wei(balance, 'ether')} HONEY")
    return balance

def check_and_approve_honey(w3, account, honey_contract, amount):
    """检查并授权 Honey"""
    try:
        # 检查当前授权额度
        current_allowance = honey_contract.functions.allowance(
            account['address'],
            BERPS_CONTRACT
        ).call()
        
        print(f"当前授权额度: {w3.from_wei(current_allowance, 'ether')} HONEY")
        
        if current_allowance < amount:
            print("需要授权 Honey...")
            # 构建授权交易
            approve_txn = honey_contract.functions.approve(
                BERPS_CONTRACT,
                amount
            ).build_transaction({
                'from': account['address'],
                'nonce': w3.eth.get_transaction_count(account['address']),
                'gas': 100000,
                'gasPrice': w3.eth.gas_price
            })
            
            # 签名并发送交易
            signed_txn = w3.eth.account.sign_transaction(
                approve_txn,
                account['private_key']
            )
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # 等待交易确认
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt['status'] == 1:
                print(f"授权成功！交易哈希: {tx_hash.hex()}")
                return True
            else:
                print("授权失败！")
                return False
        else:
            print("已有足够的授权额度")
            return True
            
    except Exception as e:
        print(f"授权过程出错: {str(e)}")
        return False

def deposit_honey(w3, account, amount_in_honey=None):
    """
    向 BERPS 协议质押 Honey
    w3: Web3 实例
    account: 账户信息 dict，包含 private_key 和 address
    amount_in_honey: 质押的 Honey 数量，如果不指定则随机生成
    """
    try:
        # 创建合约实例
        honey_contract = w3.eth.contract(address=HONEY_ADDRESS, abi=HONEY_ABI)
        berps_contract = w3.eth.contract(address=BERPS_CONTRACT, abi=BERPS_ABI)
        
        # 获取账户余额
        balance = get_honey_balance(w3, account, honey_contract)
        balance_in_eth = float(w3.from_wei(balance, 'ether'))  # 转换为 float
        
        # 如果没有指定金额，则随机生成（2-余额的一半）
        if amount_in_honey is None:
            max_amount = min(balance_in_eth / 2, 2)
            if max_amount < 1:
                amount_in_honey = 1
            else:
                amount_in_honey = round(random.uniform(2, max_amount), 2)
            print(f"随机生成质押金额: {amount_in_honey} HONEY")
        
        # 转换为 Wei
        amount = w3.to_wei(amount_in_honey, 'ether')
        
        # 检查并授权
        if not check_and_approve_honey(w3, account, honey_contract, amount):
            return False
            
        print(f"\n开始质押 {amount_in_honey} HONEY...")
        
        # 构建质押交易
        deposit_txn = berps_contract.functions.deposit(
            amount,
            account['address']
        ).build_transaction({
            'from': account['address'],
            'nonce': w3.eth.get_transaction_count(account['address']),
            'gas': 300000,
            'gasPrice': w3.eth.gas_price
        })
        
        # 签名交易
        signed_txn = w3.eth.account.sign_transaction(
            deposit_txn,
            account['private_key']
        )
        
        # 发送交易
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(f"质押交易已发送，哈希: {tx_hash.hex()}")
        
        # 等待交易确认
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt['status'] == 1:
            print(f"质押成功！交易哈希: {tx_hash.hex()}")
            print(f"Gas 使用: {receipt['gasUsed']}")
            return True
        else:
            print("质押失败！")
            return False
            
    except Exception as e:
        print(f"质押过程出错: {str(e)}")
        return False

def main():
    # 设置 Web3
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    
    # 检查连接
    if not w3.is_connected():
        print("无法连接到 Berachain 网络！")
        return

    print("开始执行质押...")
    # 这里仅作为单独测试使用
    test_account = {
        "private_key": "YOUR_PRIVATE_KEY",
        "address": "YOUR_ADDRESS"
    }
    success = deposit_honey(w3, test_account)
    
    if success:
        print("质押执行完成！")
    else:
        print("质押执行失败！")

if __name__ == "__main__":
    main() 