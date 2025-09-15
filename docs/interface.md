以下是基于代码的接口定义总结表格：

| 类别 | 方法 | 端点 | 功能描述 | 请求体/参数 | 响应 |
|------|------|------|----------|-------------|------|
| **对话管理** | POST | `/conversations` | 创建新对话 | `{"title": "string"}` | `201`: 创建成功，返回对话信息 |
|  | GET | `/conversations` | 获取所有对话 | 无 | `200`: 返回对话列表 |
|  | GET | `/conversations/<int:conversation_id>` | 获取单个对话 | URL参数: conversation_id | `200`: 返回对话详情；`404`: 未找到 |
|  | DELETE | `/conversations/<int:conversation_id>` | 删除对话 | URL参数: conversation_id | `200`: 删除成功；`404`: 未找到；`500`: 删除失败 |
|  | PUT | `/conversations/<int:conversation_id>` | 更新对话标题 | URL参数: conversation_id<br>Body: `{"title": "string"}` | `200`: 更新成功；`400`: 数据无效；`404`: 未找到；`500`: 更新失败 |
| **消息管理** | GET | `/conversations/<int:conversation_id>/messages/recent` | 获取最近消息 | URL参数: conversation_id<br>Query: `?limit=500` | `200`: 返回消息列表 |
|  | POST | `/conversations/<int:conversation_id>/messages` | 创建新消息 | URL参数: conversation_id<br>Body: `{"role": "string", "content": "string"}` | `201`: 创建成功，返回消息信息；`400`: 数据无效 |
|  | POST | `/conversations/<int:conversation_id>/stream` | 流式创建消息 | URL参数: conversation_id<br>Body: `{"content": "string"}` | SSE流: 实时返回消息片段，最后保存完整消息 |
|  | GET | `/messages/<int:message_id>` | 获取特定消息 | URL参数: message_id | `200`: 返回消息详情；`404`: 未找到 |
|  | DELETE | `/messages/<int:message_id>` | 删除特定消息 | URL参数: message_id | `200`: 删除成功；`404`: 未找到；`500`: 删除失败 |
|  | GET | `/conversations/<int:conversation_id>/messages` | 获取对话所有消息 | URL参数: conversation_id | `200`: 返回消息列表 |
|  | DELETE | `/conversations/<int:conversation_id>/messages` | 删除对话所有消息 | URL参数: conversation_id | `200`: 删除成功；`500`: 删除失败 |

**主要功能说明：**

1. **对话管理**：完整的CRUD操作，支持创建、查询、更新和删除对话
2. **消息管理**：
   - 支持普通消息创建和流式消息创建
   - 支持按消息ID和对话ID查询消息
   - 支持删除单个消息或整个对话的所有消息
   - 流式接口使用Server-Sent Events (SSE) 技术实时返回AI响应

**错误处理：**
- 所有接口都使用统一的错误处理装饰器
- 返回适当的HTTP状态码和错误信息
- 服务端错误会记录日志

**数据验证：**
- 验证必需的请求字段
- 验证数据类型（字符串类型）
- 验证资源存在性（对话/消息是否存在）