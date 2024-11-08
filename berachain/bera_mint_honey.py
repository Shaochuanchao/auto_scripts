from web3 import Web3
import json
import time
import random

# 固定配置
RPC_URL = "https://bartio.rpc.berachain.com/"
STGUSDC_ADDRESS = "0xd6D83aF58a19Cd14eF3CF6fe848C9A4d21e5727c"
HONEY_MINT_CONTRACT = "0xAd1782b2a7020631249031618fB1Bd09CD926b31"

# STGUSDC 的 ABI
STGUSDC_ABI = [
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
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "result", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "result", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# Honey Mint 合约 ABI
HONEY_MINT_ABI = [
    {
        "inputs": [
            {"name": "asset", "type": "address"},
            {"name": "amount", "type": "uint256"},
            {"name": "receiver", "type": "address"}
        ],
        "name": "mint",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "asset", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "previewMint",
        "outputs": [{"name": "honeyAmount", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

def check_and_approve_stgusdc(w3, account, stgusdc_contract, amount):
    """检查并授权 stgUSDC"""
    try:
        # 检查当前授权额度
        current_allowance = stgusdc_contract.functions.allowance(
            account['address'],
            HONEY_MINT_CONTRACT
        ).call()
        
        print(f"当前授权额度: {current_allowance}")
        
        if current_allowance < amount:
            print("需要授权 stgUSDC...")
            # 构建授权交易
            approve_txn = stgusdc_contract.functions.approve(
                HONEY_MINT_CONTRACT,
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

def mint_honey(w3, account, amount_in_usdc=None):
    """
    将 stgUSDC 换成 honey
    w3: Web3 实例
    account: 账户信息 dict，包含 private_key 和 address
    amount_in_usdc: 输入的 stgUSDC 数量，如果不指定则使用全部余额
    """
    try:
        # 创建合约实例
        stgusdc_contract = w3.eth.contract(address=STGUSDC_ADDRESS, abi=STGUSDC_ABI)
        honey_contract = w3.eth.contract(address=HONEY_MINT_CONTRACT, abi=HONEY_MINT_ABI)
        
        # 获取 stgUSDC 余额
        balance = stgusdc_contract.functions.balanceOf(account['address']).call()
        print(f"stgUSDC 余额: {balance}")
        
        # 如果没有指定金额，使用全部余额
        amount = amount_in_usdc if amount_in_usdc is not None else balance
        print(f"将要使用的 stgUSDC 数量: {amount}")
        
        # 检查并授权
        if not check_and_approve_stgusdc(w3, account, stgusdc_contract, amount):
            return False
            
        try:
            # 预览 mint 数量
            honey_amount = honey_contract.functions.previewMint(
                STGUSDC_ADDRESS,
                amount
            ).call()
            print(f"预计可以获得的 honey 数量: {honey_amount}")
        except Exception as e:
            print(f"预览 mint 数量失败: {str(e)}")
        
        # 构建 mint 交易
        mint_txn = honey_contract.functions.mint(
            STGUSDC_ADDRESS,
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
            mint_txn,
            account['private_key']
        )
        
        # 发送交易
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(f"Mint 交易已发送，哈希: {tx_hash.hex()}")
        
        # 等待交易确认
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt['status'] == 1:
            print(f"Mint 成功！交易哈希: {tx_hash.hex()}")
            print(f"Gas 使用: {receipt['gasUsed']}")
            return True
        else:
            print("Mint 失败！")
            return False
            
    except Exception as e:
        print(f"Mint 过程出错: {str(e)}")
        return False

def main():
    # 设置 Web3
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    
    # 检查连接
    if not w3.is_connected():
        print("无法连接到 Berachain 网络！")
        return

    print("开始执行 Mint...")
    # 这里仅作为单独测试使用
    test_account = {
        "private_key": "YOUR_PRIVATE_KEY",
        "address": "YOUR_ADDRESS"
    }
    success = mint_honey(w3, test_account)
    
    if success:
        print("Mint 执行完成！")
    else:
        print("Mint 执行失败！")

if __name__ == "__main__":
    main() 