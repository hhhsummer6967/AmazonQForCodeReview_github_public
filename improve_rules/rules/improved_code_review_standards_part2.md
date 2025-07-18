### 3.3 功能实现

- **需求符合度**
  - 代码是否完全实现了需求
  - 是否处理了所有用例场景
  - 是否符合产品规格说明

- **参数校验**
  - 所有外部输入必须进行校验（如非空检查、类型检查、范围检查等）
  - 遵循先检查、后处理的原则
  - 对数据库字段长度限制进行相应的输入长度校验

- **判空处理**
  - 获取对象的属性前进行判空处理，避免空指针异常
  - 遍历列表前进行判空检查
  - 外部调用返回结果进行判空处理

- **错误处理**
  - 不要捕获通用的Exception异常，而应该捕获特定的异常
  - 在捕获异常时，记录异常信息以便于调试
  - 在finally块中释放资源，或者使用try-with-resource
  - 不要使用e.printStackTrace()，而是使用log打印
  - 捕获到的异常不能忽略，要打印相应的日志
  - 注意异常匹配的顺序，优先捕获具体的异常
  - 对外提供API时，提供对应的错误码
  - 系统内部应抛出有业务含义的自定义异常

- **边界条件处理**
  - 处理空值/null
  - 处理空集合/数组
  - 处理最小/最大值
  - 处理溢出情况
  - 处理特殊字符
  - 处理格式错误的输入

### 3.4 安全性

- **输入验证和数据清洗**
  - 对所有外部输入进行验证
  - 使用白名单而非黑名单验证
  - 验证数据类型、范围和格式
  - 在服务器端进行验证（而非仅客户端）

- **输出编码**
  - 对HTML输出进行编码（防XSS）
  - 对SQL查询参数化（防SQL注入）
  - 对命令行参数进行转义（防命令注入）
  - 对URL参数进行编码
  - 对JSON输出进行验证

- **认证和授权**
  - 验证用户身份
  - 检查操作权限
  - 实施最小权限原则
  - 避免硬编码凭证
  - 安全存储敏感信息
  - 使用安全的会话管理

- **敏感数据处理**
  - 敏感数据加密存储
  - 敏感数据加密传输
  - 避免日志中的敏感信息
  - 安全处理临时文件
  - 实施适当的访问控制
  - 日志中的敏感信息（如手机号、身份证等）需要脱敏处理

- **防范常见安全漏洞**
  - 防范跨站脚本攻击（XSS）
  - 防范SQL注入攻击
  - 防范跨站请求伪造（CSRF）
  - 防范会话劫持
  - 防范点击劫持
  - 防范目录遍历

### 3.5 性能与效率

- **算法效率**
  - 选择适当的算法
  - 优化时间复杂度
  - 优化空间复杂度
  - 避免不必要的计算
  - 避免重复计算（如使用缓存或记忆化）

- **资源使用**
  - 及时释放资源（文件句柄、连接等）
  - 避免内存泄漏
  - 避免不必要的对象创建
  - 使用对象池（如适用）
  - 避免过度使用内存

- **数据库操作**
  - 查询是否高效
  - 使用适当的索引
  - 批处理操作
  - 避免N+1查询问题
  - 使用连接池
  - 使用事务（如需要）
  - 避免循环调用数据库操作
  - 查询SQL时，如果条数不明确，加limit限制
  - 数据库的返回进行判空处理

- **并发处理**
  - 正确处理并发访问
  - 避免死锁
  - 避免竞态条件
  - 使用适当的锁粒度
  - 使用线程安全的数据结构
  - 正确使用异步/并行处理
