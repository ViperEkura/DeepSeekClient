class StreamReceiverService {
  constructor() {
    this.activeStreams = new Map() // key: conversationId, value: { messages[], controller }
  }

  startStream(conversationId, inputText, apiBaseUrl) {
    if (this.activeStreams.has(conversationId)) {
      console.warn('Stream already active for conversation', conversationId)
      return
    }

    const controller = new AbortController()
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
      .then(res => res.body.getReader())
      .then(reader => {
        const decoder = new TextDecoder()
        let buf = ''

        const pump = ({ done, value }) => {
          if (done) {
            streamData.isDone = true
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
              console.warn('parse error', e)
            }
          }
          return reader.read().then(pump)
        }
        return reader.read().then(pump)
      })
      .catch(err => {
        console.error('Stream error', err)
      })
      .finally(() => {
        streamData.isDone = true
      })
  }

  getStreamData(conversationId) {
    return this.activeStreams.get(conversationId)
  }

  cancelStream(conversationId) {
    const data = this.activeStreams.get(conversationId)
    if (data) {
      data.controller.abort()
      this.activeStreams.delete(conversationId)
    }
  }
}

export default new StreamReceiverService()