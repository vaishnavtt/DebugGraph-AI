import React, { useState } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  Database,
  FileSearch,
  FileText,
  Filter,
  RefreshCw,
  Search,
  Sparkles,
  UploadCloud,
} from 'lucide-react';
import { api } from '../services/api';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

export const LogExplorerPage: React.FC = () => {
  // Upload State
  const [file, setFile] = useState<File | null>(null);
  const [serviceName, setServiceName] = useState('payment-service');
  const [environment, setEnvironment] = useState('production');
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState<any | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  // Search State
  const [searchQuery, setSearchQuery] = useState('ConnectionTimeoutError in stripe_client');
  const [searchService, setSearchService] = useState('payment-service');
  const [topK, setTopK] = useState(5);
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<any | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    try {
      const res = await api.uploadLogs(file, serviceName, environment);
      setUploadSuccess(res);
      setFile(null);
    } catch (err: any) {
      setUploadError(err.message || 'Log upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setSearching(true);
    setSearchError(null);

    try {
      const res = await api.searchHybrid(
        searchQuery.trim(),
        searchService.trim() || undefined,
        topK
      );
      setSearchResults(res);
    } catch (err: any) {
      setSearchError(err.message || 'Hybrid search failed');
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* SECTION 1: LOG INGESTION INTERFACE */}
      <Card
        title="Intelligent Log Ingestion"
        subtitle="Upload raw logs, exception stack traces, JSON, or JSONL files for automatic parsing and BGE vector indexing"
      >
        <form onSubmit={handleUpload} className="space-y-4">
          {/* Drag & Drop Area */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleFileDrop}
            className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all cursor-pointer ${
              isDragging
                ? 'border-cyan-400 bg-cyan-950/20'
                : 'border-slate-700 bg-slate-950/60 hover:border-slate-600'
            }`}
          >
            <input
              type="file"
              id="logFileInput"
              accept=".log,.txt,.json,.jsonl"
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) {
                  setFile(e.target.files[0]);
                }
              }}
              className="hidden"
            />
            <label htmlFor="logFileInput" className="cursor-pointer">
              <UploadCloud
                className={`w-10 h-10 mx-auto mb-3 transition-colors ${
                  file ? 'text-cyan-400' : 'text-slate-400'
                }`}
              />
              {file ? (
                <div>
                  <p className="text-sm font-bold text-white font-mono">{file.name}</p>
                  <p className="text-xs text-slate-400 font-mono mt-0.5">
                    {(file.size / 1024).toFixed(1)} KB • Click or drop to replace
                  </p>
                </div>
              ) : (
                <div>
                  <p className="text-sm font-semibold text-slate-200">
                    Drag and drop your log file here, or{' '}
                    <span className="text-cyan-400 underline underline-offset-2">browse files</span>
                  </p>
                  <p className="text-xs text-slate-400 font-mono mt-1">
                    Supports .log, .txt, .json, and .jsonl files (up to 10 MB)
                  </p>
                </div>
              )}
            </label>
          </div>

          {/* Service and Environment inputs */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 font-mono mb-1.5">
                Microservice Identifier *
              </label>
              <input
                type="text"
                value={serviceName}
                onChange={(e) => setServiceName(e.target.value)}
                placeholder="e.g. payment-service"
                required
                className="w-full bg-slate-950 border border-slate-700/80 rounded-lg px-3 py-2 text-xs text-slate-100 placeholder-slate-500 font-mono focus:outline-none focus:border-cyan-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 font-mono mb-1.5">
                Environment
              </label>
              <select
                value={environment}
                onChange={(e) => setEnvironment(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700/80 rounded-lg px-3 py-2 text-xs text-slate-100 font-mono focus:outline-none focus:border-cyan-500"
              >
                <option value="production">production</option>
                <option value="staging">staging</option>
                <option value="development">development</option>
              </select>
            </div>
          </div>

          {/* Submit */}
          <div className="flex items-center justify-between pt-2">
            <span className="text-[11px] text-slate-400 font-mono">
              Parses multiline stack traces & extracts UTC timestamps automatically
            </span>
            <button
              type="submit"
              disabled={uploading || !file}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white font-bold text-xs shadow-md transition-all flex items-center gap-2 font-mono disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {uploading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Ingesting & Indexing...</span>
                </>
              ) : (
                <>
                  <UploadCloud className="w-4 h-4" />
                  <span>Upload & Index Log</span>
                </>
              )}
            </button>
          </div>
        </form>

        {/* Upload Success Banner */}
        {uploadSuccess && (
          <div className="mt-4 p-4 bg-emerald-950/40 border border-emerald-800 rounded-xl space-y-2">
            <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs font-mono">
              <CheckCircle2 className="w-4 h-4" />
              <span>Log File Ingested Successfully!</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono text-slate-300">
              <div>
                File: <span className="text-white font-bold">{uploadSuccess.filename}</span>
              </div>
              <div>
                Service: <span className="text-cyan-400">{uploadSuccess.service_name}</span>
              </div>
              <div>
                Parsed Lines: <span className="text-emerald-400">{uploadSuccess.parsed_lines_count}</span>
              </div>
              <div>
                Indexed Chunks: <span className="text-purple-400">{uploadSuccess.indexed_chunks_count}</span>
              </div>
            </div>
          </div>
        )}

        {/* Upload Error Banner */}
        {uploadError && (
          <div className="mt-4 p-4 bg-rose-950/40 border border-rose-800 rounded-xl flex items-center gap-2 text-xs text-rose-300 font-mono">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{uploadError}</span>
          </div>
        )}
      </Card>

      {/* SECTION 2: LIVE HYBRID RETRIEVAL TESTER */}
      <Card
        title="Hybrid Search & Reranking Explorer"
        subtitle="Test Qdrant Dense + BM25 keyword matching with Reciprocal Rank Fusion & Cross-Encoder"
      >
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Enter search query or error code..."
                className="w-full bg-slate-950 border border-slate-700/80 rounded-lg px-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 font-mono focus:outline-none focus:border-cyan-500"
              />
            </div>
            <div className="w-full sm:w-48">
              <input
                type="text"
                value={searchService}
                onChange={(e) => setSearchService(e.target.value)}
                placeholder="Service filter..."
                className="w-full bg-slate-950 border border-slate-700/80 rounded-lg px-3 py-2.5 text-xs text-slate-100 placeholder-slate-500 font-mono focus:outline-none focus:border-cyan-500"
              />
            </div>
            <button
              type="submit"
              disabled={searching || !searchQuery.trim()}
              className="px-5 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-300 font-bold text-xs border border-slate-700 transition-colors flex items-center justify-center gap-1.5 font-mono shrink-0 disabled:opacity-50"
            >
              {searching ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Search className="w-4 h-4" />
              )}
              <span>Search Logs</span>
            </button>
          </div>
        </form>

        {/* Search Results Display */}
        {searchResults && (
          <div className="mt-6 space-y-4">
            <div className="flex items-center justify-between text-xs font-mono text-slate-400 pb-2 border-b border-slate-800">
              <span>
                Found {searchResults.total_hits} chunks (Top {searchResults.hits?.length || 0} shown)
              </span>
              <span className="text-cyan-400">Reranker: {searchResults.reranker_applied ? 'Active' : 'Bypassed'}</span>
            </div>

            <div className="space-y-3">
              {(searchResults.hits || []).map((hit: any, idx: number) => (
                <div
                  key={idx}
                  className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2 hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-white">
                        {hit.chunk_id}
                      </span>
                      <Badge variant={hit.severity === 'CRITICAL' ? 'danger' : 'info'} size="sm">
                        {hit.severity || 'INFO'}
                      </Badge>
                      <span className="text-[11px] font-mono text-slate-400">
                        [{hit.service_name || 'unknown'}]
                      </span>
                    </div>

                    <div className="flex items-center gap-3 text-[11px] font-mono">
                      <span className="text-slate-400">
                        Score: <span className="text-cyan-400 font-bold">{hit.combined_score?.toFixed(4) || hit.similarity_score?.toFixed(4) || 'N/A'}</span>
                      </span>
                      {hit.source_line_start && (
                        <span className="text-slate-500">
                          Lines {hit.source_line_start}-{hit.source_line_end}
                        </span>
                      )}
                    </div>
                  </div>

                  <pre className="p-3 bg-dark-950 rounded-lg border border-slate-850 font-mono text-xs text-slate-300 overflow-x-auto whitespace-pre-wrap leading-relaxed">
                    {hit.relevant_log_content || hit.content}
                  </pre>
                </div>
              ))}
            </div>
          </div>
        )}

        {searchError && (
          <div className="mt-4 p-3 bg-rose-950/40 border border-rose-800 rounded-lg text-xs text-rose-300 font-mono">
            {searchError}
          </div>
        )}
      </Card>
    </div>
  );
};

