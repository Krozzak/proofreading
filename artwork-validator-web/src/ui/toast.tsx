// Minimal toast system (no dependency): toast('message') from anywhere,
// <Toaster /> renders the stack bottom-right.
import { useEffect, useState } from 'react'

interface ToastItem {
  id: number
  message: string
  kind: 'info' | 'success' | 'error'
}

type Listener = (item: ToastItem) => void

let nextId = 1
const listeners = new Set<Listener>()

export function toast(message: string, kind: ToastItem['kind'] = 'info'): void {
  const item = { id: nextId++, message, kind }
  listeners.forEach((l) => l(item))
}

export function Toaster() {
  const [items, setItems] = useState<ToastItem[]>([])

  useEffect(() => {
    const listener: Listener = (item) => {
      setItems((prev) => [...prev, item])
      setTimeout(() => {
        setItems((prev) => prev.filter((i) => i.id !== item.id))
      }, 3500)
    }
    listeners.add(listener)
    return () => {
      listeners.delete(listener)
    }
  }, [])

  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {items.map((item) => (
        <div
          key={item.id}
          className={
            'pointer-events-auto rounded-lg px-4 py-2 text-sm text-white shadow-lg ' +
            (item.kind === 'success'
              ? 'bg-emerald-600'
              : item.kind === 'error'
                ? 'bg-red-600'
                : 'bg-neutral-800')
          }
        >
          {item.message}
        </div>
      ))}
    </div>
  )
}
