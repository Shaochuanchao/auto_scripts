from web3 import Web3
import json
import time
import random

# 固定配置
RPC_URL = "https://bartio.rpc.berachain.com/"
SWAP_CONTRACT = "0x21e2C0AFd058A89FCf7caf3aEA3cB84Ae977B73D"  # 需要替换为实际的合约地址
BERA_ADDRESS = "0x0000000000000000000000000000000000000000"
STGUSDC_ADDRESS = "0xd6D83aF58a19Cd14eF3CF6fe848C9A4d21e5727c"

# 合约 ABI
ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "uint256", "name": "poolIdx", "type": "uint256"},
                    {"internalType": "address", "name": "base", "type": "address"},
                    {"internalType": "address", "name": "quote", "type": "address"},
                    {"internalType": "bool", "name": "isBuy", "type": "bool"}
                ],
                "internalType": "struct SwapHelpers.SwapStep[]",
                "name": "_steps",
                "type": "tuple[]"
            },
            {"internalType": "uint128", "name": "_amount", "type": "uint128"},
            {"internalType": "uint128", "name": "_minOut", "type": "uint128"}
        ],
        "name": "multiSwap",
        "outputs": [
            {"internalType": "uint128", "name": "out", "type": "uint128"}
        ],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "uint256", "name": "poolIdx", "type": "uint256"},
                    {"internalType": "address", "name": "base", "type": "address"},
                    {"internalType": "address", "name": "quote", "type": "address"},
                    {"internalType": "bool", "name": "isBuy", "type": "bool"}
                ],
                "internalType": "struct SwapHelpers.SwapStep[]",
                "name": "_steps",
                "type": "tuple[]"
            },
            {"internalType": "uint128", "name": "_amount", "type": "uint128"}
        ],
        "name": "previewMultiSwap",
        "outputs": [
            {"internalType": "uint128", "name": "out", "type": "uint128"},
            {"internalType": "uint256", "name": "predictedQty", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

def setup_web3():
    """初始化 Web3"""
    return Web3(Web3.HTTPProvider(RPC_URL))

def get_min_out(w3, contract, steps, amount):
    """
    使用 previewMultiSwap 获取预期输出量
    返回的数量会作为 multiSwap 的 minOut 参数
    如果获取失败则返回默认值
    """
    try:
        out, predicted = contract.functions.previewMultiSwap(
            steps,
            amount
        ).call()
        
        # 设置滑点容忍度为 5%
        min_out = int(out * 0.95)  # 增加滑点容忍度到5%
        print(f"预期输出: {out}")
        print(f"考虑滑点后的最小输出: {min_out}")
        return min_out
    except Exception as e:
        print(f"获取预期输出失败：{str(e)}")
        # 返回一个较小的默认值
        if amount == w3.to_wei(0.5, 'ether'):
            default_min_out = 7275991  # 使用成功交易的参数
        else:
            # 按比例计算默认值
            ratio = amount / w3.to_wei(0.5, 'ether')
            default_min_out = int(7275991 * ratio * 0.95)  # 添加5%滑点
        print(f"使用默认最小输出值: {default_min_out}")
        return default_min_out

def swap_bera_to_stgusdc(w3, account, amount_in_bera=None):
    """
    将 BERA 换成 stgUSDC
    w3: Web3 实例
    account: 账户信息 dict，包含 private_key 和 address
    amount_in_bera: 输入的 BERA 数量，如果不指定则在 0.5-0.8 之间随机
    """
    try:
        # 如果没有指定金额，则随机生成
        if amount_in_bera is None:
            amount_in_bera = round(random.uniform(0.5, 0.8), 2)
            print(f"随机生成交易金额: {amount_in_bera} BERA")
        
        # 创建合约实例
        contract = w3.eth.contract(address=SWAP_CONTRACT, abi=ABI)
        
        # 修改 steps 结构以匹配成功交易
        steps = [{
            "poolIdx": 36000,
            "base": BERA_ADDRESS,
            "quote": STGUSDC_ADDRESS,
            "isBuy": True
        }]
        
        # 将 BERA 数量转换为 Wei
        amount = w3.to_wei(amount_in_bera, 'ether')
        print(f"转换后的 Wei 金额: {amount}")
        
        # 获取预期最小输出量
        min_out = get_min_out(w3, contract, steps, amount)
        print(f"使用的 min_out 值: {min_out}")
        
        # 构建交易前先模拟调用验证参数
        try:
            print("\n--- 开始交易参数验证 ---")
            print("Steps:", steps)
            print("Amount:", amount)
            print("Min Out:", min_out)
            
            result = contract.functions.multiSwap(
                steps,
                amount,
                min_out
            ).call({
                'from': account['address'],
                'value': amount
            })
            print("交易参数验证成功，预期返回值:", result)
        except Exception as call_error:
            print("\n交易参数验证失败:")
            print(f"错误类型: {type(call_error).__name__}")
            print(f"错误信息: {str(call_error)}")
            if hasattr(call_error, 'args'):
                print(f"错误参数: {call_error.args}")
            return False

        # 构建交易
        transaction = contract.functions.multiSwap(
            steps,
            amount,
            min_out
        ).build_transaction({
            'from': account['address'],
            'value': amount,  # 附带 BERA
            'nonce': w3.eth.get_transaction_count(account['address']),
            'gas': 300000,
            'gasPrice': w3.eth.gas_price
        })
        
        print("交易参数：")
        print(f"From: {transaction['from']}")
        print(f"Value: {transaction['value']}")
        print(f"Gas: {transaction['gas']}")
        print(f"Gas Price: {transaction['gasPrice']}")
        print(f"Nonce: {transaction['nonce']}")

        try:
            # 尝试估算 gas
            gas_estimate = contract.functions.multiSwap(
                steps,
                amount,
                min_out
            ).estimate_gas({
                'from': account['address'],
                'value': amount
            })
            print(f"估算的 gas 限制: {gas_estimate}")
        except Exception as gas_error:
            print(f"Gas 估算失败: {str(gas_error)}")

        # 签名交易
        try:
            signed_txn = w3.eth.account.sign_transaction(
                transaction, account['private_key']
            )
            print("交易签名成功")
        except Exception as sign_error:
            print(f"交易签名失败: {str(sign_error)}")
            return False

        # 发送交易
        try:
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            print(f"交易已发送，哈希: {tx_hash.hex()}")
        except Exception as send_error:
            print(f"发送交易失败: {str(send_error)}")
            return False
        
        # 等待交易确认
        try:
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            print("交易状态：", "成功" if receipt['status'] == 1 else "失败")
            print(f"Gas 使用: {receipt['gasUsed']}")
            
            if receipt['status'] == 1:
                print(f"Swap 成功！交易哈希: {tx_hash.hex()}")
                return True
            else:
                # 尝试获取失败原因
                try:
                    # 模拟交易来获取具体错误
                    contract.functions.multiSwap(
                        steps,
                        amount,
                        min_out
                    ).call({
                        'from': account['address'],
                        'value': amount
                    })
                except Exception as call_error:
                    print(f"交易失败原因: {str(call_error)}")
                return False
                
        except Exception as receipt_error:
            print(f"获取交易回执失败: {str(receipt_error)}")
            return False
            
    except Exception as e:
        print(f"Swap 执行过程中发生错误：")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        if hasattr(e, 'args'):
            print(f"错误参数: {e.args}")
        return False

def main():
    # 设置 Web3
    w3 = setup_web3()
    
    # 检查连接
    if not w3.is_connected():
        print("无法连接到 Berachain 网络！")
        return

    print("开始执行 Swap...")
    # 这里仅作为单独测试使用
    test_account = {
        "private_key": "YOUR_PRIVATE_KEY",
        "address": "YOUR_ADDRESS"
    }
    success = swap_bera_to_stgusdc(w3, test_account)
    
    if success:
        print("Swap 执行完成！")
    else:
        print("Swap 执行失败！")

if __name__ == "__main__":
    main() 