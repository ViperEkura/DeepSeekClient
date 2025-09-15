### 🧩 **Conversation APIs（对话管理）**

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|---------------|-----------|
| POST | `/conversations` | 创建新对话 | `{ "title": "string" }` | 201: `{ message, conversation_id, title, created_at }` |
| GET | `/conversations` | 获取所有对话 | - | 200: `[ { conversation_id, title, created_at } ]` |
| GET | `/conversations/<int:conversation_id>` | 获取指定对话 | - | 200: `{ conversation_id, title, created_at }` |
| PUT | `/conversations/<int:conversation_id>` | 更新对话标题 | `{ "title": "string" }` | 200: `{ message, conversation_id, title, created_at }` |
| DELETE | `/conversations/<int:conversation_id>` | 删除指定对话 | - | 200: `{ message: "Conversation deleted successfully" }` |


### 💬 **Message APIs（消息管理）**

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|---------------|-----------|
| POST | `/conversations/<int:conversation_id>/messages` | 创建新消息 | `{ "role": "string", "content": "string" }` | 201: `{ message, message_id, conversation_id, role, content, timestamp }` |
| GET | `/conversations/<int:conversation_id>/messages` | 获取某对话的所有消息 | - | 200: `[ { message_id, conversation_id, role, content, timestamp } ]` |
| GET | `/conversations/<int:conversation_id>/messages/recent?limit=<int>` | 获取最近消息（默认500条） | Query param: `limit` | 同上 |
| GET | `/messages/<int:message_id>` | 获取单条消息 | - | 200: `{ message_id, conversation_id, role, content, timestamp }` |
| DELETE | `/messages/<int:message_id>` | 删除单条消息 | - | 200: `{ message: "Message deleted successfully" }` |
| DELETE | `/conversations/<int:conversation_id>/messages` | 删除某对话的所有消息 | - | 200: `{ message: "All messages in conversation deleted successfully" }` |



### 🌊 **Streaming API（流式响应）**

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|---------------|-----------|
| POST | `/conversations/<int:conversation_id>/stream` | 流式生成AI回复 | `{ "content": "string" }` | `text/event-stream`：<br>`data: {"type": "chunk", "content": "..."}`<br>`data: {"type": "complete"}` |

