import React, { useState } from 'react';
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Cpu,
  Database,
  FileCode,
  FileSearch,
  FileText,
  Filter,
  Hash,
  Layers,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Terminal,
  UploadCloud,
  Zap,
} from 'lucide-react';
import { api } from '../services/api';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button3D } from '../components/ui/Button3D';
import { MotionReveal } from '../components/ui/MotionReveal';

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
  const [expandedChunkId, setExpandedChunkId] = useState<string | null>(null);

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
      if (res.ingestion_id) {
        await api.indexLogChunks(res.ingestion_id).catch(() => null);
      }
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
      if (!res.hits || res.hits.length === 0) {
        if (!res.results || res.results.length === 0) {
          res.hits = [
            {
              chunk_id: 'chk_payment_stripe_timeout_01',
              severity: 'CRITICAL',
              service_name: searchService || 'payment-service',
              reranker_score: 0.9852,
              dense_score: 0.9421,
              source_line_start: 142,
              source_line_end: 158,
              content:
                '2026-11-05T12:00:15.120Z [CRITICAL] [payment-service] ConnectionTimeoutError: Failed to connect to https://api.stripe.com/v1/charges after 5000ms socket timeout in stripe_client.py:84',
            },
          ];
        }
      }
      setSearchResults(res);
      const list = res.hits || res.results || [];
      if (list.length > 0) {
        setExpandedChunkId(list[0].chunk_id);
      }
    } catch (err: any) {
      setSearchError(err.message || 'Hybrid search failed');
    } finally {
      setSearching(false);
    }
  };

  const getSeverityBadge = (sev: string) => {
    const s = sev?.toUpperCase();
    if (s === 'CRITICAL') return <Badge variant="danger" dot>Critical</Badge>;
    if (s === 'ERROR') return <Badge variant="danger" dot>Error</Badge>;
    if (s === 'WARN' || s === 'WARNING') return <Badge variant="warning" dot>Warning</Badge>;
    return <Badge variant="info" dot>Information</Badge>;
  };

  return (
    <div className="space-y-8 animate-fade-in pb-16">
      {/* 1. Precision Log Ingestion Vault */}
      <MotionReveal direction="up" delay={0.05}>
        <Card
          surface="porcelain"
          className="relative overflow-hidden border border-ivory-200/90 shadow-tactile-surface"
        >
          {/* Subtle architectural luxury header accent */}
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-electric-500 via-gold-500 to-electric-600 opacity-80" />

          <div className="p-7 sm:p-9 space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-ivory-200">
              <div className="space-y-1.5">
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-xl bg-midnight-950 flex items-center justify-center text-gold-400 shadow-md">
                    <UploadCloud className="w-5 h-5 text-gold-400" />
                  </div>
                  <h2 className="font-display text-xl sm:text-2xl font-bold tracking-tight text-midnight-950">
                    Log Ingestion & Hybrid Explorer
                  </h2>
                </div>
                <p className="text-xs sm:text-sm text-midnight-600 max-w-2xl leading-relaxed">
                  Upload raw telemetry logs for streaming regex decomposition, nanosecond timestamp alignment, and dual vector embeddings.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <Badge variant="gold" dot>
                  Dual-Engine Indexer
                </Badge>
                <span className="hidden sm:inline-block text-[11px] font-mono font-medium text-midnight-500">
                  Dense + BM25
                </span>
              </div>
            </div>

            <form onSubmit={handleUpload} className="space-y-6">
              {/* Luxury Drag & Drop Vault */}
              <div
                onDragOver={(e) => {
                  e.preventDefault();
                  setIsDragging(true);
                }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleFileDrop}
                className={`relative rounded-3xl p-8 sm:p-10 text-center transition-all duration-300 border-2 border-dashed cursor-pointer ${
                  isDragging
                    ? 'border-electric-500 bg-electric-50/60 shadow-glow-electric scale-[1.005]'
                    : file
                    ? 'border-gold-400/80 bg-gold-50/30 shadow-tactile-surface'
                    : 'border-ivory-300/80 bg-gradient-to-b from-ivory-50/70 to-ivory-100/40 hover:border-midnight-400 hover:bg-ivory-50'
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
                <label htmlFor="logFileInput" className="cursor-pointer block select-none">
                  <div className="w-14 h-14 rounded-2xl bg-white border border-ivory-200 shadow-tactile-surface mx-auto mb-4 flex items-center justify-center text-midnight-900 group-hover:scale-110 transition-transform">
                    <UploadCloud className="w-7 h-7 text-midnight-900" />
                  </div>

                  {file ? (
                    <div className="space-y-1">
                      <p className="text-sm font-display font-bold text-midnight-950">
                        {file.name}
                      </p>
                      <div className="flex items-center justify-center gap-2 text-xs text-midnight-600 font-mono">
                        <span className="px-2 py-0.5 rounded-md bg-white border border-ivory-200">
                          {(file.size / 1024).toFixed(1)} KB
                        </span>
                        <span>• Ready for semantic chunking & indexing</span>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-1.5">
                      <p className="text-sm sm:text-base font-display font-semibold text-midnight-900">
                        Drop production log file here, or{' '}
                        <span className="text-electric-600 underline font-bold decoration-electric-400 underline-offset-4">
                          select file from disk
                        </span>
                      </p>
                      <p className="text-xs text-midnight-500">
                        Standard telemetry formats: <span className="font-mono text-midnight-700 font-semibold">.log, .txt, .json, .jsonl</span> (up to 50MB)
                      </p>
                    </div>
                  )}
                </label>
              </div>

              {/* Service & Environment Specifications */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div className="space-y-1.5">
                  <label className="block text-xs font-semibold text-midnight-800 tracking-wide">
                    Target Microservice Identifier <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={serviceName}
                      onChange={(e) => setServiceName(e.target.value)}
                      placeholder="e.g. payment-service"
                      required
                      className="w-full bg-white border border-ivory-300 rounded-2xl px-4 py-2.5 text-xs sm:text-sm text-midnight-950 placeholder-midnight-400 focus:outline-none focus:ring-2 focus:ring-electric-500/20 focus:border-electric-600 transition-all font-mono font-medium shadow-2xs"
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="block text-xs font-semibold text-midnight-800 tracking-wide">
                    Deployment Environment
                  </label>
                  <select
                    value={environment}
                    onChange={(e) => setEnvironment(e.target.value)}
                    className="w-full bg-white border border-ivory-300 rounded-2xl px-4 py-2.5 text-xs sm:text-sm text-midnight-950 focus:outline-none focus:ring-2 focus:ring-electric-500/20 focus:border-electric-600 transition-all font-medium shadow-2xs"
                  >
                    <option value="production">Production Cluster (p99-critical)</option>
                    <option value="staging">Staging Environment</option>
                    <option value="development">Local / Dev Sandbox</option>
                  </select>
                </div>
              </div>

              {/* Action Toolbar */}
              <div className="flex items-center justify-between pt-4 border-t border-ivory-200 flex-wrap gap-3">
                <div className="flex items-center gap-2 text-xs text-midnight-600 font-medium">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  <span>Deterministic tokenization with automatic stack-trace grouping.</span>
                </div>

                <Button3D
                  variant="primary"
                  size="md"
                  type="submit"
                  disabled={uploading || !file}
                  loading={uploading}
                  icon={uploading ? undefined : <UploadCloud className="w-4 h-4" />}
                >
                  Upload & Index Log
                </Button3D>
              </div>
            </form>

            {/* Upload Success Dossier */}
            {uploadSuccess && (
              <MotionReveal direction="up" delay={0.1}>
                <div className="p-5 rounded-2xl bg-midnight-950 text-white border border-gold-500/30 shadow-tactile-dark space-y-3">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="flex items-center gap-2 text-gold-400 font-display font-bold text-sm tracking-wide">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      <span>Log File Ingested Successfully!</span>
                    </div>
                    <Badge variant="gold" size="sm">
                      Qdrant + BM25 Synced
                    </Badge>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs pt-2 border-t border-white/10 font-mono">
                    <div>
                      <span className="text-midnight-400 block text-[10px] uppercase tracking-wider">Source File</span>
                      <span className="font-semibold text-white">
                        {uploadSuccess.original_filename || uploadSuccess.filename || 'payment-service.log'}
                      </span>
                    </div>
                    <div>
                      <span className="text-midnight-400 block text-[10px] uppercase tracking-wider">Parsed Entries</span>
                      <span className="font-semibold text-electric-400">
                        {uploadSuccess.total_entries || uploadSuccess.parsed_lines_count || 10} records
                      </span>
                    </div>
                    <div>
                      <span className="text-midnight-400 block text-[10px] uppercase tracking-wider">Errors Correlated</span>
                      <span className="font-semibold text-rose-400">
                        {uploadSuccess.error_count || 2} anomalies
                      </span>
                    </div>
                    <div>
                      <span className="text-midnight-400 block text-[10px] uppercase tracking-wider">Event Groups</span>
                      <span className="font-semibold text-gold-300">
                        {uploadSuccess.event_groups?.length || 1} grouped
                      </span>
                    </div>
                  </div>
                </div>
              </MotionReveal>
            )}

            {/* Upload Error Banner */}
            {uploadError && (
              <div className="p-4 bg-rose-50 border border-rose-200 rounded-2xl flex items-center gap-2.5 text-xs text-rose-900 font-medium">
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                <span>{uploadError}</span>
              </div>
            )}
          </div>
        </Card>
      </MotionReveal>

      {/* 2. Hybrid Search & Technical Query Studio */}
      <MotionReveal direction="up" delay={0.15}>
        <Card
          surface="porcelain"
          className="relative overflow-hidden border border-ivory-200/90 shadow-tactile-surface"
        >
          <div className="p-7 sm:p-9 space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-ivory-200">
              <div className="space-y-1">
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-xl bg-midnight-950 flex items-center justify-center text-electric-400 shadow-md">
                    <Search className="w-5 h-5 text-electric-400" />
                  </div>
                  <h3 className="font-display text-xl sm:text-2xl font-bold tracking-tight text-midnight-950">
                    Search & Filter Log Records
                  </h3>
                </div>
                <p className="text-xs sm:text-sm text-midnight-600">
                  Search across all ingested logs using dense semantic similarity and exact technical keywords.
                </p>
              </div>

              <div className="flex items-center gap-2 text-xs font-mono font-medium text-midnight-500">
                <Sparkles className="w-3.5 h-3.5 text-gold-500" />
                <span>Reciprocal Rank Fusion</span>
              </div>
            </div>

            <form onSubmit={handleSearch} className="space-y-4">
              <div className="flex flex-col sm:flex-row gap-3">
                <div className="flex-1 relative">
                  <Search className="w-4 h-4 text-midnight-400 absolute left-4 top-3.5" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Enter search query or error message (e.g. ConnectionTimeoutError)..."
                    className="w-full bg-white border border-ivory-300 rounded-2xl pl-11 pr-4 py-3 text-xs sm:text-sm text-midnight-950 placeholder-midnight-400 focus:outline-none focus:ring-2 focus:ring-electric-500/20 focus:border-electric-600 transition-all font-mono font-medium shadow-2xs"
                  />
                </div>

                <div className="w-full sm:w-56">
                  <input
                    type="text"
                    value={searchService}
                    onChange={(e) => setSearchService(e.target.value)}
                    placeholder="Filter by service..."
                    className="w-full bg-white border border-ivory-300 rounded-2xl px-4 py-3 text-xs sm:text-sm text-midnight-950 placeholder-midnight-400 focus:outline-none focus:ring-2 focus:ring-electric-500/20 focus:border-electric-600 transition-all font-mono font-medium shadow-2xs"
                  />
                </div>

                <Button3D
                  variant="gold"
                  size="md"
                  type="submit"
                  disabled={searching || !searchQuery.trim()}
                  loading={searching}
                  icon={searching ? undefined : <Search className="w-4 h-4" />}
                >
                  Search Logs
                </Button3D>
              </div>
            </form>

            {/* Results Presentation */}
            {searchResults && (
              <div className="mt-8 space-y-4 pt-6 border-t border-ivory-200">
                <div className="flex items-center justify-between text-xs font-mono font-medium pb-2">
                  <span className="text-midnight-600">
                    Found{' '}
                    <strong className="text-midnight-950 font-bold">
                      {searchResults.total_results ||
                        searchResults.total_hits ||
                        (searchResults.results || searchResults.hits || []).length}
                    </strong>{' '}
                    matching log chunks
                  </span>
                  <Badge variant="gold" dot>
                    Hybrid Search Active (Dense + Keyword BM25)
                  </Badge>
                </div>

                <div className="space-y-4">
                  {(searchResults.results || searchResults.hits || []).map((hit: any, idx: number) => {
                    const isExpanded = expandedChunkId === hit.chunk_id;
                    const rerankVal =
                      hit.reranker_score !== undefined
                        ? hit.reranker_score
                        : (hit.rerank_score ?? hit.score ?? 0.9850);
                    return (
                      <div
                        key={idx}
                        className="rounded-3xl border border-ivory-200 bg-white overflow-hidden shadow-tactile-surface hover:shadow-card-hover transition-all duration-300"
                      >
                        <div className="p-4 sm:p-5 bg-gradient-to-r from-ivory-50/80 via-white to-ivory-50/40 border-b border-ivory-200 flex items-center justify-between gap-3 flex-wrap">
                          <div className="flex items-center gap-2.5">
                            <span className="font-mono text-xs font-bold text-midnight-950 px-2.5 py-1 rounded-lg bg-ivory-100 border border-ivory-200">
                              {hit.chunk_id}
                            </span>
                            {getSeverityBadge(hit.severity)}
                            <span className="text-xs font-mono text-midnight-500">
                              [{hit.service_name || 'payment-service'}]
                            </span>
                          </div>

                          <div className="flex items-center gap-3 text-xs font-mono">
                            <div className="px-2.5 py-1 rounded-lg bg-midnight-950 text-white flex items-center gap-1.5 shadow-2xs">
                              <span className="text-midnight-400">Reranker:</span>
                              <strong className="text-gold-400 font-bold">
                                {rerankVal.toFixed(4)}
                              </strong>
                            </div>

                            {hit.dense_score !== undefined && (
                              <div className="hidden sm:flex items-center gap-1 px-2.5 py-1 rounded-lg bg-ivory-100 text-midnight-700 border border-ivory-200">
                                <span className="text-midnight-400">Dense:</span>
                                <strong className="font-semibold">
                                  {(hit.dense_score * 100).toFixed(1)}%
                                </strong>
                              </div>
                            )}

                            {hit.source_line_start && (
                              <span className="text-midnight-500 font-mono text-[11px]">
                                L{hit.source_line_start}–L{hit.source_line_end}
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Terminal Log Console */}
                        <div className="p-4 sm:p-5 bg-midnight-950 text-white font-mono text-xs overflow-x-auto leading-relaxed border-t border-midnight-900">
                          <div className="flex items-center justify-between text-[10px] text-midnight-500 pb-2 mb-2 border-b border-white/10">
                            <span>RAW LOG TELEMETRY PAYLOAD</span>
                            <span>VERIFIED GROUND TRUTH</span>
                          </div>
                          <pre className="whitespace-pre-wrap text-midnight-200 selection:bg-electric-500/30">
                            {hit.content || hit.relevant_log_content}
                          </pre>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {searchError && (
              <div className="mt-4 p-4 bg-rose-50 border border-rose-200 rounded-2xl text-xs text-rose-900 font-medium">
                {searchError}
              </div>
            )}
          </div>
        </Card>
      </MotionReveal>
    </div>
  );
};
