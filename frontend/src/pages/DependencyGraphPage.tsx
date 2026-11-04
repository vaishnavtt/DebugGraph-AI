import React, { useCallback, useEffect, useState } from 'react';
import {
  Background,
  Controls,
  Edge,
  Handle,
  MarkerType,
  MiniMap,
  Node,
  NodeProps,
  Position,
  ReactFlow,
  useEdgesState,
  useNodesState,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {
  AlertTriangle,
  Database,
  Globe,
  Layers,
  Network,
  Plus,
  RefreshCw,
  Server,
  ShieldAlert,
  Zap,
} from 'lucide-react';
import { api } from '../services/api';
import { BlastRadius, ServiceDetail } from '../types';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

// Custom Node Component for Service Topology
const CustomServiceNode: React.FC<NodeProps> = ({ data, selected }) => {
  const isDatabase = data.type === 'database';
  const isApi = data.type === 'api';
  const isImpacted = data.isImpacted;

  return (
    <div
      className={`px-4 py-3 rounded-xl border font-mono transition-all shadow-lg ${
        isImpacted
          ? 'bg-rose-950/80 border-rose-500 text-rose-200 shadow-rose-900/40 ring-2 ring-rose-500/50'
          : selected
          ? 'bg-indigo-950/90 border-cyan-400 text-white shadow-cyan-500/20 ring-2 ring-cyan-400/40'
          : 'bg-dark-900 border-slate-700/80 text-slate-200 hover:border-slate-500'
      }`}
    >
      <Handle type="target" position={Position.Top} className="!bg-slate-400 !w-2 !h-2" />
      <div className="flex items-center gap-2">
        {isDatabase ? (
          <Database className="w-4 h-4 text-emerald-400 shrink-0" />
        ) : isApi ? (
          <Globe className="w-4 h-4 text-amber-400 shrink-0" />
        ) : (
          <Server className="w-4 h-4 text-indigo-400 shrink-0" />
        )}
        <div>
          <div className="text-xs font-bold leading-tight truncate max-w-[140px]">{data.label as string}</div>
          <div className="text-[10px] text-slate-400 capitalize">
            {isDatabase ? 'Database' : isApi ? 'API Endpoint' : (data.tier as string) || 'Service'}
          </div>
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-cyan-400 !w-2 !h-2" />
    </div>
  );
};

const nodeTypes = {
  serviceNode: CustomServiceNode,
};

export const DependencyGraphPage: React.FC = () => {
  // Graph Data
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [loading, setLoading] = useState(true);
  const [selectedService, setSelectedService] = useState<ServiceDetail | null>(null);
  const [blastRadius, setBlastRadius] = useState<BlastRadius | null>(null);
  const [graphHealthy, setGraphHealthy] = useState(true);

  // Modal State
  const [showAddServiceModal, setShowAddServiceModal] = useState(false);
  const [showAddDepModal, setShowAddDepModal] = useState(false);
  const [newServiceName, setNewServiceName] = useState('');
  const [newServiceTier, setNewServiceTier] = useState('backend');
  const [depSource, setDepSource] = useState('');
  const [depTarget, setDepTarget] = useState('');

  // Initial Seed Topology
  const loadGraph = useCallback(async () => {
    setLoading(true);
    try {
      const health = await api.getGraphHealth().catch(() => ({ connected: false }));
      setGraphHealthy(Boolean(health.connected));

      // Build visual representation of microservices
      const initialNodes: Node[] = [
        {
          id: 'checkout-service',
          type: 'serviceNode',
          position: { x: 250, y: 50 },
          data: { label: 'checkout-service', tier: 'frontend', type: 'service' },
        },
        {
          id: 'order-service',
          type: 'serviceNode',
          position: { x: 100, y: 160 },
          data: { label: 'order-service', tier: 'backend', type: 'service' },
        },
        {
          id: 'payment-service',
          type: 'serviceNode',
          position: { x: 400, y: 160 },
          data: { label: 'payment-service', tier: 'backend', type: 'service' },
        },
        {
          id: 'auth-service',
          type: 'serviceNode',
          position: { x: 250, y: 280 },
          data: { label: 'auth-service', tier: 'core', type: 'service' },
        },
        {
          id: 'payments-db',
          type: 'serviceNode',
          position: { x: 550, y: 280 },
          data: { label: 'payments-db', tier: 'storage', type: 'database' },
        },
        {
          id: 'stripe-api',
          type: 'serviceNode',
          position: { x: 550, y: 80 },
          data: { label: 'Stripe Gateway', tier: 'external', type: 'api' },
        },
      ];

      const initialEdges: Edge[] = [
        {
          id: 'e-checkout-order',
          source: 'checkout-service',
          target: 'order-service',
          label: 'DEPENDS_ON',
          markerEnd: { type: MarkerType.ArrowClosed, color: '#818cf8' },
          style: { stroke: '#818cf8' },
        },
        {
          id: 'e-checkout-payment',
          source: 'checkout-service',
          target: 'payment-service',
          label: 'DEPENDS_ON',
          markerEnd: { type: MarkerType.ArrowClosed, color: '#818cf8' },
          style: { stroke: '#818cf8' },
        },
        {
          id: 'e-order-auth',
          source: 'order-service',
          target: 'auth-service',
          label: 'CALLS',
          markerEnd: { type: MarkerType.ArrowClosed, color: '#38bdf8' },
          style: { stroke: '#38bdf8' },
        },
        {
          id: 'e-payment-auth',
          source: 'payment-service',
          target: 'auth-service',
          label: 'CALLS',
          markerEnd: { type: MarkerType.ArrowClosed, color: '#38bdf8' },
          style: { stroke: '#38bdf8' },
        },
        {
          id: 'e-payment-db',
          source: 'payment-service',
          target: 'payments-db',
          label: 'CONNECTS_TO',
          markerEnd: { type: MarkerType.ArrowClosed, color: '#34d399' },
          style: { stroke: '#34d399' },
        },
        {
          id: 'e-payment-stripe',
          source: 'payment-service',
          target: 'stripe-api',
          label: 'CALLS',
          markerEnd: { type: MarkerType.ArrowClosed, color: '#fbbf24' },
          style: { stroke: '#fbbf24' },
        },
      ];

      setNodes(initialNodes);
      setEdges(initialEdges);
    } catch (err) {
      console.error('Failed to initialize graph:', err);
    } finally {
      setLoading(false);
    }
  }, [setNodes, setEdges]);

  useEffect(() => {
    loadGraph();
  }, [loadGraph]);

  // Handle Node Click to show details
  const onNodeClick = async (_: React.MouseEvent, node: Node) => {
    const serviceName = node.data.label as string;
    try {
      const detail = await api.getService(serviceName).catch(() => ({
        name: serviceName,
        environment: 'production',
        tier: (node.data.tier as string) || 'backend',
        status: 'active',
        metadata: {},
        upstream_dependencies: edges
          .filter((e) => e.target === node.id)
          .map((e) => e.source),
        downstream_dependencies: edges
          .filter((e) => e.source === node.id && e.target !== 'payments-db')
          .map((e) => e.target),
        connected_databases: edges
          .filter((e) => e.source === node.id && e.target.includes('db'))
          .map((e) => e.target),
        connected_apis: [],
        repositories: [`https://github.com/my-org/${serviceName}`],
      }));
      setSelectedService(detail);
      setBlastRadius(null);
    } catch (err) {
      console.error('Failed to get service detail:', err);
    }
  };

  // Calculate Blast Radius
  const handleCalculateBlastRadius = async () => {
    if (!selectedService) return;
    try {
      const radius = await api.getBlastRadius(selectedService.name).catch(() => ({
        service_name: selectedService.name,
        blast_radius_score: 0.65,
        severity_level: 'HIGH' as const,
        direct_dependents_count: selectedService.upstream_dependencies.length,
        total_impacted_services_count:
          selectedService.upstream_dependencies.length +
          selectedService.downstream_dependencies.length,
        impacted_services: [
          ...selectedService.upstream_dependencies,
          ...selectedService.downstream_dependencies,
        ],
        impacted_databases: selectedService.connected_databases,
        impacted_apis: [],
        dependency_chains: [
          [...selectedService.upstream_dependencies, selectedService.name],
        ],
      }));

      setBlastRadius(radius);

      // Highlight impacted nodes on canvas
      setNodes((nds) =>
        nds.map((n) => {
          const isAffected =
            radius.impacted_services.includes(n.id) ||
            radius.impacted_databases.includes(n.id) ||
            n.id === selectedService.name;
          return {
            ...n,
            data: {
              ...n.data,
              isImpacted: isAffected,
            },
          };
        })
      );
    } catch (err) {
      console.error('Failed to calculate blast radius:', err);
    }
  };

  const handleAddService = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newServiceName.trim()) return;

    try {
      await api.registerService({
        name: newServiceName.trim(),
        tier: newServiceTier,
      });

      const newNode: Node = {
        id: newServiceName.trim(),
        type: 'serviceNode',
        position: { x: 300, y: 200 },
        data: { label: newServiceName.trim(), tier: newServiceTier, type: 'service' },
      };

      setNodes((nds) => [...nds, newNode]);
      setShowAddServiceModal(false);
      setNewServiceName('');
    } catch (err) {
      console.error('Failed to register service:', err);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto h-[calc(100vh-64px)] flex flex-col">
      {/* Header Controls */}
      <div className="flex items-center justify-between flex-wrap gap-4 shrink-0">
        <div className="flex items-center gap-3">
          <Badge variant={graphHealthy ? 'success' : 'default'}>
            {graphHealthy ? 'Neo4j Bolt Connected' : 'Neo4j Offline (Cached Topology)'}
          </Badge>
          <span className="text-xs text-slate-400 font-mono">
            {nodes.length} Nodes • {edges.length} Directed Relationships
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowAddServiceModal(true)}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-mono transition-colors flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5 text-cyan-400" />
            <span>Add Service</span>
          </button>

          <button
            onClick={loadGraph}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700 transition-colors"
            title="Reset layout"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Main Flow Canvas and Side-Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
        {/* Interactive React Flow Canvas */}
        <div className="lg:col-span-2 bg-slate-950 border border-slate-800 rounded-2xl overflow-hidden relative shadow-inner">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            fitView
          >
            <Background color="#1e293b" gap={16} />
            <Controls className="!bg-slate-900 !border-slate-800 !text-slate-300" />
            <MiniMap
              nodeColor={(n) => (n.data.type === 'database' ? '#10b981' : '#6366f1')}
              className="!bg-dark-900 !border-slate-800"
            />
          </ReactFlow>
        </div>

        {/* Node Inspection & Blast Radius Panel */}
        <div className="space-y-4 overflow-y-auto">
          {selectedService ? (
            <Card
              title={selectedService.name}
              subtitle="Microservice topology properties & connections"
            >
              <div className="space-y-4 mt-2">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-slate-400">Environment:</span>
                  <Badge variant="purple">{selectedService.environment}</Badge>
                </div>

                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-slate-400">Architecture Tier:</span>
                  <span className="text-white font-bold capitalize">
                    {selectedService.tier || 'backend'}
                  </span>
                </div>

                {/* Callers (Upstream) */}
                <div>
                  <span className="text-[11px] font-mono text-slate-400 block mb-1">
                    Upstream Callers ({selectedService.upstream_dependencies.length}):
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedService.upstream_dependencies.length > 0 ? (
                      selectedService.upstream_dependencies.map((u) => (
                        <Badge key={u} variant="purple">
                          {u}
                        </Badge>
                      ))
                    ) : (
                      <span className="text-xs text-slate-500 font-mono">None (Edge Service)</span>
                    )}
                  </div>
                </div>

                {/* Callees (Downstream) */}
                <div>
                  <span className="text-[11px] font-mono text-slate-400 block mb-1">
                    Downstream Dependencies ({selectedService.downstream_dependencies.length}):
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedService.downstream_dependencies.length > 0 ? (
                      selectedService.downstream_dependencies.map((d) => (
                        <Badge key={d} variant="info">
                          {d}
                        </Badge>
                      ))
                    ) : (
                      <span className="text-xs text-slate-500 font-mono">None</span>
                    )}
                  </div>
                </div>

                {/* Connected Databases */}
                <div>
                  <span className="text-[11px] font-mono text-slate-400 block mb-1">
                    Connected Databases:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedService.connected_databases.length > 0 ? (
                      selectedService.connected_databases.map((db) => (
                        <Badge key={db} variant="success">
                          {db}
                        </Badge>
                      ))
                    ) : (
                      <span className="text-xs text-slate-500 font-mono">None</span>
                    )}
                  </div>
                </div>

                {/* Blast Radius Action */}
                <div className="pt-3 border-t border-slate-800">
                  <button
                    onClick={handleCalculateBlastRadius}
                    className="w-full py-2.5 rounded-xl bg-gradient-to-r from-rose-600 to-amber-600 hover:from-rose-500 hover:to-amber-500 text-white font-bold text-xs shadow-md shadow-rose-900/30 transition-all flex items-center justify-center gap-2 font-mono"
                  >
                    <ShieldAlert className="w-4 h-4" />
                    <span>Calculate Failure Blast Radius</span>
                  </button>
                </div>

                {/* Blast Radius Result Banner */}
                {blastRadius && (
                  <div className="p-4 bg-slate-950 rounded-xl border border-rose-900/60 space-y-3 animate-fadeIn">
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-[10px] font-mono text-slate-400">Cascade Risk Score</span>
                        <div className="text-xl font-extrabold text-rose-400">
                          {blastRadius.blast_radius_score}
                        </div>
                      </div>
                      <Badge variant="danger">{blastRadius.severity_level} IMPACT</Badge>
                    </div>

                    <div className="text-xs font-mono space-y-1 text-slate-300">
                      <div>
                        Direct Callers: <span className="text-white font-bold">{blastRadius.direct_dependents_count}</span>
                      </div>
                      <div>
                        Total Impact Scope: <span className="text-white font-bold">{blastRadius.total_impacted_services_count} services</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </Card>
          ) : (
            <Card className="text-center py-12">
              <Network className="w-8 h-8 text-slate-600 mx-auto mb-2" />
              <h4 className="text-xs font-bold text-slate-300">No Service Selected</h4>
              <p className="text-xs text-slate-500 font-mono mt-1">
                Click any service node on the canvas to inspect dependencies and calculate cascade impact.
              </p>
            </Card>
          )}
        </div>
      </div>

      {/* Add Service Modal */}
      {showAddServiceModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-dark-900 border border-slate-700 rounded-2xl p-6 w-full max-w-md shadow-2xl">
            <h3 className="text-sm font-bold text-white font-mono mb-4">Register Microservice</h3>
            <form onSubmit={handleAddService} className="space-y-4">
              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1">Service Name *</label>
                <input
                  type="text"
                  value={newServiceName}
                  onChange={(e) => setNewServiceName(e.target.value)}
                  placeholder="e.g. notification-service"
                  required
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 font-mono focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1">Architecture Tier</label>
                <select
                  value={newServiceTier}
                  onChange={(e) => setNewServiceTier(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 font-mono focus:outline-none focus:border-cyan-500"
                >
                  <option value="frontend">frontend</option>
                  <option value="backend">backend</option>
                  <option value="core">core</option>
                  <option value="storage">storage</option>
                </select>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddServiceModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 text-slate-300 text-xs font-mono hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold font-mono"
                >
                  Add Node
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

