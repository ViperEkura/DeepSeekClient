class StreamReceiverService {
  constructor() {
    this.activeStreams = new Map() // key: conversationId, value: { messages[], controller, isDone }
    this.connectionTimeout = 30000 // 30秒连接超时
  }

  startStream(conversationId, inputText, apiBaseUrl) {
    if (this.activeStreams.has(conversationId)) {
      console.warn('Stream already active for conversation', conversationId)
      return
    }

    const controller = new AbortController()
    const timeoutId = setTimeout(() => {
      controller.abort()
      console.error('Stream connection timeout')
    }, this.connectionTimeout)

    const streamData = {
      messages: [],
      controller,
      isDone: false
    }
    this.activeStreams.set(conversationId, streamData)

    fetch(`${apiBaseUrl}/conversations/${conversationId}/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: inputText }),
      signal: controller.signal
    })
      .then(res => {
        clearTimeout(timeoutId)
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`)
        }
        return res.body.getReader()
      })
      .then(reader => {
        const decoder = new TextDecoder()
        let buf = ''

        const pump = ({ done, value }) => {
          if (done) {
            streamData.isDone = true
            this.cleanupStream(conversationId)
            return
          }

          buf += decoder.decode(value, { stream: true })
          const lines = buf.split('\n')
          buf = lines.pop()

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue
            try {
              const msg = JSON.parse(line.slice(6))
              streamData.messages.push(msg)
            } catch (e) {
              console.warn('parse error', e, 'for line:', line)
            }
          }
          return reader.read().then(pump)
        }
        return reader.read().then(pump)
      })
      .catch(err => {
        clearTimeout(timeoutId)
        console.error('Stream error', err)
        streamData.isDone = true
        this.cleanupStream(conversationId)
      })
  }

  getStreamData(conversationId) {
    return this.activeStreams.get(conversationId)
  }

  // 获取所有活跃的流
  getAllActiveStreams() {
    return this.activeStreams
  }

  // 检查特定对话是否有活跃的流
  hasActiveStream(conversationId) {
    return this.activeStreams.has(conversationId) && !this.activeStreams.get(conversationId).isDone
  }

  cancelStream(conversationId) {
    const data = this.activeStreams.get(conversationId)
    if (data) {
      data.controller.abort()
      this.cleanupStream(conversationId)
    }
  }

  // 清理完成的流
  cleanupStream(conversationId) {
    const data = this.activeStreams.get(conversationId)
    if (data && data.isDone) {
      // 延迟清理，确保所有数据都被处理
      setTimeout(() => {
        this.activeStreams.delete(conversationId)
      }, 5000)
    }
  }

  // 检查是否有活跃的流
  hasActiveStreams() {
    return this.activeStreams.size > 0
  }
}

// 创建全局单例
const streamReceiver = new StreamReceiverService()

// 页面可见性变化时恢复流
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') {
    // 页面重新可见时，可以执行一些恢复操作
    console.log('Page became visible, active streams:', streamReceiver.hasActiveStreams())
  }
})

export default streamReceiver