"use client";

import { useState } from "react";

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const res = await fetch("http://localhost:8000/pipeline", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      const data = await res.json();
      setResult(data);
    } catch (e) {
      setError("Failed to connect to backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-950 text-white flex flex-col">
      {/* Header */}
      <header className="border-b border-gray-800 px-8 py-4 flex items-center gap-3">
        <div className="w-8 h-8 bg-orange-500 rounded-lg" />
        <span className="text-xl font-semibold tracking-tight">Basalt</span>
        <span className="text-gray-500 text-sm ml-2">Architecture Generator</span>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Left panel — input */}
        <div className="w-96 border-r border-gray-800 flex flex-col p-6 gap-4">
          <div>
            <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-2">
              Describe your system
            </h2>
            <textarea
              className="w-full bg-gray-900 border border-gray-700 rounded-lg p-4 text-sm text-white placeholder-gray-500 resize-none focus:outline-none focus:border-orange-500 transition-colors"
              rows={8}
              placeholder="e.g. Pharma plant OT network with FDA 21 CFR compliance on AWS, medium scale, high security..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />
          </div>

          <button
            onClick={handleGenerate}
            disabled={loading || !prompt.trim()}
            className="w-full bg-orange-500 hover:bg-orange-600 disabled:bg-gray-700 disabled:text-gray-500 text-white font-medium py-3 rounded-lg transition-colors"
          >
            {loading ? "Generating..." : "Generate Architecture"}
          </button>

          {error && (
            <p className="text-red-400 text-sm">{error}</p>
          )}

          {/* Parsed output */}
          {result?.parsed && (
            <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 text-xs">
              <p className="text-gray-400 font-medium mb-2 uppercase tracking-wider">Parsed</p>
              <div className="space-y-1">
                <div className="flex justify-between">
                  <span className="text-gray-500">Domain</span>
                  <span className="text-orange-400 font-medium">{result.parsed.app_type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Cloud</span>
                  <span className="text-white">{result.parsed.cloud}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Scale</span>
                  <span className="text-white">{result.parsed.scale}</span>
                </div>
                {result.parsed.compliance?.length > 0 && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Compliance</span>
                    <span className="text-green-400">{result.parsed.compliance.join(", ")}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right panel — architecture output */}
        <div className="flex-1 flex flex-col p-6 gap-4 overflow-auto">
          {!result && !loading && (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <div className="w-16 h-16 bg-gray-900 rounded-2xl mx-auto mb-4 flex items-center justify-center">
                  <div className="w-8 h-8 bg-orange-500 rounded-lg opacity-60" />
                </div>
                <p className="text-gray-500 text-sm">Describe your system and click Generate</p>
              </div>
            </div>
          )}

          {loading && (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                <p className="text-gray-400 text-sm">Analysing requirements...</p>
              </div>
            </div>
          )}

          {result?.classified && (
            <div className="space-y-4">
              {/* Architecture tiers */}
              <div>
                <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-3">
                  Architecture — {result.classified.app_type.toUpperCase()}
                </h2>
                <div className="space-y-2">
                  {Object.entries(result.classified.cheat_sheet.aws_services || {}).map(
                    ([tier, services]: [string, any]) => (
                      <div key={tier} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
                        <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">{tier}</p>
                        <div className="flex flex-wrap gap-2">
                          {services.map((service: string) => (
                            <span
                              key={service}
                              className="bg-gray-800 border border-gray-700 text-gray-200 text-xs px-3 py-1 rounded-full"
                            >
                              {service}
                            </span>
                          ))}
                        </div>
                      </div>
                    )
                  )}
                </div>
              </div>

              {/* Must haves */}
              <div className="bg-gray-900 border border-orange-900 rounded-lg p-4">
                <p className="text-xs text-orange-400 uppercase tracking-wider mb-2">Must have</p>
                <div className="flex flex-wrap gap-2">
                  {result.classified.cheat_sheet.must_have?.map((item: string) => (
                    <span key={item} className="bg-orange-950 border border-orange-800 text-orange-300 text-xs px-3 py-1 rounded-full">
                      {item}
                    </span>
                  ))}
                </div>
              </div>

              {/* Compliance */}
              <div className="bg-gray-900 border border-green-900 rounded-lg p-4">
                <p className="text-xs text-green-400 uppercase tracking-wider mb-2">Compliance</p>
                <div className="flex flex-wrap gap-2">
                  {result.classified.cheat_sheet.compliance_pool?.map((item: string) => (
                    <span key={item} className="bg-green-950 border border-green-800 text-green-300 text-xs px-3 py-1 rounded-full">
                      {item}
                    </span>
                  ))}
                </div>
              </div>

              {/* RAG context preview */}
              {result.context_preview && (
                <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
                  <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Document context retrieved</p>
                  <p className="text-xs text-gray-400 leading-relaxed">{result.context_preview}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
