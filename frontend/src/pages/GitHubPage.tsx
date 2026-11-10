import React, { useState } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  ChevronRight,
  ExternalLink,
  FileCode,
  FolderGit2,
  GitBranch,
  GitCommit,
  Plus,
  RefreshCw,
  Search,
  Sparkles,
  Star,
} from 'lucide-react';
import { api } from '../services/api';
import { CommitDetails, CommitSummary, RepositoryItem } from '../types';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button3D } from '../components/ui/Button3D';
import { MotionReveal } from '../components/ui/MotionReveal';

export const GitHubPage: React.FC = () => {
  // Repo Input State
  const [repoUrl, setRepoUrl] = useState('https://github.com/octocat/Hello-World');
  const [serviceName, setServiceName] = useState('');
  const [registering, setRegistering] = useState(false);
  const [registerSuccess, setRegisterSuccess] = useState<RepositoryItem | null>(null);
  const [registerError, setRegisterError] = useState<string | null>(null);

  // Commits State
  const [commits, setCommits] = useState<CommitSummary[]>([]);
  const [loadingCommits, setLoadingCommits] = useState(false);
  const [selectedCommitSha, setSelectedCommitSha] = useState<string | null>(null);
  const [commitDetails, setCommitDetails] = useState<CommitDetails | null>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl.trim()) return;

    setRegistering(true);
    setRegisterError(null);
    setRegisterSuccess(null);

    try {
      const res = await api.registerRepository({
        url: repoUrl.trim(),
        service_name: serviceName.trim() || undefined,
      });
      setRegisterSuccess(res);
      fetchCommits(res.owner, res.repo);
    } catch (err: any) {
      setRegisterError(err.message || 'Failed to register repository');
    } finally {
      setRegistering(false);
    }
  };

  const fetchCommits = async (owner: string, repo: string) => {
    setLoadingCommits(true);
    setSelectedCommitSha(null);
    setCommitDetails(null);
    try {
      const list = await api.getRepositoryCommits(owner, repo, 10);
      setCommits(list);
      if (list.length > 0) {
        fetchCommitDetails(owner, repo, list[0].sha);
      }
    } catch (err: any) {
      console.error('Failed to fetch commits:', err);
    } finally {
      setLoadingCommits(false);
    }
  };

  const fetchCommitDetails = async (owner: string, repo: string, sha: string) => {
    setSelectedCommitSha(sha);
    setLoadingDetails(true);
    try {
      const details = await api.getCommitDetails(owner, repo, sha);
      setCommitDetails(details);
    } catch (err: any) {
      console.error('Failed to fetch commit details:', err);
    } finally {
      setLoadingDetails(false);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in pb-16">
      {/* 1. Repository Registration Card */}
      <MotionReveal direction="up" delay={0.05}>
        <Card
          surface="porcelain"
          className="relative overflow-hidden border border-ivory-200 shadow-tactile-surface"
        >
          {/* Subtle top horological accent line */}
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-electric-500 via-gold-500 to-electric-600 opacity-80" />

          <div className="p-7 sm:p-9 space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-ivory-200">
              <div className="space-y-1.5">
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-xl bg-midnight-950 flex items-center justify-center text-electric-400 shadow-md">
                    <GitBranch className="w-5 h-5 text-electric-400" />
                  </div>
                  <h2 className="font-display text-xl sm:text-2xl font-bold tracking-tight text-midnight-950">
                    GitHub Repository & Commit Intelligence
                  </h2>
                </div>
                <p className="text-xs sm:text-sm text-midnight-600 max-w-2xl leading-relaxed">
                  Track code changes, recent commits, and inspect file diffs correlated with incident error logs.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <Badge variant="gold" dot>
                  Mutation Correlator
                </Badge>
              </div>
            </div>

            <form onSubmit={handleRegister} className="space-y-5">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
                <div className="sm:col-span-2 space-y-1.5">
                  <label className="block text-xs font-semibold text-midnight-800 tracking-wide">
                    GitHub Repository URL or Slug <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={repoUrl}
                    onChange={(e) => setRepoUrl(e.target.value)}
                    placeholder="https://github.com/my-org/payment-service or my-org/payment-service"
                    required
                    className="w-full bg-white border border-ivory-300 rounded-2xl px-4 py-3 text-xs sm:text-sm text-midnight-950 placeholder-midnight-400 focus:outline-none focus:ring-2 focus:ring-electric-500/20 focus:border-electric-600 transition-all font-mono font-medium shadow-2xs"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="block text-xs font-semibold text-midnight-800 tracking-wide">
                    Linked Microservice (Optional)
                  </label>
                  <input
                    type="text"
                    value={serviceName}
                    onChange={(e) => setServiceName(e.target.value)}
                    placeholder="e.g. payment-service"
                    className="w-full bg-white border border-ivory-300 rounded-2xl px-4 py-3 text-xs sm:text-sm text-midnight-950 placeholder-midnight-400 focus:outline-none focus:ring-2 focus:ring-electric-500/20 focus:border-electric-600 transition-all font-mono font-medium shadow-2xs"
                  />
                </div>
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-ivory-200 flex-wrap gap-3">
                <span className="text-xs text-midnight-500 font-mono">
                  Supports public GitHub repositories and private repositories via configured personal access token.
                </span>

                <Button3D
                  variant="primary"
                  size="md"
                  type="submit"
                  disabled={registering || !repoUrl.trim()}
                  loading={registering}
                  icon={registering ? undefined : <Plus className="w-4 h-4" />}
                >
                  Register & Inspect Repository
                </Button3D>
              </div>
            </form>

            {/* Success Dossier */}
            {registerSuccess && (
              <MotionReveal direction="up" delay={0.05}>
                <div className="p-5 rounded-2xl bg-midnight-950 text-white border border-gold-500/30 shadow-tactile-dark space-y-3">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="flex items-center gap-3">
                      <FolderGit2 className="w-5 h-5 text-gold-400" />
                      <span className="font-display font-bold text-sm text-white">
                        {registerSuccess.owner}/{registerSuccess.repo}
                      </span>
                      <Badge variant="gold" size="sm">
                        {registerSuccess.default_branch}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-3 text-xs font-mono">
                      <span className="flex items-center gap-1 font-semibold text-gold-300">
                        <Star className="w-3.5 h-3.5 fill-gold-400 text-gold-400" />{' '}
                        {registerSuccess.stars} stars
                      </span>
                      <Badge variant="midnight" size="sm">
                        {registerSuccess.language || 'Code'}
                      </Badge>
                    </div>
                  </div>
                  {registerSuccess.description && (
                    <p className="text-xs text-midnight-300 leading-relaxed font-mono pt-1 border-t border-white/10">
                      {registerSuccess.description}
                    </p>
                  )}
                </div>
              </MotionReveal>
            )}

            {/* Error Banner */}
            {registerError && (
              <div className="p-4 bg-rose-50 border border-rose-200 rounded-2xl text-xs text-rose-900 font-medium flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                <span>{registerError}</span>
              </div>
            )}
          </div>
        </Card>
      </MotionReveal>

      {/* 2. Commits & Diff Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Commit History (1/3) */}
        <MotionReveal direction="up" delay={0.1} className="lg:col-span-1">
          <Card
            surface="porcelain"
            title="Recent Git Commits"
            subtitle={commits.length > 0 ? `Showing last ${commits.length} commits` : 'Enter a repository above'}
            icon={<GitCommit className="w-5 h-5 text-electric-600" />}
            className="border border-ivory-200 shadow-tactile-surface h-full"
          >
            {loadingCommits ? (
              <div className="py-16 text-center text-midnight-400 text-xs">
                <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-electric-600" />
                <span>Fetching repository commits...</span>
              </div>
            ) : commits.length > 0 ? (
              <div className="space-y-3 mt-2 max-h-[560px] overflow-y-auto pr-1">
                {commits.map((c) => {
                  const isSelected = selectedCommitSha === c.sha;
                  return (
                    <div
                      key={c.sha}
                      onClick={() => {
                        if (registerSuccess) {
                          fetchCommitDetails(registerSuccess.owner, registerSuccess.repo, c.sha);
                        }
                      }}
                      className={`p-4 rounded-2xl border cursor-pointer transition-all duration-200 ${
                        isSelected
                          ? 'bg-electric-50/70 border-electric-500 shadow-tactile-surface ring-2 ring-electric-500/20'
                          : 'bg-white border-ivory-200 hover:border-midnight-400 hover:bg-ivory-50/50'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-mono text-xs font-bold text-electric-700 bg-electric-100/70 px-2 py-0.5 rounded-lg border border-electric-200/80">
                          {c.short_sha}
                        </span>
                        <span className="text-[11px] font-mono text-midnight-500">
                          {new Date(c.date).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="text-xs font-display font-semibold text-midnight-950 line-clamp-2 leading-relaxed">
                        {c.message}
                      </p>
                      <div className="text-[11px] font-mono text-midnight-500 mt-2 flex items-center justify-between">
                        <span>by <strong className="text-midnight-800 font-semibold">{c.author}</strong></span>
                        <ChevronRight className="w-3.5 h-3.5 text-midnight-400" />
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="py-20 text-center text-midnight-400 text-xs">
                <GitCommit className="w-8 h-8 mx-auto mb-2 text-midnight-300" />
                <span>No commits loaded yet. Register a repository above.</span>
              </div>
            )}
          </Card>
        </MotionReveal>

        {/* Right: Commit Details & Unified Diff Viewer (2/3) */}
        <MotionReveal direction="up" delay={0.15} className="lg:col-span-2">
          <Card
            surface="porcelain"
            title="Commit Changes & Diff Viewer"
            subtitle={
              commitDetails
                ? `Commit ${commitDetails.short_sha} by ${commitDetails.author} (${commitDetails.files.length} changed files)`
                : 'Select a commit from the left list to inspect code diffs'
            }
            icon={<FileCode className="w-5 h-5 text-gold-500" />}
            className="border border-ivory-200 shadow-tactile-surface"
          >
            {loadingDetails ? (
              <div className="py-20 text-center text-midnight-400 text-xs">
                <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-electric-600" />
                <span>Loading commit diff patch...</span>
              </div>
            ) : commitDetails ? (
              <div className="space-y-4 mt-2">
                {/* Commit Summary Banner */}
                <div className="p-5 bg-gradient-to-r from-ivory-50 to-white rounded-2xl border border-ivory-200 shadow-2xs space-y-2">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <span className="font-mono text-xs font-bold text-midnight-950">
                      SHA: <span className="text-electric-600">{commitDetails.sha}</span>
                    </span>
                    <div className="flex items-center gap-2 text-xs font-mono font-bold">
                      <span className="text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-lg border border-emerald-200">
                        +{commitDetails.stats.additions || 0}
                      </span>
                      <span className="text-rose-700 bg-rose-50 px-2.5 py-0.5 rounded-lg border border-rose-200">
                        -{commitDetails.stats.deletions || 0}
                      </span>
                    </div>
                  </div>
                  <h4 className="text-sm font-display font-bold text-midnight-950 leading-snug">
                    {commitDetails.message}
                  </h4>
                </div>

                {/* Files Diff List */}
                <div className="space-y-4">
                  {commitDetails.files.map((file, idx) => (
                    <div
                      key={idx}
                      className="rounded-2xl bg-white border border-ivory-200 overflow-hidden shadow-tactile-surface"
                    >
                      <div className="p-3.5 bg-ivory-50/80 border-b border-ivory-200 flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2">
                          <FileCode className="w-4 h-4 text-electric-600" />
                          <span className="font-mono font-bold text-midnight-950">{file.filename}</span>
                        </div>
                        <div className="flex items-center gap-2 font-mono font-semibold text-[11px]">
                          <span className="text-emerald-700">+{file.additions}</span>
                          <span className="text-rose-700">-{file.deletions}</span>
                        </div>
                      </div>

                      {file.patch ? (
                        <div className="p-4 bg-midnight-950 text-white font-mono text-xs overflow-x-auto leading-relaxed border-t border-midnight-900">
                          {file.patch.split('\n').map((line, lIdx) => {
                            const isAdd = line.startsWith('+');
                            const isDel = line.startsWith('-');
                            return (
                              <div
                                key={lIdx}
                                className={
                                  isAdd
                                    ? 'text-emerald-300 bg-emerald-950/60 px-2 py-0.5 rounded-xs'
                                    : isDel
                                    ? 'text-rose-300 bg-rose-950/60 px-2 py-0.5 rounded-xs'
                                    : 'text-midnight-300 px-2 py-0.5'
                                }
                              >
                                {line}
                              </div>
                            );
                          })}
                        </div>
                      ) : (
                        <p className="p-4 text-xs text-midnight-400 font-mono">Binary or empty diff</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="py-24 text-center text-midnight-400 text-xs">
                <GitBranch className="w-10 h-10 mx-auto mb-2 text-midnight-300" />
                <span>Select any commit on the left to inspect syntax-highlighted diff patches and code mutations.</span>
              </div>
            )}
          </Card>
        </MotionReveal>
      </div>
    </div>
  );
};
