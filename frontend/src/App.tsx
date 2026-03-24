import { useState, useEffect, useRef } from 'react';
import { 
  Send, Plus, User, Bot, Settings, ChevronLeft, ChevronRight, 
  MessageSquare, Users, X, Edit2, Trash2, Save 
} from 'lucide-react';
import Markdown from 'react-markdown';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface Message {
  id: string;
  sender_type: 'user' | 'agent';
  content: string;
  persona_name?: string;
  persona_id?: number;
  created_at?: string;
}

interface Session {
  id: number;
  title: string;
}

interface Persona {
  id: number;
  name: string;
  instruction: string;
  is_favorite: boolean;
}

export default function App() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [participantIds, setParticipantIds] = useState<number[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeSpeakerId, setActiveSpeakerId] = useState<number | null>(null);
  const [isPersonaModalOpen, setIsPersonaModalOpen] = useState(false);
  
  // Persona form state
  const [editingPersona, setEditingPersona] = useState<Partial<Persona> | null>(null);

  const chatEndRef = useRef<HTMLDivElement>(null);
  const ws = useRef<WebSocket | null>(null);

  const fetchPersonas = () => {
    fetch('/api/personas').then(res => res.json()).then(data => {
      setPersonas(data);
      if (participantIds.length === 0 && data.length > 0) {
        setParticipantIds([data[0].id]);
      }
    });
  };

  useEffect(() => {
    fetch('/api/sessions').then(res => res.json()).then(setSessions);
    fetchPersonas();

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/chat`;
    
    ws.current = new WebSocket(wsUrl);
    
    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'chunk') {
        setMessages(prev => {
          const lastMsg = prev[prev.length - 1];
          if (lastMsg && lastMsg.sender_type === 'agent' && lastMsg.persona_name === data.persona_name) {
            return [
              ...prev.slice(0, -1),
              { ...lastMsg, content: lastMsg.content + data.content }
            ];
          } else {
            return [
              ...prev,
              { 
                id: Date.now().toString(), 
                sender_type: 'agent', 
                content: data.content, 
                persona_name: data.persona_name,
                created_at: new Date().toISOString()
              }
            ];
          }
        });
      } else if (data.type === 'done') {
        setIsStreaming(false);
      }
    };

    return () => {
      ws.current?.close();
    };
  }, []);

  useEffect(() => {
    if (activeSessionId) {
      fetch(`/api/sessions/${activeSessionId}`).then(res => res.json()).then(data => {
        const msgs = (data.messages || []).map((m: any) => ({
          ...m,
          persona_name: m.persona?.name
        }));
        setMessages(msgs);
      });
    } else {
      setMessages([]);
    }
  }, [activeSessionId]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const toggleParticipant = (id: number) => {
    setParticipantIds(prev => 
      prev.includes(id) ? (prev.length > 1 ? prev.filter(pid => pid !== id) : prev) : [...prev, id]
    );
  };

  const handleSendMessage = async (targetPersonaId?: number) => {
    const personaId = targetPersonaId || participantIds[0];
    if (!personaId || isStreaming || !ws.current) return;

    let sessionId = activeSessionId;
    if (!sessionId) {
      const res = await fetch('/api/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: inputValue.slice(0, 30) || "New Debate" })
      });
      const newSession = await res.json();
      setSessions([newSession, ...sessions]);
      setActiveSessionId(newSession.id);
      sessionId = newSession.id;
    }

    if (inputValue.trim()) {
      const userMessage: Message = {
        id: Date.now().toString(),
        sender_type: 'user',
        content: inputValue,
        created_at: new Date().toISOString()
      };
      setMessages(prev => [...prev, userMessage]);
    }
    
    ws.current.send(JSON.stringify({
      session_id: sessionId,
      persona_id: personaId,
      content: inputValue
    }));

    setInputValue('');
    setIsStreaming(true);
    setActiveSpeakerId(personaId);
  };

  const formatTime = (dateStr?: string) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Persona CRUD handlers
  const handleSavePersona = async () => {
    if (!editingPersona?.name || !editingPersona?.instruction) return;

    const method = editingPersona.id ? 'PUT' : 'POST';
    const url = editingPersona.id ? `/api/personas/${editingPersona.id}` : '/api/personas';

    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(editingPersona)
    });

    if (res.ok) {
      fetchPersonas();
      setEditingPersona(null);
    }
  };

  const handleDeletePersona = async (id: number) => {
    if (!confirm('Are you sure you want to delete this persona?')) return;
    const res = await fetch(`/api/personas/${id}`, { method: 'DELETE' });
    if (res.ok) {
      fetchPersonas();
      setParticipantIds(prev => prev.filter(pid => pid !== id));
    }
  };

  const isDebateMode = participantIds.length > 1;

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      {/* Sidebar */}
      <div className={cn(
        "bg-muted border-r transition-all duration-300 flex flex-col",
        isSidebarOpen ? "w-64" : "w-0 overflow-hidden"
      )}>
        <div className="p-4 border-b flex items-center justify-between shrink-0">
          <h1 className="font-bold text-lg">BotChat2</h1>
          <button onClick={() => setActiveSessionId(null)} className="p-1 hover:bg-background rounded">
            <Plus size={20} />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {sessions.map(s => (
            <button
              key={s.id}
              onClick={() => setActiveSessionId(s.id)}
              className={cn(
                "w-full text-left px-3 py-2 rounded text-sm truncate",
                activeSessionId === s.id ? "bg-primary text-primary-foreground" : "hover:bg-background/50"
              )}
            >
              {s.title}
            </button>
          ))}
        </div>
        <div className="p-4 border-t shrink-0">
          <button 
            onClick={() => setIsPersonaModalOpen(true)}
            className="flex items-center gap-2 text-sm hover:text-primary transition-colors w-full"
          >
            <Settings size={18} />
            <span>Manage Personas</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col relative min-w-0 bg-background">
        <button 
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          className="absolute left-0 top-1/2 -translate-y-1/2 bg-muted border border-l-0 p-1 rounded-r z-10 hover:bg-accent"
        >
          {isSidebarOpen ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
        </button>

        {/* Header: Moderator Controls */}
        <header className="h-16 border-b flex items-center justify-between px-6 bg-background/80 backdrop-blur shrink-0">
          <div className="flex items-center gap-4 overflow-x-auto no-scrollbar">
            <div className="flex items-center gap-2 px-3 py-1 bg-muted rounded-lg shrink-0">
              {isDebateMode ? <Users size={16} className="text-primary" /> : <MessageSquare size={16} />}
              <span className="text-xs font-bold uppercase tracking-wider">
                {isDebateMode ? "Debate Mode" : "1:1 Mode"}
              </span>
            </div>
            <div className="h-6 w-px bg-border shrink-0" />
            <div className="flex gap-2">
              {personas.map(p => (
                <button
                  key={p.id}
                  onClick={() => toggleParticipant(p.id)}
                  className={cn(
                    "px-3 py-1 rounded-full text-xs font-medium border transition-all whitespace-nowrap",
                    participantIds.includes(p.id) 
                      ? "bg-primary/10 border-primary text-primary shadow-sm" 
                      : "border-border hover:border-primary/50 opacity-60"
                  )}
                >
                  {p.name}
                </button>
              ))}
            </div>
          </div>
        </header>

        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {(messages.length === 0 && !isStreaming) && (
            <div className="h-full flex flex-col items-center justify-center text-muted-foreground space-y-4">
              <Bot size={48} className="opacity-10" />
              <div className="text-center">
                <p className="font-medium">Welcome, Moderator.</p>
                <p className="text-sm opacity-60">Select participants and start the conversation.</p>
              </div>
            </div>
          )}
          {messages.map((m, idx) => (
            <div key={m.id || idx} className={cn(
              "flex gap-4 max-w-4xl mx-auto group",
              m.sender_type === 'user' ? "flex-row-reverse" : ""
            )}>
              <div className={cn(
                "w-10 h-10 rounded-xl flex items-center justify-center shrink-0 shadow-sm border transition-transform group-hover:scale-105",
                m.sender_type === 'user' ? "bg-primary border-primary text-primary-foreground" : "bg-muted"
              )}>
                {m.sender_type === 'user' ? <User size={20} /> : <Bot size={20} />}
              </div>
              <div className={cn(
                "flex-1 space-y-1.5 min-w-0",
                m.sender_type === 'user' ? "flex flex-col items-end" : ""
              )}>
                <div className={cn(
                  "flex items-center gap-2 px-1",
                  m.sender_type === 'user' ? "justify-end" : ""
                )}>
                  {m.persona_name && (
                    <span className="text-[10px] uppercase font-black text-primary tracking-widest">
                      {m.persona_name}
                    </span>
                  )}
                  <span className="text-[10px] text-muted-foreground font-medium">
                    {formatTime(m.created_at)}
                  </span>
                </div>
                <div className={cn(
                  "rounded-2xl px-5 py-3 text-[15px] shadow-sm inline-block max-w-full text-left",
                  m.sender_type === 'user' 
                    ? "bg-primary text-primary-foreground rounded-tr-none" 
                    : "bg-muted border rounded-tl-none prose prose-neutral max-w-none break-words text-foreground"
                )}>
                  <Markdown>
                    {m.content}
                  </Markdown>
                </div>
              </div>
            </div>
          ))}
          {isStreaming && (
            <div className="flex gap-4 max-w-4xl mx-auto">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 shadow-sm border bg-muted">
                <Bot size={20} />
              </div>
              <div className="space-y-1.5 flex-1">
                <div className="flex items-center gap-2 px-1">
                  <span className="text-[10px] uppercase font-black text-primary tracking-widest">
                    {personas.find(p => p.id === activeSpeakerId)?.name || "Agent"}
                  </span>
                  <span className="text-[10px] text-muted-foreground font-medium italic">
                    typing...
                  </span>
                </div>
                <div className="bg-muted/50 border rounded-2xl rounded-tl-none px-5 py-3 inline-flex items-center gap-2">
                  <span className="text-sm italic text-muted-foreground">Thinking</span>
                  <div className="dot-animation">
                    <span></span><span></span><span></span>
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input Area: Call to Speak */}
        <div className="p-6 border-t bg-background shrink-0 shadow-2xl">
          <div className="max-w-4xl mx-auto space-y-4">
            {isDebateMode && (
              <div className="flex items-center gap-2 overflow-x-auto pb-2 no-scrollbar">
                <span className="text-[10px] font-bold uppercase text-muted-foreground whitespace-nowrap">Call to Speak:</span>
                {participantIds.map(pid => {
                  const p = personas.find(pers => pers.id === pid);
                  return (
                    <button
                      key={pid}
                      onClick={() => handleSendMessage(pid)}
                      disabled={isStreaming}
                      className="px-3 py-1.5 bg-muted hover:bg-primary hover:text-primary-foreground rounded-lg text-xs font-bold transition-colors disabled:opacity-50 border border-border flex items-center gap-2 whitespace-nowrap"
                    >
                      <Bot size={14} />
                      {p?.name}
                    </button>
                  );
                })}
              </div>
            )}
            
            <div className="relative group">
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                placeholder={isDebateMode ? "Set a topic or guide the debate..." : "Type your message..."}
                className="w-full bg-muted/50 border-2 border-transparent focus:border-primary/20 rounded-2xl pl-5 pr-14 py-4 focus:outline-none transition-all resize-none min-h-[64px] max-h-48 shadow-inner"
                rows={1}
              />
              <button
                onClick={() => handleSendMessage()}
                disabled={(!inputValue.trim() && !isDebateMode) || isStreaming}
                className="absolute right-3 bottom-3 p-2 bg-primary text-primary-foreground rounded-xl disabled:opacity-50 hover:scale-105 active:scale-95 transition-all shadow-lg"
              >
                <Send size={20} />
              </button>
            </div>
            {!isDebateMode && (
              <p className="text-[10px] text-center text-muted-foreground opacity-60">
                1:1 Chat with <strong>{personas.find(p => p.id === participantIds[0])?.name}</strong>
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Persona Management Modal */}
      {isPersonaModalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-background border rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl">
            <div className="p-4 border-b flex items-center justify-between">
              <h2 className="font-bold text-xl">Manage Personas</h2>
              <button onClick={() => { setIsPersonaModalOpen(false); setEditingPersona(null); }} className="p-1 hover:bg-muted rounded">
                <X size={20} />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
              {/* Form Section */}
              <div className="bg-muted/30 p-4 rounded-xl border border-dashed border-border space-y-4">
                <h3 className="text-sm font-bold uppercase text-muted-foreground tracking-widest">
                  {editingPersona?.id ? 'Edit Persona' : 'Create New Persona'}
                </h3>
                <div className="space-y-2">
                  <label className="text-xs font-medium">Name</label>
                  <input 
                    type="text" 
                    value={editingPersona?.name || ''} 
                    onChange={e => setEditingPersona({...editingPersona, name: e.target.value})}
                    placeholder="e.g. Logic Expert"
                    className="w-full bg-background border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-medium">System Instruction</label>
                  <textarea 
                    value={editingPersona?.instruction || ''} 
                    onChange={e => setEditingPersona({...editingPersona, instruction: e.target.value})}
                    placeholder="Describe how this agent should behave..."
                    className="w-full bg-background border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 min-h-[100px]"
                  />
                </div>
                <div className="flex justify-end gap-2">
                  {editingPersona && (
                    <button 
                      onClick={() => setEditingPersona(null)}
                      className="px-4 py-2 text-sm hover:bg-background rounded-lg transition-colors"
                    >
                      Cancel
                    </button>
                  )}
                  <button 
                    onClick={handleSavePersona}
                    className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-bold shadow-lg hover:scale-105 active:scale-95 transition-all flex items-center gap-2"
                  >
                    <Save size={16} />
                    Save Persona
                  </button>
                </div>
              </div>

              {/* List Section */}
              <div className="space-y-3">
                <h3 className="text-sm font-bold uppercase text-muted-foreground tracking-widest">Available Personas</h3>
                <div className="grid gap-3">
                  {personas.map(p => (
                    <div key={p.id} className="p-4 border rounded-xl flex items-center justify-between group hover:border-primary/50 transition-colors bg-muted/10">
                      <div className="min-w-0 pr-4">
                        <h4 className="font-bold text-sm">{p.name}</h4>
                        <p className="text-xs text-muted-foreground truncate">{p.instruction}</p>
                      </div>
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button 
                          onClick={() => setEditingPersona(p)}
                          className="p-2 hover:bg-background rounded-lg text-muted-foreground hover:text-primary transition-colors"
                        >
                          <Edit2 size={16} />
                        </button>
                        <button 
                          onClick={() => handleDeletePersona(p.id)}
                          className="p-2 hover:bg-background rounded-lg text-muted-foreground hover:text-destructive transition-colors"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
