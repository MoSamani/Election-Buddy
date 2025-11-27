'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'

type RagSource = {
  document_id: number
  chunk_index: number
  title: string
  meta?: Record<string, any> | null
  score: number
}

type RagAnswerResponse = {
  question: string
  answer: string
  sources: RagSource[]
}

type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: RagSource[]
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000'

export default function HomePage() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSend(e: React.FormEvent) {
    e.preventDefault()
    if (!input.trim() || loading) return

    const question = input.trim()
    setInput('')
    setError(null)

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: question,
    }
    setMessages((prev) => [...prev, userMessage])

    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/rag_answer/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question,
          top_k: 3,
        }),
      })

      if (!res.ok) {
        const txt = await res.text()
        throw new Error(`HTTP ${res.status}: ${txt}`)
      }

      const data: RagAnswerResponse = await res.json()

      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: data.answer,
        sources: data.sources,
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (err: any) {
      console.error(err)
      setError(err.message ?? 'Fehler beim Abrufen der Antwort')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4 py-6">
      <div className="w-full max-w-4xl space-y-4">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">
              RAG Science Chat
            </h1>
            <p className="text-sm text-slate-400">
              Stelle dein RAG-System Fragen zu wissenschaftlichen
              Sachverhalten..
            </p>
          </div>
        </header>

        <Card className="border-slate-800 bg-slate-900/60 backdrop-blur">
          <CardHeader className="pb-3">
            <p className="text-sm text-slate-300">
              Stelle eine Frage, z.&nbsp;B.:{' '}
              <button
                className="underline decoration-dotted text-sky-300 hover:text-sky-200"
                onClick={() =>
                  setInput(
                    'Wie sicher sind mRNA-Impfstoffe laut aktueller Forschung?'
                  )
                }
              >
                „Wie sicher sind mRNA-Impfstoffe?“
              </button>
            </p>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <ScrollArea className="h-[360px] rounded-md border border-slate-800 bg-slate-950/40 px-3 py-2">
              {messages.length === 0 ? (
                <div className="flex h-full items-center justify-center text-sm text-slate-500">
                  Noch keine Fragen gestellt. Starte den Dialog oben.
                </div>
              ) : (
                <div className="space-y-3">
                  {messages.map((m) => (
                    <ChatBubble key={m.id} message={m} />
                  ))}
                </div>
              )}
            </ScrollArea>

            {error && (
              <div className="rounded-md border border-red-500/60 bg-red-950/40 px-3 py-2 text-xs text-red-200">
                {error}
              </div>
            )}

            <form onSubmit={handleSend} className="flex gap-2 pt-1">
              <Input
                placeholder="Stelle eine Frage zur Studie, z. B. zu Wirksamkeit oder Risiken …"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={loading}
                className="border-slate-700 bg-slate-950/60 text-slate-50 placeholder:text-slate-400"
              />
              <Button type="submit" disabled={loading || !input.trim()}>
                {loading ? 'Analysiere…' : 'Senden'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user'

  return (
    <div
      className={`flex w-full ${
        isUser ? 'justify-end' : 'justify-start'
      } text-sm`}
    >
      <div
        className={`max-w-[80%] space-y-2 rounded-2xl px-4 py-3 shadow-md ${
          isUser
            ? 'bg-sky-600 text-white'
            : 'bg-slate-800 text-slate-100 border border-slate-700'
        }`}
      >
        {/* Chat Message */}
        <div className="whitespace-pre-wrap leading-relaxed">
          {message.content}
        </div>

        {/* Sources */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="pt-2 border-t border-slate-700/60 space-y-1">
            <p className="text-[10px] uppercase tracking-wide text-slate-400">
              Quellen
            </p>
            <ul className="space-y-1">
              {message.sources.map((s) => {
                const year =
                  s.meta?.year ?? s.meta?.Year ?? s.meta?.YEAR ?? 'unbekannt'
                const journal =
                  s.meta?.journal ??
                  s.meta?.source ??
                  s.meta?.Journal ??
                  'Quelle unbekannt'
                const peerReviewed =
                  s.meta?.peer_reviewed === true ||
                  s.meta?.peerReviewed === true

                return (
                  <li
                    key={`${s.document_id}-${s.chunk_index}`}
                    className="text-[11px] text-slate-300"
                  >
                    <span className="font-medium text-slate-100">
                      {s.title}
                    </span>{' '}
                    <span className="text-slate-400">
                      ({journal}, {year})
                    </span>
                    {peerReviewed && (
                      <span className="ml-2 rounded-full bg-emerald-700 px-2 py-[1px] text-[10px] text-emerald-50">
                        peer-reviewed
                      </span>
                    )}
                  </li>
                )
              })}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}
