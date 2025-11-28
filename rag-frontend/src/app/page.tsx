'use client'

import { useState, useEffect } from 'react'
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
  conversation_id: number
  precision_at_k?: number | null
  judge_score?: number | null
  judge_label?: string | null
  judge_explanation?: string | null
}

type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: RagSource[]
  precision_at_k?: number | null
  judge_score?: number | null
  judge_label?: string | null
  judge_explanation?: string | null
}

type ChatSessionItem = {
  id: number
  title?: string | null
  updated_at?: string
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000'

export default function HomePage() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedSource, setSelectedSource] = useState<RagSource | null>(null)
  const [topK, setTopK] = useState<number>(3)
  const [conversationId, setConversationId] = useState<number | null>(null)
  const [sessions, setSessions] = useState<ChatSessionItem[]>([])
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null)
  const [evalRelevantDocs, setEvalRelevantDocs] = useState<string>('')
  const [evalReferenceAnswer, setEvalReferenceAnswer] = useState<string>('')
  const [runJudge, setRunJudge] = useState<boolean>(false)

  // 🔹 Peer-reviewed only
  const [peerReviewedOnly, setPeerReviewedOnly] = useState<boolean>(false)

  // Sessions laden
  async function refreshSessions() {
    try {
      const res = await fetch(`${API_BASE}/chat_sessions/`)
      if (!res.ok) return
      const data = await res.json()
      setSessions(data)
    } catch (e) {
      console.error('Fehler beim Laden der Sessions', e)
    }
  }

  useEffect(() => {
    refreshSessions()
  }, [])

  async function loadSession(id: number) {
    setActiveSessionId(id)
    setError(null)
    setLoading(true)

    try {
      const res = await fetch(`${API_BASE}/chat_sessions/${id}`)
      if (!res.ok) {
        const txt = await res.text()
        throw new Error(`HTTP ${res.status}: ${txt}`)
      }
      const data = await res.json()

      const mapped: ChatMessage[] = (data.messages ?? []).map((m: any) => ({
        id: m.id.toString(),
        role: m.role as 'user' | 'assistant',
        content: m.content,
        sources: m.sources || [],
      }))

      setMessages(mapped)
      setConversationId(id)
    } catch (err: any) {
      console.error(err)
      setError(err.message ?? 'Fehler beim Laden der Session')
    } finally {
      setLoading(false)
    }
  }

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

    // 🔹 relevante Dokument-IDs (Precision@k)
    let relevant_document_ids: number[] | undefined = undefined
    if (evalRelevantDocs.trim()) {
      const parsed = evalRelevantDocs
        .split(',')
        .map((s) => parseInt(s.trim(), 10))
        .filter((n) => !Number.isNaN(n))
      if (parsed.length > 0) {
        relevant_document_ids = parsed
      }
    }

    console.log('DEBUG relevant_document_ids vor fetch:', relevant_document_ids)

    setLoading(true)
    try {
      const body = {
        question,
        top_k: topK,
        peer_reviewed_only: peerReviewedOnly,
        conversation_id: conversationId,
        relevant_document_ids,
        run_judge: runJudge,
        reference_answer: evalReferenceAnswer || null,
      }
      console.log('DEBUG Request-Body:', body)

      const res = await fetch(`${API_BASE}/rag_answer/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (!res.ok) {
        const txt = await res.text()
        throw new Error(`HTTP ${res.status}: ${txt}`)
      }

      const data: RagAnswerResponse = await res.json()
      console.log('DEBUG Response von /rag_answer:', data)

      setConversationId(data.conversation_id)

      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: data.answer,
        sources: data.sources,
        precision_at_k: data.precision_at_k ?? null,
        judge_score: data.judge_score ?? null,
        judge_label: data.judge_label ?? null,
        judge_explanation: data.judge_explanation ?? null,
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (err: any) {
      console.error(err)
      setError(err.message ?? 'Fehler beim Abrufen der Antwort')
    } finally {
      setLoading(false)
    }
  }

  function handleNewChat() {
    setMessages([])
    setConversationId(null)
    setActiveSessionId(null)
    setError(null)
  }

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-50">
      {/* 🔹 Sidebar links */}
      <aside className="hidden md:flex w-64 flex-col border-r border-slate-800 p-4 gap-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-100">Chats</h2>
          <Button
            variant="outline"
            size="sm"
            className="h-7 px-2 text-xs"
            onClick={handleNewChat}
          >
            Neuer Chat
          </Button>
        </div>

        <ScrollArea className="flex-1 rounded-md border border-slate-800 bg-slate-900/60 px-1 py-2">
          <div className="flex flex-col gap-1">
            {sessions.length === 0 && (
              <p className="text-[11px] text-slate-500 px-2">
                Noch keine gespeicherten Chats.
              </p>
            )}

            {sessions.map((s) => (
              <button
                key={s.id}
                type="button"
                className={`w-full rounded-md px-3 py-2 text-left text-xs transition
                  ${
                    activeSessionId === s.id
                      ? 'bg-slate-800 border border-slate-700'
                      : 'hover:bg-slate-800/70'
                  }`}
                onClick={() => loadSession(s.id)}
              >
                <div className="font-medium truncate">
                  {s.title || 'Unbenannter Chat'}
                </div>
                {s.updated_at && (
                  <div className="text-[10px] text-slate-400">
                    {new Date(s.updated_at).toLocaleString()}
                  </div>
                )}
              </button>
            ))}
          </div>
        </ScrollArea>
      </aside>

      {/* 🔹 Hauptbereich rechts */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 py-6">
        <div className="w-full max-w-4xl space-y-4">
          <header className="flex items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight text-slate-50">
                RAG Science Chat
              </h1>
              <p className="text-sm text-slate-400">
                Stelle dein RAG-System Fragen zu wissenschaftlichen
                Sachverhalten.
              </p>
            </div>

            {/* Modus-Badge (Peer-reviewed / Alle Quellen) */}
            <div className="flex items-center gap-2 ml-auto">
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
                    <div className="text-xs text-slate-400">
                      KI denkt nach …
                    </div>
                  )}

                  {messages.length === 0 && !loading && (
                    <div className="text-xs text-slate-500">
                      Stelle deine erste Frage, um die wissenschaftlichen
                      Quellen zu durchsuchen.
                    </div>
                  )}
                </div>
              </ScrollArea>

              {error && (
                <div className="rounded-md border border-red-500/60 bg-red-950/40 px-3 py-2 text-xs text-red-200">
                  {error}
                </div>
              )}

              {/* Peer-reviewed Toggle */}
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

              {/* 🔹 Precision@k: Relevante Dokument-IDs */}
              <div className="flex flex-col gap-1 text-xs text-slate-300">
                <label className="text-[11px] text-slate-400">
                  Relevante Dokument-IDs (für Precision@k, optional)
                </label>
                <Input
                  value={evalRelevantDocs}
                  onChange={(e) => setEvalRelevantDocs(e.target.value)}
                  placeholder="z. B. 1, 5, 12"
                  className="bg-slate-900/60 border-slate-700 text-slate-100 placeholder:text-slate-500 h-8 text-xs"
                />
                <span className="text-[10px] text-slate-500">
                  Wenn gesetzt, berechnet das Backend Precision@k basierend auf
                  den Top-k-Retrievals.
                </span>
              </div>

              {/* LLM-Judge Toggle + Referenz-Antwort */}
              <div className="flex flex-col gap-1 text-xs text-slate-300 border-t border-slate-800 pt-2 mt-1">
                <div className="flex items-center gap-2">
                  <Switch
                    id="run-judge"
                    checked={runJudge}
                    onCheckedChange={setRunJudge}
                  />
                  <Label
                    htmlFor="run-judge"
                    className="cursor-pointer text-slate-200"
                  >
                    LLM-Judge ausführen (Antwort bewerten)
                  </Label>
                </div>
                <textarea
                  value={evalReferenceAnswer}
                  onChange={(e) => setEvalReferenceAnswer(e.target.value)}
                  placeholder="Optionale Referenz-Antwort (Gold-Standard) für die Bewertung..."
                  className="mt-1 h-16 w-full rounded-md bg-slate-900/60 border border-slate-700 px-2 py-1 text-[11px] text-slate-100 placeholder:text-slate-500"
                />
                <span className="text-[10px] text-slate-500">
                  Wenn gesetzt, vergleicht der LLM-Judge die System-Antwort mit
                  dieser Referenz.
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
                      <p>Jahr {(selectedSource.meta as any).year}</p>
                    )}
                    {'journal' in selectedSource.meta && (
                      <p>Journal {(selectedSource.meta as any).journal}</p>
                    )}
                    {'doi' in selectedSource.meta && (
                      <p>DOI {(selectedSource.meta as any).doi}</p>
                    )}
                    {'source' in selectedSource.meta && (
                      <p>Quelle {(selectedSource.meta as any).source}</p>
                    )}
                  </div>
                )}
              </DialogContent>
            </Dialog>
          )}
        </div>
      </main>
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
        {/* User/Assistant Text */}
        <div className="whitespace-pre-wrap leading-relaxed">
          {message.content}
        </div>

        {/* Precision@k Badge (nur bei Assistant) */}
        {!isUser && message.precision_at_k != null && (
          <div className="pt-1">
            <span className="inline-flex items-center rounded-full bg-slate-700/70 px-2 py-[2px] text-[11px] text-slate-100">
              Precision@k:{' '}
              <span className="font-semibold">
                {message.precision_at_k.toFixed(2)}
              </span>
            </span>
          </div>
        )}

        {/* LLM-Judge Result */}
        {!isUser && (message.judge_score != null || message.judge_label) && (
          <div className="mt-1 rounded-md bg-slate-900/70 border border-slate-700 px-3 py-2 text-[11px] space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-100">LLM-Judge</span>
              {message.judge_score != null && (
                <span className="rounded-full bg-slate-700/80 px-2 py-[1px]">
                  Score:{' '}
                  <span className="font-semibold">
                    {message.judge_score.toFixed(2)}
                  </span>
                </span>
              )}
            </div>
            {message.judge_label && (
              <p className="text-slate-200">
                Urteil:{' '}
                <span className="font-medium">{message.judge_label}</span>
              </p>
            )}
            {message.judge_explanation && (
              <p className="text-slate-300 whitespace-pre-wrap">
                {message.judge_explanation}
              </p>
            )}
          </div>
        )}

        {/* Quellenliste */}
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
                  (s.meta as any)?.peerReviewed === true

                return (
                  <li
                    key={`${s.document_id}-${s.chunk_index}`}
                    className="text-[11px] text-slate-300"
                  >
                    <button
                      type="button"
                      className="cursor-pointer text-sky-300 hover:text-sky-200 underline underline-offset-2 decoration-dotted hover:bg-slate-700/40 rounded-md px-1 py-[1px]"
                      onClick={() => onSourceClick(s)}
                      title={s.chunk_text.slice(0, 220)}
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
