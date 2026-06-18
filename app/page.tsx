"use client";

import { useState } from "react";
import dynamic from "next/dynamic";

const DiagramCanvas = dynamic(() => import("./components/diagram/DiagramCanvas"), { ssr: false });

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
      const res = await fetch("http://localhost:8000/generate", {
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

      <div className="flex flex-1 overflow-hidden" style={{ height: "calc(100vh - 57px)" }}>
        {/* Left panel */}
        <div className="w-80 border-r border-gray-800 flex flex-col p-5 gap-4 overflow-y-auto">
          <div>
            <h2 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">
              Describe your system
            </h2>
            <textarea
              className="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-sm text-white placeholder-gray-500 resize-none focus:outline-none focus:border-orange-500 transition-colors"
              rows={7}
              placeholder="e.g. Pharma OT network with FDA 21 CFR on AWS, hybrid with on-prem SCADA..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && e.metaKey) handleGenerate(); }}
            />
            <p className="text-xs text-gray-600 mt-1">⌘ + Enter to generate</p>
          </div>

          <button
            onClick={handleGenerate}
            disabled={loading || !prompt.trim()}
            className="w-full bg-orange-500 hover:bg-orange-600 disabled:bg-gray-800 disabled:text-gray-600 text-white font-medium py-2.5 rounded-lg transition-colors text-sm"
          >
            {loading ? "Generating..." : "Generate Architecture"}
          </button>

          {error && <p className="text-red-400 text-xs">{error}</p>}

          {result?.parsed && (
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-3 text-xs space-y-2">
              <p className="text-gray-500 uppercase tracking-wider font-medium">Detected</p>
              <div className="space-y-1.5">
                <div className="flex justify-between">
                  <span className="text-gray-500">Domain</span>
                  <span className="text-orange-400 font-semibold uppercase">{result.parsed.app_type}</span>
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
                  <div className="flex justify-between gap-2">
                    <span className="text-gray-500 shrink-0">Compliance</span>
                    <span className="text-green-400 text-right">{result.parsed.compliance.join(", ")}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {result?.classified?.cheat_sheet?.must_have && (
            <div className="bg-gray-900 border border-orange-900 rounded-lg p-3 text-xs">
              <p className="text-orange-400 uppercase tracking-wider font-medium mb-2">Must have</p>
              <div className="space-y-1">
                {result.classified.cheat_sheet.must_have.map((item: string) => (
                  <div key={item} className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-orange-500" />
                    <span className="text-gray-300">{item}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result?.classified?.cheat_sheet?.compliance_pool && (
            <div className="bg-gray-900 border border-green-900 rounded-lg p-3 text-xs">
              <p className="text-green-400 uppercase tracking-wider font-medium mb-2">Compliance pool</p>
              <div className="flex flex-wrap gap-1.5">
                {result.classified.cheat_sheet.compliance_pool.map((item: string) => (
                  <span key={item} className="bg-green-950 text-green-300 px-2 py-0.5 rounded text-xs">
                    {item}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right panel — diagram canvas */}
        <div className="flex-1 relative">
          {!result && !loading && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="w-16 h-16 bg-gray-900 rounded-2xl mx-auto mb-4 flex items-center justify-center border border-gray-800">
                  <div className="w-8 h-8 bg-orange-500 rounded-lg opacity-40" />
                </div>
                <p className="text-gray-600 text-sm">Describe your system and generate</p>
              </div>
            </div>
          )}

          {loading && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                <p className="text-gray-500 text-sm">Building architecture...</p>
              </div>
            </div>
          )}

          {result?.diagram && (
            <DiagramCanvas diagram={result.diagram} title={result.diagram.title} />
          )}
        </div>
      </div>
    </main>
  );
}
