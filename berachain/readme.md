

# Berachain 自动交互脚本

自动执行 Berachain 测试网上的一系列 DeFi 操作。

## 功能特点

- Swap BERA 到 stgUSDC（随机 0.5-0.8 BERA）
- 将 stgUSDC 换成 HONEY
- 向 Bend 协议质押部分 HONEY
- 向 BERPS 协议质押部分 HONEY
- 质押全部 bHONEY
- 自动处理所有授权操作
- 随机延时执行
- 详细的执行日志

## 配置说明

1. 安装依赖：
  pip install -r requirements.txt
2、创建配置文件 config.yaml，添加以下内容：
berachain:
 private_key: "your_private_key" # 私钥，不要带 0x 前缀
 address: "your_address" # 地址，需要带 0x 前缀


## 合约地址

- SWAP 合约：0x21e2C0AFd058A89FCf7caf3aEA3cB84Ae977B73D
- STGUSDC：0xd6D83aF58a19Cd14eF3CF6fe848C9A4d21e5727c
- HONEY：0x0E4aaF1351de4c0264C5c7056Ef3777b41BD8e03
- HONEY MINT：0xAd1782b2a7020631249031618fB1Bd09CD926b31
- BEND：0x30A3039675E5b5cbEA49d9a5eacbc11f9199B86D
- BERPS：0x1306D3c36eC7E38dd2c128fBe3097C2C2449af64
- BERPS STAKE：0xC5Cb3459723B828B3974f7E58899249C2be3B33d

## 使用方法

1. 运行自动化脚本：
python berachain/bera_auto.py config.yaml
2. 单独运行各个功能：
Swap BERA 到 stgUSDC
python berachain/bera_swap.py
Mint HONEY
python berachain/bera_mint_honey.py
向 Bend 质押 HONEY
python berachain/bera_bend_supply.py
向 BERPS 质押 HONEY
python berachain/bera_berps_deposit.py
质押 bHONEY
python berachain/bera_berps_stake.py


## 执行流程

1. Swap：将 0.5-0.8 BERA 随机兑换成 stgUSDC
2. Mint：将全部 stgUSDC 兑换成 HONEY
3. Bend：将部分 HONEY 质押到 Bend 协议
4. BERPS：将部分 HONEY 质押到 BERPS 协议获得 bHONEY
5. Stake：将获得的 bHONEY 进行质押

每个步骤之间会有随机延时（5-10秒），最后一步之前延时 1-5 秒。

## 注意事项

1. 请确保账户中有足够的 BERA 用于支付 gas 费用
2. 私钥请妥善保管，不要泄露给他人
3. 建议先用小额测试脚本功能
4. 每个操作都会先检查授权，未授权会自动处理
5. 如果某一步失败，后续步骤将不会执行

## 错误处理

- 每个操作都有详细的错误日志输出
- 可以查看交易哈希在区块浏览器上查询具体原因
- 常见错误包括：gas 不足、滑点过大、余额不足等

## 安全建议

1. 使用专门的测试账户运行脚本
2. 定期检查账户余额和交易历史
3. 不要将私钥明文保存在代码中
4. 建议使用环境变量或加密方式存储私钥



