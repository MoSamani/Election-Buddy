'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Slider } from '@/components/ui/slider'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'

type RagSource = {
  document_id: number
  chunk_index: number
  title: string
  chunk_text: string
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
  const [selectedSource, setSelectedSource] = useState<RagSource | null>(null)
  const [topK, setTopK] = useState<number>(3)

  // 🔹 Neuer State: Peer-reviewed only
  const [peerReviewedOnly, setPeerReviewedOnly] = useState<boolean>(false)

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
          top_k: topK,
          peer_reviewed_only: peerReviewedOnly,
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
    <div className="flex min-h-screen flex-col items-center justify-center px-4 py-6 bg-slate-950">
      <div className="w-full max-w-4xl space-y-4">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-slate-50">
              RAG Science Chat
            </h1>
            <p className="text-sm text-slate-400">
              Stelle dein RAG-System Fragen zu wissenschaftlichen Sachverhalten.
            </p>
          </div>

          {/* 🔹 Modus-Badge (Peer-reviewed / Alle Quellen) */}
          <div className="hidden sm:flex items-center">
            <span
              className={`rounded-full border px-3 py-[3px] text-[10px] uppercase tracking-wide ${
                peerReviewedOnly
                  ? 'border-emerald-500/60 bg-emerald-900/40 text-emerald-200'
                  : 'border-slate-500/60 bg-slate-800/60 text-slate-200'
              }`}
            >
              {peerReviewedOnly ? 'Peer-reviewed only' : 'Alle Quellen'}
            </span>
          </div>
        </header>

        <Card className="border-slate-800 bg-slate-900/60 backdrop-blur">
          <CardHeader className="pb-3">
            <p className="text-sm text-slate-300">
              Stelle eine Frage, z.&nbsp;B.:{' '}
              <button
                type="button"
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
              <div className="space-y-3">
                {messages.map((m) => (
                  <ChatBubble
                    key={m.id}
                    message={m}
                    onSourceClick={(s) => setSelectedSource(s)}
                  />
                ))}

                {loading && (
                  <div className="text-xs text-slate-400">KI denkt nach …</div>
                )}

                {messages.length === 0 && !loading && (
                  <div className="text-xs text-slate-500">
                    Stelle deine erste Frage, um die wissenschaftlichen Quellen
                    zu durchsuchen.
                  </div>
                )}
              </div>
            </ScrollArea>

            {error && (
              <div className="rounded-md border border-red-500/60 bg-red-950/40 px-3 py-2 text-xs text-red-200">
                {error}
              </div>
            )}

            {/* 🔹 Peer-reviewed Toggle */}
            <div className="flex items-center justify-between gap-3 text-xs text-slate-300">
              <div className="flex items-center gap-2">
                <Switch
                  id="peer-reviewed"
                  checked={peerReviewedOnly}
                  onCheckedChange={setPeerReviewedOnly}
                />
                <Label
                  htmlFor="peer-reviewed"
                  className="cursor-pointer text-slate-200"
                >
                  Nur peer-reviewte Quellen
                </Label>
              </div>
              <span className="text-[10px] text-slate-500 text-right">
                Aus: auch Preprints, Reports & sonstige Quellen
              </span>
            </div>

            {/* Top-k Slider */}
            <div className="flex items-center justify-between gap-3 text-xs text-slate-300">
              <span className="whitespace-nowrap">
                Top-k (Anzahl der genutzten Quellen):
              </span>
              <div className="flex items-center gap-3 flex-1">
                <Slider
                  value={[topK]}
                  min={1}
                  max={10}
                  step={1}
                  onValueChange={(val) => setTopK(val[0])}
                  className="w-full"
                />
                <span className="w-6 text-right text-sm font-semibold text-slate-100">
                  {topK}
                </span>
              </div>
            </div>

            <form onSubmit={handleSend} className="flex gap-2 pt-1">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Frag z. B.: Welche Evidenz gibt es für Langzeitfolgen von COVID-19?"
                className="flex-1 bg-slate-900/60 border-slate-700 text-slate-100 placeholder:text-slate-500"
              />
              <Button
                type="submit"
                disabled={loading || !input.trim()}
                className="shrink-0"
              >
                {loading ? 'Senden …' : 'Senden'}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Dialog für Source-Details */}
        {selectedSource && (
          <Dialog
            open={true}
            onOpenChange={(open) => {
              if (!open) setSelectedSource(null)
            }}
          >
            <DialogContent className="bg-slate-900 text-slate-50 border border-slate-700 max-w-xl">
              <DialogHeader>
                <DialogTitle className="text-base">
                  {selectedSource.title}
                </DialogTitle>
                <DialogDescription className="text-xs text-slate-400">
                  Dokument #{selectedSource.document_id}, Chunk{' '}
                  {selectedSource.chunk_index}
                </DialogDescription>
              </DialogHeader>

              <div className="mt-4 text-sm whitespace-pre-wrap leading-relaxed">
                {selectedSource.chunk_text}
              </div>

              {selectedSource.meta && (
                <div className="mt-3 rounded-md border border-slate-700 p-3 text-xs space-y-1">
                  {'year' in selectedSource.meta && (
                    <p>Jahr: {(selectedSource.meta as any).year}</p>
                  )}
                  {'journal' in selectedSource.meta && (
                    <p>Journal: {(selectedSource.meta as any).journal}</p>
                  )}
                  {'doi' in selectedSource.meta && (
                    <p>DOI: {(selectedSource.meta as any).doi}</p>
                  )}
                  {'source' in selectedSource.meta && (
                    <p>Quelle: {(selectedSource.meta as any).source}</p>
                  )}
                </div>
              )}
            </DialogContent>
          </Dialog>
        )}
      </div>
    </div>
  )
}

function ChatBubble({
  message,
  onSourceClick,
}: {
  message: ChatMessage
  onSourceClick: (s: RagSource) => void
}) {
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
                    <button
                      type="button"
                      className="cursor-pointer text-sky-300 hover:text-sky-200 underline underline-offset-2 decoration-dotted hover:bg-slate-700/40 rounded-md px-1 py-[1px]"
                      onClick={() => onSourceClick(s)}
                      title={s.chunk_text.slice(0, 220)} // 🔹 kleine Hover-Preview
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
                    </button>
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
