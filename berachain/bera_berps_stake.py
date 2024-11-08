from web3 import Web3
import json
import time
import random

# 固定配置
RPC_URL = "https://bartio.rpc.berachain.com/"
BHONEY_ADDRESS = "0x1306D3c36eC7E38dd2c128fBe3097C2C2449af64"  # bHONEY 合约地址
STAKE_CONTRACT = "0xC5Cb3459723B828B3974f7E58899249C2be3B33d"  # 质押合约地址

# bHONEY Token ABI
BHONEY_ABI = [
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

# 质押合约 ABI
STAKE_ABI = [
    {
        "inputs": [
            {"name": "amount", "type": "uint256"}
        ],
        "name": "stake",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

def get_bhoney_balance(w3, account, bhoney_contract):
    """获取账户的 bHONEY 余额"""
    balance = bhoney_contract.functions.balanceOf(account['address']).call()
    print(f"bHONEY 余额: {w3.from_wei(balance, 'ether')} bHONEY")
    return balance

def check_and_approve_bhoney(w3, account, bhoney_contract, amount):
    """检查并授权 bHONEY"""
    try:
        # 检查当前授权额度
        current_allowance = bhoney_contract.functions.allowance(
            account['address'],
            STAKE_CONTRACT
        ).call()
        
        print(f"当前授权额度: {w3.from_wei(current_allowance, 'ether')} bHONEY")
        
        if current_allowance < amount:
            print("需要授权 bHONEY...")
            # 构建授权交易
            approve_txn = bhoney_contract.functions.approve(
                STAKE_CONTRACT,
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

def stake_bhoney(w3, account, amount_in_bhoney=None):
    """
    质押 bHONEY
    w3: Web3 实例
    account: 账户信息 dict，包含 private_key 和 address
    amount_in_bhoney: 质押的 bHONEY 数量，如果不指定则使用全部余额
    """
    try:
        # 创建合约实例
        bhoney_contract = w3.eth.contract(address=BHONEY_ADDRESS, abi=BHONEY_ABI)
        stake_contract = w3.eth.contract(address=STAKE_CONTRACT, abi=STAKE_ABI)
        
        # 获取账户余额
        balance = get_bhoney_balance(w3, account, bhoney_contract)
        
        # 如果没有指定金额，则使用全部余额
        if amount_in_bhoney is None:
            amount = balance
            amount_in_bhoney = w3.from_wei(balance, 'ether')
            print(f"使用全部余额质押: {amount_in_bhoney} bHONEY")
        else:
            amount = w3.to_wei(amount_in_bhoney, 'ether')
        
        # 检查并授权
        if not check_and_approve_bhoney(w3, account, bhoney_contract, amount):
            return False
            
        print(f"\n开始质押 {amount_in_bhoney} bHONEY...")
        
        # 构建质押交易
        stake_txn = stake_contract.functions.stake(
            amount
        ).build_transaction({
            'from': account['address'],
            'nonce': w3.eth.get_transaction_count(account['address']),
            'gas': 300000,
            'gasPrice': w3.eth.gas_price
        })
        
        # 签名交易
        signed_txn = w3.eth.account.sign_transaction(
            stake_txn,
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
    success = stake_bhoney(w3, test_account)
    
    if success:
        print("质押执行完成！")
    else:
        print("质押执行失败！")

if __name__ == "__main__":
    main() 