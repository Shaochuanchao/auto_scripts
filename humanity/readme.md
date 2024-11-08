# Humanity 测试网自动领取奖励脚本

自动调用 Humanity 测试网上的智能合约 claimReward 和 claimBuffer 方法。

## 功能特点

- 支持多账户配置
- 自动检查领取状态
- 自动检查和领取 buffer
- 随机延时调用（5-10秒）
- 从 YAML 配置文件读取账户信息
- 详细的执行日志
- 自动重试机制
- Gas 价格自动调整

## 配置说明

1. 安装依赖：
 pip install -r requirements.txt

2. 创建配置文件 config.yaml，添加以下内容：

accounts:
   name: "账户1"
    private_key: "your_private_key_1" # 私钥，不要带 0x 前缀
    address: "your_address_1" # 地址，需要带 0x 前缀
   name: "账户2"
    private_key: "your_private_key_2"
    address: "your_address_2"
## 使用方法

运行脚本：
python humanity/humanity_test_claimreward.py config.yaml

## 执行流程

1. 检查账户配置和私钥是否匹配
2. 获取当前周期
3. 检查账户在当前周期的领取状态
4. 如果可以领取，执行 claimReward
5. 检查是否有可领取的 buffer
6. 如果有 buffer，执行 claimBuffer
7. 在每个账户操作之间随机等待 5-10 秒

## 错误处理

- 自动处理交易超时
- 自动重试失败的交易（最多3次）
- 自动调整 gas 价格
- 详细的错误日志输出

## 注意事项

1. 请确保账户中有足够的 gas 费用
2. 私钥请妥善保管，不要泄露给他人
3. 建议先用单个账户测试脚本功能
4. 如果交易长时间未确认，脚本会自动增加 gas 价格重试
5. 每个账户都会先检查是否可以领取，避免无效交易

## 安全建议

1. 使用专门的测试账户运行脚本
2. 定期检查账户余额和交易历史
3. 不要将私钥明文保存在代码中
4. 建议使用环境变量或加密方式存储私钥
5. 确保 config.yaml 文件不会被提交到代码仓库

## 常见问题

1. 交易超时：脚本会自动增加 gas 价格并重试
2. 领取失败：可能是当前周期已领取或未注册
3. Buffer 领取失败：可能是没有可领取的 buffer
4. 私钥错误：脚本会在执行前验证私钥和地址是否匹配