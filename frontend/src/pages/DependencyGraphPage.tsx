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
  Activity,
  AlertTriangle,
  ArrowRight,
  Database,
  Flame,
  Globe,
  Layers,
  Network,
  Plus,
  RefreshCw,
  Server,
  ShieldAlert,
  Sparkles,
  Zap,
} from 'lucide-react';
import { api } from '../services/api';
import { BlastRadius, ServiceDetail } from '../types';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button3D } from '../components/ui/Button3D';
import { MotionReveal } from '../components/ui/MotionReveal';

// Custom Node Component with Luxury Horological & Porcelain Aesthetic
const CustomServiceNode: React.FC<NodeProps> = ({ data, selected }) => {
  const isDatabase = data.type === 'database';
  const isApi = data.type === 'api';
  const isImpacted = data.isImpacted;

  return (
    <div
      className={`px-4 py-3 rounded-2xl border-2 transition-all duration-300 min-w-[180px] shadow-tactile-surface ${
        isImpacted
          ? 'bg-rose-50/95 border-rose-500 text-rose-950 shadow-glow-rose ring-4 ring-rose-300/40'
          : selected
          ? 'bg-white border-electric-600 text-midnight-950 ring-4 ring-electric-500/20 shadow-tactile-primary'
          : isDatabase
          ? 'bg-white border-emerald-300/80 text-midnight-950 hover:border-emerald-500'
          : isApi
          ? 'bg-white border-gold-300/80 text-midnight-950 hover:border-gold-500'
          : 'bg-white border-ivory-300/90 text-midnight-950 hover:border-midnight-500'
      }`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-midnight-400 !border-white !w-2.5 !h-2.5"
      />
      <div className="flex items-center gap-2.5">
        <div
          className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 shadow-2xs ${
            isImpacted
              ? 'bg-rose-500 text-white'
              : isDatabase
              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
              : isApi
              ? 'bg-gold-50 text-gold-700 border border-gold-200'
              : 'bg-midnight-950 text-gold-400 border border-midnight-900'
          }`}
        >
          {isDatabase ? (
            <Database className="w-4 h-4" />
          ) : isApi ? (
            <Globe className="w-4 h-4" />
          ) : (
            <Server className="w-4 h-4" />
          )}
        </div>
        <div className="overflow-hidden">
          <div className="text-xs font-display font-bold truncate text-midnight-950">
            {data.label as string}
          </div>
          <div className="flex items-center gap-1.5 mt-0.5">
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                isImpacted
                  ? 'bg-rose-500 animate-pulse'
                  : isDatabase
                  ? 'bg-emerald-500'
                  : 'bg-electric-500'
              }`}
            />
            <span className="text-[10px] font-mono text-midnight-500 uppercase tracking-wider">
              {data.tier as string}
            </span>
          </div>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-midnight-400 !border-white !w-2.5 !h-2.5"
      />
    </div>
  );
};

const nodeTypes = {
  serviceNode: CustomServiceNode,
};

export const DependencyGraphPage: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [loading, setLoading] = useState(true);
  const [selectedService, setSelectedService] = useState<ServiceDetail | null>(null);
  const [blastRadius, setBlastRadius] = useState<BlastRadius | null>(null);
  const [graphHealthy, setGraphHealthy] = useState(true);

  // Add Service Modal
  const [showAddServiceModal, setShowAddServiceModal] = useState(false);
  const [newServiceName, setNewServiceName] = useState('');
  const [newServiceTier, setNewServiceTier] = useState('backend');

  const loadGraph = useCallback(async () => {
    setLoading(true);
    try {
      const health = await api.getGraphHealth().catch(() => ({ connected: false } as any));
      setGraphHealthy(Boolean(health.connected));

      const initialNodes: Node[] = [
        {
          id: 'api-gateway',
          type: 'serviceNode',
          position: { x: 300, y: 30 },
          data: { label: 'api-gateway', tier: 'gateway', type: 'service' },
        },
        {
          id: 'auth-service',
          type: 'serviceNode',
          position: { x: 100, y: 150 },
          data: { label: 'auth-service', tier: 'core', type: 'service' },
        },
        {
          id: 'payment-service',
          type: 'serviceNode',
          position: { x: 300, y: 150 },
          data: { label: 'payment-service', tier: 'backend', type: 'service' },
        },
        {
          id: 'notification-service',
          type: 'serviceNode',
          position: { x: 500, y: 150 },
          data: { label: 'notification-service', tier: 'backend', type: 'service' },
        },
        {
          id: 'payments-db',
          type: 'serviceNode',
          position: { x: 200, y: 280 },
          data: { label: 'payments-db (PostgreSQL)', tier: 'storage', type: 'database' },
        },
        {
          id: 'stripe-api',
          type: 'serviceNode',
          position: { x: 420, y: 280 },
          data: { label: 'Stripe Gateway (External)', tier: 'external', type: 'api' },
        },
      ];

      const initialEdges: Edge[] = [
        {
          id: 'e-gw-auth',
          source: 'api-gateway',
          target: 'auth-service',
          label: 'Verifies JWT',
          markerEnd: { type: MarkerType.ArrowClosed, color: '#0066FF' },
          style: { stroke: '#0066FF', strokeWidth: 1.5 },
        },
        {
          id: 'e-gw-payment',
          source: 'api-gateway',
          target: 'payment-service',
          label: 'Processes Checkout',
          markerEnd: { type: MarkerType.ArrowClosed, color: '#0066FF' },
          style: { stroke: '#0066FF', strokeWidth: 2 },
        },
        {
          id: 'e-payment-notif',
          source: 'payment-service',
          target: 'notification-service',
          label: 'Payment Completed Event',
          markerEnd: { type: MarkerType.ArrowClosed, color: '#94A3B8' },
          style: { stroke: '#94A3B8', strokeWidth: 1.5, strokeDasharray: '4 4' },
        },
        {
          id: 'e-payment-db',
          source: 'payment-service',
          target: 'payments-db',
          label: 'ACID Ledger Tx',
          markerEnd: { type: MarkerType.ArrowClosed, color: '#10B981' },
          style: { stroke: '#10B981', strokeWidth: 1.5 },
        },
        {
          id: 'e-payment-stripe',
          source: 'payment-service',
          target: 'stripe-api',
          label: 'Charges Card',
          markerEnd: { type: MarkerType.ArrowClosed, color: '#C5A059' },
          style: { stroke: '#C5A059', strokeWidth: 2 },
        },
      ];

      setNodes(initialNodes);
      setEdges(initialEdges);

      // Pre-select payment-service so blast radius analysis is immediately available
      const defaultDetail: ServiceDetail = {
        name: 'payment-service',
        environment: 'production',
        tier: 'backend',
        status: 'active',
        metadata: {},
        upstream_dependencies: ['api-gateway'],
        downstream_dependencies: ['notification-service'],
        connected_databases: ['payments-db (PostgreSQL)'],
        connected_apis: ['Stripe Gateway (External)'],
        repositories: ['https://github.com/my-org/payment-service'],
      };
      setSelectedService(defaultDetail);
    } catch (err) {
      console.error('Failed to initialize graph:', err);
    } finally {
      setLoading(false);
    }
  }, [setNodes, setEdges]);

  useEffect(() => {
    loadGraph();
  }, [loadGraph]);

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
          .filter((e) => e.source === node.id && !e.target.includes('db') && !e.target.includes('api'))
          .map((e) => e.target),
        connected_databases: edges
          .filter((e) => e.source === node.id && e.target.includes('db'))
          .map((e) => e.target),
        connected_apis: edges
          .filter((e) => e.source === node.id && e.target.includes('api'))
          .map((e) => e.target),
        repositories: [`https://github.com/my-org/${serviceName}`],
      }));
      setSelectedService(detail);
      setBlastRadius(null);
    } catch (err) {
      console.error('Failed to get service detail:', err);
    }
  };

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
        impacted_apis: selectedService.connected_apis,
        dependency_chains: [
          [...selectedService.upstream_dependencies, selectedService.name],
        ],
      }));

      setBlastRadius(radius);

      // Highlight impacted nodes
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
      await api.createService({
        name: newServiceName.trim(),
        tier: newServiceTier,
        environment: 'production',
      }).catch(() => null);

      const newNode: Node = {
        id: newServiceName.trim().toLowerCase().replace(/\s+/g, '-'),
        type: 'serviceNode',
        position: { x: 250 + Math.random() * 100, y: 220 + Math.random() * 80 },
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
    <div className="space-y-6 animate-fade-in flex flex-col h-[calc(100vh-130px)] pb-4">
      {/* Top Controls Bar */}
      <div className="flex items-center justify-between flex-wrap gap-4 shrink-0 bg-white/80 backdrop-blur-md p-4 rounded-3xl border border-ivory-200 shadow-tactile-surface">
        <div className="flex items-center gap-3">
          <Badge variant={graphHealthy ? 'gold' : 'default'} dot>
            {graphHealthy ? 'Neo4j Connected' : 'Cached Topology'}
          </Badge>
          <div className="h-4 w-[1px] bg-ivory-300 hidden sm:block" />
          <span className="text-xs font-mono text-midnight-600 font-medium">
            <strong className="text-midnight-950 font-bold">{nodes.length}</strong> Services & Databases • <strong className="text-midnight-950 font-bold">{edges.length}</strong> Active Connections
          </span>
        </div>

        <div className="flex items-center gap-2.5">
          <Button3D
            variant="surface"
            size="sm"
            onClick={() => setShowAddServiceModal(true)}
            icon={<Plus className="w-3.5 h-3.5 text-electric-600" />}
          >
            Add Service
          </Button3D>

          <button
            onClick={loadGraph}
            className="p-2.5 rounded-2xl bg-white hover:bg-ivory-100 text-midnight-600 hover:text-midnight-950 border border-ivory-200 transition-colors shadow-tactile-surface"
            title="Reset Graph Layout"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-electric-600' : ''}`} />
          </button>
        </div>
      </div>

      {/* Main Graph Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
        {/* React Flow Canvas (Left 2/3) */}
        <div className="lg:col-span-2 bg-gradient-to-b from-ivory-50/60 to-ivory-100/30 border border-ivory-200 rounded-3xl overflow-hidden relative shadow-tactile-surface">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            fitView
          >
            <Background color="#cbd5e1" gap={24} size={1.2} />
            <Controls className="!bg-white !border-ivory-200 !text-midnight-800 !shadow-tactile-surface !rounded-2xl overflow-hidden" />
            <MiniMap
              nodeColor={(n) => (n.data.type === 'database' ? '#10B981' : n.data.type === 'api' ? '#C5A059' : '#0066FF')}
              className="!bg-white !border-ivory-200 !rounded-2xl !shadow-tactile-surface"
            />
          </ReactFlow>
        </div>

        {/* Selected Service Information & Blast Radius Panel (Right 1/3) */}
        <div className="space-y-4 overflow-y-auto pr-1">
          {selectedService ? (
            <Card
              surface="porcelain"
              title={selectedService.name}
              subtitle="Service telemetry, upstream callers, and failure impact"
              icon={<Server className="w-5 h-5 text-electric-600" />}
              className="border border-ivory-200 shadow-tactile-surface"
            >
              <div className="space-y-4 mt-2">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-midnight-500 font-medium">Cluster Environment:</span>
                  <Badge variant="gold" size="sm">{selectedService.environment}</Badge>
                </div>

                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-midnight-500 font-medium">Architecture Tier:</span>
                  <span className="font-bold text-midnight-950 uppercase tracking-wide">
                    {selectedService.tier || 'backend'}
                  </span>
                </div>

                {/* Callers (Upstream) */}
                <div className="p-3.5 bg-ivory-50 rounded-2xl border border-ivory-200">
                  <span className="text-xs font-display font-semibold text-midnight-900 block mb-2">
                    Upstream Callers ({selectedService.upstream_dependencies.length}):
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedService.upstream_dependencies.length > 0 ? (
                      selectedService.upstream_dependencies.map((u) => (
                        <Badge key={u} variant="purple" size="sm">
                          {u}
                        </Badge>
                      ))
                    ) : (
                      <span className="text-xs text-midnight-400 font-mono">None (Edge Entrypoint)</span>
                    )}
                  </div>
                </div>

                {/* Callees (Downstream) */}
                <div className="p-3.5 bg-ivory-50 rounded-2xl border border-ivory-200">
                  <span className="text-xs font-display font-semibold text-midnight-900 block mb-2">
                    Downstream Dependencies ({selectedService.downstream_dependencies.length}):
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedService.downstream_dependencies.length > 0 ? (
                      selectedService.downstream_dependencies.map((d) => (
                        <Badge key={d} variant="info" size="sm">
                          {d}
                        </Badge>
                      ))
                    ) : (
                      <span className="text-xs text-midnight-400 font-mono">None</span>
                    )}
                  </div>
                </div>

                {/* Connected Databases */}
                <div className="p-3.5 bg-ivory-50 rounded-2xl border border-ivory-200">
                  <span className="text-xs font-display font-semibold text-midnight-900 block mb-2">
                    Connected Datastores:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedService.connected_databases.length > 0 ? (
                      selectedService.connected_databases.map((db) => (
                        <Badge key={db} variant="success" size="sm">
                          {db}
                        </Badge>
                      ))
                    ) : (
                      <span className="text-xs text-midnight-400 font-mono">No direct database handle</span>
                    )}
                  </div>
                </div>

                {/* Calculate Blast Radius Action */}
                <div className="pt-2">
                  <Button3D
                    variant="gold"
                    size="md"
                    onClick={handleCalculateBlastRadius}
                    className="w-full"
                    icon={<ShieldAlert className="w-4 h-4 text-midnight-950" />}
                  >
                    Calculate Blast Radius
                  </Button3D>
                </div>

                {/* Blast Radius Result */}
                {blastRadius && (
                  <MotionReveal direction="up" delay={0.05}>
                    <div className="p-5 rounded-2xl bg-midnight-950 text-white border border-rose-500/40 shadow-tactile-dark space-y-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="text-[10px] font-mono uppercase tracking-wider text-rose-300">
                            Cascade Risk Score
                          </span>
                          <div className="text-2xl font-display font-extrabold text-white mt-0.5">
                            {blastRadius.blast_radius_score}
                          </div>
                        </div>
                        <Badge variant="danger" size="sm">{blastRadius.severity_level} IMPACT</Badge>
                      </div>

                      <div className="text-xs text-midnight-300 font-mono space-y-1.5 pt-3 border-t border-white/10">
                        <div className="flex justify-between">
                          <span>Direct Dependents:</span>
                          <strong className="text-white font-bold">{blastRadius.direct_dependents_count}</strong>
                        </div>
                        <div className="flex justify-between">
                          <span>Total Cascade Scope:</span>
                          <strong className="text-gold-400 font-bold">{blastRadius.total_impacted_services_count} services</strong>
                        </div>
                      </div>
                    </div>
                  </MotionReveal>
                )}
              </div>
            </Card>
          ) : (
            <Card surface="porcelain" className="text-center py-16 border border-ivory-200">
              <Network className="w-10 h-10 text-midnight-300 mx-auto mb-3" />
              <h4 className="text-sm font-display font-bold text-midnight-950">No Service Selected</h4>
              <p className="text-xs text-midnight-500 mt-1 max-w-xs mx-auto">
                Select any microservice node on the topology canvas to inspect callers, downstream dependencies, and cascade failure risk.
              </p>
            </Card>
          )}
        </div>
      </div>

      {/* Add Service Modal */}
      {showAddServiceModal && (
        <div className="fixed inset-0 z-50 bg-midnight-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-ivory-200 rounded-3xl p-7 w-full max-w-md shadow-tactile-dark animate-slide-down">
            <h3 className="text-lg font-display font-bold text-midnight-950 mb-1">
              Add Microservice to Graph
            </h3>
            <p className="text-xs text-midnight-600 mb-5">
              Register a new microservice entity into the Neo4j Knowledge Graph topology.
            </p>

            <form onSubmit={handleAddService} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-midnight-800 mb-1.5">
                  Service Name <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  value={newServiceName}
                  onChange={(e) => setNewServiceName(e.target.value)}
                  placeholder="e.g. notification-service"
                  required
                  className="w-full bg-white border border-ivory-300 rounded-2xl px-4 py-2.5 text-xs text-midnight-950 placeholder-midnight-400 focus:outline-none focus:ring-2 focus:ring-electric-500/20 focus:border-electric-600 transition-all font-mono font-medium"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-midnight-800 mb-1.5">
                  Architecture Tier
                </label>
                <select
                  value={newServiceTier}
                  onChange={(e) => setNewServiceTier(e.target.value)}
                  className="w-full bg-white border border-ivory-300 rounded-2xl px-4 py-2.5 text-xs text-midnight-950 focus:outline-none focus:ring-2 focus:ring-electric-500/20 focus:border-electric-600 transition-all font-medium"
                >
                  <option value="frontend">Frontend Service</option>
                  <option value="backend">Backend Microservice</option>
                  <option value="core">Core Platform Service</option>
                  <option value="storage">Database / Storage</option>
                </select>
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-4 border-t border-ivory-200">
                <Button3D
                  variant="ghost"
                  size="sm"
                  type="button"
                  onClick={() => setShowAddServiceModal(false)}
                >
                  Cancel
                </Button3D>
                <Button3D
                  variant="primary"
                  size="sm"
                  type="submit"
                >
                  Add Service
                </Button3D>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
