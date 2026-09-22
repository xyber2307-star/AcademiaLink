import React, { useState, useEffect, useRef } from "react";
import {
  Bot,
  Send,
  Sparkles,
  AlertCircle,
  Briefcase,
  Layers,
  Award,
  BookOpen,
  Info,
  CheckCircle2,
} from "lucide-react";
import { aiAssistantService, AIChatResponse } from "../../services/aiAssistantService";
import { studentService } from "../../services/studentService";

interface ChatMessage {
  id: string;
  sender: "user" | "assistant";
  text: string;
  timestamp: string;
  groundedData?: AIChatResponse["grounded_data"];
  provider?: string;
  provenance?: AIChatResponse["provenance"];
}

export const StudentAIChatPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome_1",
      sender: "assistant",
      text: "Hello! I am your AI Career Advisor. I provide grounded recommendations based strictly on your verified skills, skill gaps, learning paths, and job matches. What would you like to explore today?",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [jobs, setJobs] = useState<any[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Load student's available matched jobs for context selector
    studentService
      .getOpportunities()
      .then((res) => setJobs(res || []))
      .catch((err) => console.warn("Could not fetch jobs for chat context:", err));
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (textToSend?: string) => {
    const query = textToSend || inputMessage;
    if (!query.trim() || loading) return;

    const userMsg: ChatMessage = {
      id: `usr_${Date.now()}`,
      sender: "user",
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputMessage("");
    setLoading(true);

    try {
      const res = await aiAssistantService.sendMessage(query, selectedJobId || undefined);
      const assistantMsg: ChatMessage = {
        id: `asst_${Date.now()}`,
        sender: "assistant",
        text: res.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        groundedData: res.grounded_data,
        provider: res.provider,
        provenance: res.provenance,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          sender: "assistant",
          text: `Error connecting to advisor: ${err.message || "Please try again later."}`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const quickPrompts = [
    "Which of my skills are strongest?",
    "What should I focus on next?",
    "Explain my learning path.",
    "What evidence have I submitted?",
    ...(selectedJobId ? ["What skills am I missing for this job?", "Why is my match score low?"] : []),
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-blue-500 to-blue-600 flex items-center justify-center text-white shadow-md">
            <Bot className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-gray-900">AI Career Assistant</h1>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-700 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                Grounded Mode
              </span>
            </div>
            <p className="text-sm text-gray-500">
              Personalized career guidance grounded in your real verified skills, portfolio, and job matches.
            </p>
          </div>
        </div>

        {/* Job Context Selector */}
        <div className="flex items-center gap-2">
          <Briefcase className="w-4 h-4 text-gray-400" />
          <select
            value={selectedJobId}
            onChange={(e) => setSelectedJobId(e.target.value)}
            className="text-xs font-medium border border-gray-200 rounded-lg px-3 py-2 bg-gray-50 text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">No target job selected (General Advice)</option>
            {jobs.map((j) => (
              <option key={j.id} value={j.id}>
                Target: {j.title} @ {j.company} ({Math.round(j.matchScore || 0)}% match)
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Chat Messages Card */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm flex flex-col h-[600px]">
        {/* Messages Scroll Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
            >
              {msg.sender === "assistant" && (
                <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center flex-shrink-0 mt-1">
                  <Bot className="w-4 h-4" />
                </div>
              )}
              <div
                className={`max-w-2xl rounded-2xl p-4 ${
                  msg.sender === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-50 text-gray-800 border border-gray-100"
                }`}
              >
                <div className="text-sm whitespace-pre-wrap leading-relaxed">{msg.text}</div>

                {/* Grounded context meta badge */}
                {msg.groundedData && (
                  <div className="mt-3 pt-3 border-t border-gray-200/60 flex flex-wrap gap-2 text-xs text-gray-500">
                    <span className="flex items-center gap-1 bg-white px-2 py-0.5 rounded border border-gray-200">
                      <Layers className="w-3 h-3 text-blue-500" />
                      {msg.groundedData.skills_count ?? 0} Skills Grounded
                    </span>
                    <span className="flex items-center gap-1 bg-white px-2 py-0.5 rounded border border-gray-200">
                      <BookOpen className="w-3 h-3 text-emerald-500" />
                      {msg.groundedData.learning_paths_count ?? 0} Learning Paths
                    </span>
                    <span className="flex items-center gap-1 bg-white px-2 py-0.5 rounded border border-gray-200">
                      <Award className="w-3 h-3 text-amber-500" />
                      {msg.groundedData.evidence_count ?? 0} Evidence Items
                    </span>
                    {msg.provenance && (
                      <span className="flex items-center gap-1 bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded border border-emerald-200">
                        <CheckCircle2 className="w-3 h-3" />
                        Source: {msg.provenance.source}
                      </span>
                    )}
                  </div>
                )}

                <div
                  className={`text-[10px] mt-1.5 ${
                    msg.sender === "user" ? "text-blue-200 text-right" : "text-gray-400"
                  }`}
                >
                  {msg.timestamp}
                </div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex gap-3 justify-start">
              <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center flex-shrink-0">
                <Bot className="w-4 h-4 animate-spin" />
              </div>
              <div className="bg-gray-50 rounded-2xl p-4 border border-gray-100 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-500 animate-bounce"></span>
                <span className="w-2 h-2 rounded-full bg-blue-500 animate-bounce delay-100"></span>
                <span className="w-2 h-2 rounded-full bg-blue-500 animate-bounce delay-200"></span>
                <span className="text-xs text-gray-500 ml-2">Consulting verified student records...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Suggested Queries */}
        <div className="px-6 py-2 border-t border-gray-100 bg-gray-50/50 flex flex-wrap gap-2">
          {quickPrompts.map((prompt, idx) => (
            <button
              key={idx}
              disabled={loading}
              onClick={() => handleSend(prompt)}
              className="text-xs px-3 py-1.5 rounded-full bg-white border border-gray-200 text-gray-700 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700 transition disabled:opacity-50"
            >
              <Sparkles className="w-3 h-3 inline mr-1 text-blue-500" />
              {prompt}
            </button>
          ))}
        </div>

        {/* Chat Input Bar */}
        <div className="p-4 border-t border-gray-100 flex gap-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder={
              selectedJobId
                ? "Ask about missing skills, match score, or priorities for selected job..."
                : "Ask about your strongest skills, learning paths, or career recommendations..."
            }
            disabled={loading}
            className="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          />
          <button
            onClick={() => handleSend()}
            disabled={!inputMessage.trim() || loading}
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium text-sm transition flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
          >
            <Send className="w-4 h-4" />
            Send
          </button>
        </div>
      </div>
    </div>
  );
};
