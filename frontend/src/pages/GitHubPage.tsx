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
  Star,
} from 'lucide-react';
import { api } from '../services/api';
import { CommitDetails, CommitSummary, RepositoryItem } from '../types';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

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

      // Automatically fetch commits for this repo
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
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* SECTION 1: REPOSITORY REGISTRATION */}
      <Card
        title="GitHub Repository Intelligence"
        subtitle="Connect GitHub repositories to track recent commits and correlate code diffs with incident error logs"
      >
        <form onSubmit={handleRegister} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="sm:col-span-2">
              <label className="block text-xs font-semibold text-slate-300 font-mono mb-1.5">
                GitHub Repository URL or Slug *
              </label>
              <input
                type="text"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/my-org/payment-service or my-org/payment-service"
                required
                className="w-full bg-slate-950 border border-slate-700/80 rounded-lg px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-500 font-mono focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 font-mono mb-1.5">
                Linked Microservice (Optional)
              </label>
              <input
                type="text"
                value={serviceName}
                onChange={(e) => setServiceName(e.target.value)}
                placeholder="e.g. payment-service"
                className="w-full bg-slate-950 border border-slate-700/80 rounded-lg px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-500 font-mono focus:outline-none focus:border-cyan-500"
              />
            </div>
          </div>

          <div className="flex items-center justify-between pt-1">
            <span className="text-[11px] text-slate-400 font-mono">
              Supports public repositories without tokens & private repositories via GITHUB_TOKEN
            </span>
            <button
              type="submit"
              disabled={registering || !repoUrl.trim()}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-bold text-xs shadow-md transition-all flex items-center gap-2 font-mono disabled:opacity-50"
            >
              {registering ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Inspecting via GitHub API...</span>
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4" />
                  <span>Register & Inspect Repository</span>
                </>
              )}
            </button>
          </div>
        </form>

        {registerSuccess && (
          <div className="mt-4 p-4 bg-slate-900 rounded-xl border border-violet-800/80 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FolderGit2 className="w-4 h-4 text-violet-400" />
                <span className="font-bold text-xs text-white font-mono">
                  {registerSuccess.owner}/{registerSuccess.repo}
                </span>
                <Badge variant="purple" size="sm">{registerSuccess.default_branch}</Badge>
              </div>
              <div className="flex items-center gap-3 text-xs font-mono text-slate-400">
                <span className="flex items-center gap-1">
                  <Star className="w-3.5 h-3.5 text-amber-400" /> {registerSuccess.stars}
                </span>
                <span>{registerSuccess.language || 'Code'}</span>
              </div>
            </div>
            {registerSuccess.description && (
              <p className="text-xs text-slate-300">{registerSuccess.description}</p>
            )}
          </div>
        )}

        {registerError && (
          <div className="mt-4 p-3 bg-rose-950/40 border border-rose-800 rounded-lg text-xs text-rose-300 font-mono flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{registerError}</span>
          </div>
        )}
      </Card>

      {/* SECTION 2: COMMITS & DIFF EXPLORER */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Commit History */}
        <Card
          title="Recent Git Commits"
          subtitle={commits.length > 0 ? `Showing last ${commits.length} commits` : 'Enter a repository above'}
          className="lg:col-span-1"
        >
          {loadingCommits ? (
            <div className="py-8 text-center text-slate-500 font-mono text-xs">
              <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-cyan-400" />
              <span>Fetching commits...</span>
            </div>
          ) : commits.length > 0 ? (
            <div className="space-y-2 mt-2 max-h-[500px] overflow-y-auto pr-1">
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
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-violet-950/40 border-violet-500 text-white shadow-sm'
                        : 'bg-slate-950 border-slate-800 hover:border-slate-700 text-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-mono text-xs font-bold text-cyan-400">
                        {c.short_sha}
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        {new Date(c.date).toLocaleDateString()}
                      </span>
                    </div>
                    <p className="text-xs font-medium text-slate-200 line-clamp-2 leading-relaxed">
                      {c.message}
                    </p>
                    <div className="text-[10px] text-slate-400 font-mono mt-1">
                      by {c.author}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="py-8 text-center text-slate-500 font-mono text-xs">
              <GitCommit className="w-6 h-6 mx-auto mb-2 text-slate-600" />
              <span>No commits loaded yet. Register a repository to view history.</span>
            </div>
          )}
        </Card>

        {/* Right: Commit Details & Unified Diff Viewer */}
        <Card
          title="Commit Details & Unified Diff Viewer"
          subtitle={
            commitDetails
              ? `Commit ${commitDetails.short_sha} by ${commitDetails.author} (${commitDetails.files.length} changed files)`
              : 'Select a commit from the list to inspect code diff'
          }
          className="lg:col-span-2"
        >
          {loadingDetails ? (
            <div className="py-12 text-center text-slate-500 font-mono text-xs">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-cyan-400" />
              <span>Loading commit diff patch...</span>
            </div>
          ) : commitDetails ? (
            <div className="space-y-4 mt-2">
              {/* Commit Info Banner */}
              <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-cyan-400">
                      SHA: {commitDetails.sha}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-xs font-mono">
                    <span className="text-emerald-400">+{commitDetails.stats.additions || 0}</span>
                    <span className="text-rose-400">-{commitDetails.stats.deletions || 0}</span>
                  </div>
                </div>
                <h4 className="text-sm font-semibold text-white font-mono">
                  {commitDetails.message}
                </h4>
              </div>

              {/* Files Diff List */}
              <div className="space-y-3">
                {commitDetails.files.map((file, idx) => (
                  <div
                    key={idx}
                    className="rounded-xl bg-slate-950 border border-slate-800 overflow-hidden"
                  >
                    <div className="p-3 bg-slate-900 flex items-center justify-between text-xs font-mono">
                      <div className="flex items-center gap-2">
                        <FileCode className="w-4 h-4 text-violet-400" />
                        <span className="text-white font-bold">{file.filename}</span>
                      </div>
                      <div className="flex items-center gap-2 text-[11px]">
                        <span className="text-emerald-400">+{file.additions}</span>
                        <span className="text-rose-400">-{file.deletions}</span>
                      </div>
                    </div>

                    {file.patch ? (
                      <pre className="p-3.5 font-mono text-xs overflow-x-auto leading-relaxed bg-dark-950">
                        {file.patch.split('\n').map((line, lIdx) => {
                          const isAdd = line.startsWith('+');
                          const isDel = line.startsWith('-');
                          return (
                            <div
                              key={lIdx}
                              className={
                                isAdd
                                  ? 'text-emerald-300 bg-emerald-950/30'
                                  : isDel
                                  ? 'text-rose-300 bg-rose-950/30'
                                  : 'text-slate-400'
                              }
                            >
                              {line}
                            </div>
                          );
                        })}
                      </pre>
                    ) : (
                      <p className="p-3 text-xs text-slate-500 font-mono">Binary or empty diff</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="py-16 text-center text-slate-500 font-mono text-xs">
              <GitBranch className="w-8 h-8 mx-auto mb-2 text-slate-600" />
              <span>Select any commit to inspect unified diff patches and modified files.</span>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

