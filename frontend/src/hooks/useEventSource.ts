import { useEffect, useRef, useCallback } from 'react'

export function useEventSource(url: string, onMessage: (data: unknown) => void) {
  const esRef = useRef<EventSource | null>(null)
  const onMessageRef = useRef(onMessage)
  onMessageRef.current = onMessage

  const connect = useCallback(() => {
    if (esRef.current) esRef.current.close()
    const es = new EventSource(url)
    esRef.current = es

    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        if (data?.type !== 'connected') {
          onMessageRef.current(data)
        }
      } catch {
        // keepalive o comentario, ignorar
      }
    }

    es.onerror = () => {
      es.close()
      setTimeout(connect, 3000)
    }
  }, [url])

  useEffect(() => {
    connect()
    return () => esRef.current?.close()
  }, [connect])
}
