import React, { useEffect, useMemo, useState } from 'react';
import {
  startClearMLStack,
  stopClearMLStack,
  getClearMLStackStatus,
  isStackControlForbidden,
  extractStackLinks,
} from 'services/stack';
import {
  startSimulation,
  stopSimulation,
  pauseSimulation,
  resumeSimulation,
  setSimulationSpeed,
  getSimulationSnapshot,
} from 'services/simulation';
import {
  getRuntimeConfig,
  patchRuntimeConfig,
  getSettings,
  postSettings,
} from 'services/settings';
import { ClearMLStackStatus, SimulationSnapshot } from 'types/api';

type Json = Record<string, any> | null;

const Section: React.FC<{ title: string; subtitle?: string; children: React.ReactNode; right?: React.ReactNode }> = ({
  title,
  subtitle,
  children,
  right,
}) => (
  <section className="card">
    <div className="card-header">
      <div>
        <h2 className="card-title">{title}</h2>
        {subtitle ? <p className="card-subtitle">{subtitle}</p> : null}
      </div>
      {right}
    </div>
    <div>{children}</div>
  </section>
);

const JSONBlock: React.FC<{ data: Json; className?: string; label?: string }> = ({ data, className = '', label }) => (
  <div className={`mt-3`}>
    {label ? <div className="text-sm text-gray-600 mb-1">{label}</div> : null}
    <pre className={`bg-gray-50 border border-gray-200 rounded p-3 text-xs font-mono whitespace-pre-wrap ${className}`}>
      {data ? JSON.stringify(data, null, 2) : '—'}
    </pre>
  </div>
);

const Alert: React.FC<{ tone: 'error' | 'warning' | 'info' | 'success'; children: React.ReactNode }> = ({
  tone,
  children,
}) => {
  const toneMap = {
    error: 'bg-danger-50 text-danger-800 border-danger-200',
    warning: 'bg-warning-50 text-warning-800 border-warning-200',
    info: 'bg-blue-50 text-blue-800 border-blue-200',
    success: 'bg-success-50 text-success-800 border-success-200',
  } as const;
  return <div className={`border rounded p-3 text-sm ${toneMap[tone]}`}>{children}</div>;
};

const LinkButton: React.FC<{ href?: string; label: string }> = ({ href, label }) => {
  if (!href) return <span className="text-gray-400 text-sm">{label}</span>;
  return (
    <a
      className="btn btn-sm btn-secondary"
      href={href}
      target="_blank"
      rel="noopener noreferrer"
    >
      {label}
    </a>
  );
};

export const ControlCenter: React.FC = () => {
  // Stack state
  const [composePath, setComposePath] = useState<string>('');
  const [stackStatus, setStackStatus] = useState<ClearMLStackStatus | null>(null);
  const [stackLastResponse, setStackLastResponse] = useState<Json>(null);
  const [stackError, setStackError] = useState<string | null>(null);
  const [stackForbidden, setStackForbidden] = useState<boolean>(false);

  // Orchestrator state
  const [snapshot, setSnapshot] = useState<SimulationSnapshot | null>(null);
  const [speed, setSpeed] = useState<number>(1);
  const [simLastResponse, setSimLastResponse] = useState<Json>(null);
  const [simError, setSimError] = useState<string | null>(null);

  // Settings state
  const [runtimeConfig, setRuntimeConfig] = useState<Json>(null);
  const [runtimeConfigText, setRuntimeConfigText] = useState<string>('{}');
  const [configError, setConfigError] = useState<string | null>(null);
  const [configSuccess, setConfigSuccess] = useState<string | null>(null);

  const [uiSettings, setUiSettings] = useState<Json>(null);
  const [uiSettingsText, setUiSettingsText] = useState<string>('{}');
  const [uiError, setUiError] = useState<string | null>(null);
  const [uiSuccess, setUiSuccess] = useState<string | null>(null);

  const stackLinks = useMemo(() => extractStackLinks(stackStatus), [stackStatus]);

  // Initial loads (best-effort, non-blocking)
  useEffect(() => {
    const init = async () => {
      // ClearML stack status
      try {
        const status = await getClearMLStackStatus();
        setStackStatus(status);
        setStackForbidden(false);
        setStackError(null);
      } catch (e: any) {
        if (isStackControlForbidden(e)) {
          setStackForbidden(true);
          setStackError('Stack controls disabled on server.');
        } else {
          setStackError(e?.message || 'Failed to fetch stack status');
        }
      }

      // Simulation snapshot
      try {
        const snap = await getSimulationSnapshot();
        setSnapshot(snap);
        setSimError(null);
      } catch (e: any) {
        setSimError(e?.message || 'Failed to fetch simulation snapshot');
      }

      // Runtime config
      try {
        const cfg = await getRuntimeConfig();
        setRuntimeConfig(cfg);
        setRuntimeConfigText(JSON.stringify(cfg, null, 2));
        setConfigError(null);
      } catch (e: any) {
        setConfigError(e?.message || 'Failed to fetch runtime config');
      }

      // UI settings
      try {
        const s = await getSettings();
        setUiSettings(s);
        setUiSettingsText(JSON.stringify(s, null, 2));
        setUiError(null);
      } catch (e: any) {
        setUiError(e?.message || 'Failed to fetch UI settings');
      }
    };

    init();
  }, []);

  // Stack handlers
  const refreshStackStatus = async () => {
    try {
      const status = await getClearMLStackStatus();
      setStackStatus(status);
      setStackForbidden(false);
      setStackError(null);
    } catch (e: any) {
      if (isStackControlForbidden(e)) {
        setStackForbidden(true);
        setStackError('Stack controls disabled on server.');
      } else {
        setStackError(e?.message || 'Failed to fetch stack status');
      }
    }
  };

  const onStartStack = async () => {
    setStackError(null);
    setStackForbidden(false);
    try {
      const resp = await startClearMLStack(composePath ? { compose_path: composePath } : undefined);
      setStackLastResponse(resp);
    } catch (e: any) {
      if (isStackControlForbidden(e)) {
        setStackForbidden(true);
        setStackError('Stack controls disabled on server.');
      } else {
        setStackError(e?.message || 'Failed to start ClearML stack');
      }
    } finally {
      await refreshStackStatus();
    }
  };

  const onStopStack = async () => {
    setStackError(null);
    setStackForbidden(false);
    try {
      const resp = await stopClearMLStack();
      setStackLastResponse(resp);
    } catch (e: any) {
      if (isStackControlForbidden(e)) {
        setStackForbidden(true);
        setStackError('Stack controls disabled on server.');
      } else {
        setStackError(e?.message || 'Failed to stop ClearML stack');
      }
    } finally {
      await refreshStackStatus();
    }
  };

  // Orchestrator handlers
  const refreshSnapshot = async () => {
    try {
      const snap = await getSimulationSnapshot();
      setSnapshot(snap);
      setSimError(null);
    } catch (e: any) {
      setSimError(e?.message || 'Failed to fetch simulation snapshot');
    }
  };

  const doSimAction = async (action: 'start' | 'pause' | 'resume' | 'stop') => {
    setSimError(null);
    try {
      let resp: any = null;
      if (action === 'start') resp = await startSimulation();
      if (action === 'pause') resp = await pauseSimulation();
      if (action === 'resume') resp = await resumeSimulation();
      if (action === 'stop') resp = await stopSimulation();
      setSimLastResponse(resp);
    } catch (e: any) {
      setSimError(e?.message || `Failed to ${action} simulation`);
    } finally {
      await refreshSnapshot();
    }
  };

  const onSetSpeed = async () => {
    setSimError(null);
    try {
      const resp = await setSimulationSpeed(Number(speed));
      setSimLastResponse(resp);
    } catch (e: any) {
      setSimError(e?.message || 'Failed to set simulation speed');
    } finally {
      await refreshSnapshot();
    }
  };

  // Settings handlers
  const onPatchRuntimeConfig = async () => {
    setConfigSuccess(null);
    setConfigError(null);
    try {
      const parsed = runtimeConfigText.trim() ? JSON.parse(runtimeConfigText) : {};
      const resp = await patchRuntimeConfig(parsed);
      setRuntimeConfig(resp);
      setRuntimeConfigText(JSON.stringify(resp, null, 2));
      setConfigSuccess('Runtime config updated.');
    } catch (e: any) {
      setConfigError(e?.message || 'Failed to patch runtime config (ensure valid JSON).');
    }
  };

  const onPostSettings = async () => {
    setUiSuccess(null);
    setUiError(null);
    try {
      const parsed = uiSettingsText.trim() ? JSON.parse(uiSettingsText) : {};
      const resp = await postSettings(parsed);
      setUiSettings(resp);
      setUiSettingsText(JSON.stringify(resp, null, 2));
      setUiSuccess('Settings saved.');
    } catch (e: any) {
      setUiError(e?.message || 'Failed to save settings (ensure valid JSON).');
    }
  };

  return (
    <div className="space-y-6">
      {/* ClearML Stack */}
      <Section
        title="ClearML Stack"
        subtitle="Start/Stop the ClearML Docker stack and view status"
        right={
          <div className="flex items-center space-x-2">
            <button className="btn btn-secondary btn-sm" onClick={refreshStackStatus}>
              Refresh Status
            </button>
          </div>
        }
      >
        {stackForbidden && (
          <div className="mb-3">
            <span className="badge badge-warning">Disabled by server</span>
          </div>
        )}
        {stackError && (
          <div className="mb-3">
            <Alert tone={stackForbidden ? 'warning' : 'error'}>
              {stackError} {stackForbidden ? '(ALLOW_STACK_CONTROL gating)' : null}
            </Alert>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2">
            <label className="form-label">Optional docker-compose path</label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g., ./infrastructure/compose/clearml/docker-compose.yaml"
              value={composePath}
              onChange={(e) => setComposePath(e.target.value)}
              disabled={stackForbidden}
            />
            <div className="mt-3 flex items-center space-x-2">
              <button className="btn btn-success" onClick={onStartStack} disabled={stackForbidden}>
                Start Stack
              </button>
              <button className="btn btn-danger" onClick={onStopStack} disabled={stackForbidden}>
                Stop Stack
              </button>
            </div>

            <JSONBlock data={stackLastResponse} label="Last stack response" />
          </div>

          <div className="md:col-span-1">
            <div className="border rounded p-3">
              <div className="text-sm font-medium text-gray-800 mb-2">Status</div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Web</span>
                  <span className={`status-indicator ${stackStatus?.ports?.web ? 'status-ok' : 'status-danger'}`}>
                    <span className="status-dot" />
                    {stackStatus?.ports?.web ? 'Open' : 'Closed'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">API</span>
                  <span className={`status-indicator ${stackStatus?.ports?.api ? 'status-ok' : 'status-danger'}`}>
                    <span className="status-dot" />
                    {stackStatus?.ports?.api ? 'Open' : 'Closed'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">File Server</span>
                  <span className={`status-indicator ${stackStatus?.ports?.file ? 'status-ok' : 'status-danger'}`}>
                    <span className="status-dot" />
                    {stackStatus?.ports?.file ? 'Open' : 'Closed'}
                  </span>
                </div>

                <div className="mt-3 flex items-center space-x-2">
                  <LinkButton href={stackLinks.web} label="Open Web UI" />
                  <LinkButton href={stackLinks.api} label="Open API" />
                  <LinkButton href={stackLinks.file} label="Open Files" />
                </div>
              </div>
            </div>
          </div>
        </div>

        <JSONBlock data={stackStatus} label="Status JSON" />
      </Section>

      {/* Orchestrator */}
      <Section
        title="Orchestrator"
        subtitle="Control the simulation lifecycle and speed"
        right={
          <div className="flex items-center space-x-2">
            <button className="btn btn-secondary btn-sm" onClick={refreshSnapshot}>
              Refresh Snapshot
            </button>
          </div>
        }
      >
        {simError && (
          <div className="mb-3">
            <Alert tone="error">{simError}</Alert>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2">
            <div className="flex items-center space-x-2">
              <button className="btn btn-success" onClick={() => doSimAction('start')}>
                Start
              </button>
              <button className="btn btn-warning" onClick={() => doSimAction('pause')}>
                Pause
              </button>
              <button className="btn btn-success" onClick={() => doSimAction('resume')}>
                Resume
              </button>
              <button className="btn btn-danger" onClick={() => doSimAction('stop')}>
                Stop
              </button>
            </div>

            <div className="mt-4 flex items-end space-x-3">
              <div className="flex-1">
                <label className="form-label">Speed</label>
                <input
                  type="number"
                  className="form-input"
                  min={0}
                  step={1}
                  value={Number.isFinite(speed) ? speed : 1}
                  onChange={(e) => setSpeed(Number(e.target.value))}
                />
              </div>
              <button className="btn btn-primary" onClick={onSetSpeed}>
                Set Speed
              </button>
            </div>

            <JSONBlock data={simLastResponse} label="Last orchestrator response" />
          </div>

          <div className="md:col-span-1">
            <div className="border rounded p-3">
              <div className="text-sm font-medium text-gray-800 mb-2">Current Snapshot</div>
              <div className="text-sm text-gray-700 space-y-1">
                <div>
                  <span className="text-gray-500">Status: </span>
                  <span className="font-medium">{snapshot?.status ?? '—'}</span>
                </div>
                <div>
                  <span className="text-gray-500">Day: </span>
                  <span className="font-medium">{snapshot?.day ?? '—'}</span>
                </div>
                <div>
                  <span className="text-gray-500">Tick: </span>
                  <span className="font-medium">{snapshot?.tick ?? '—'}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <JSONBlock data={snapshot} label="Snapshot JSON" />
      </Section>

      {/* Settings */}
      <Section title="Settings" subtitle="View and modify runtime configuration and UI settings">
        {/* Runtime Config */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <div className="text-sm font-medium text-gray-800">Runtime Config (/api/v1/config)</div>
            <div className="flex items-center space-x-2">
              <button
                className="btn btn-secondary btn-sm"
                onClick={async () => {
                  setConfigError(null);
                  setConfigSuccess(null);
                  try {
                    const cfg = await getRuntimeConfig();
                    setRuntimeConfig(cfg);
                    setRuntimeConfigText(JSON.stringify(cfg, null, 2));
                  } catch (e: any) {
                    setConfigError(e?.message || 'Failed to refresh runtime config');
                  }
                }}
              >
                Refresh
              </button>
              <button className="btn btn-primary btn-sm" onClick={onPatchRuntimeConfig}>
                Patch
              </button>
            </div>
          </div>
          {configError && (
            <div className="mb-2">
              <Alert tone="error">{configError}</Alert>
            </div>
          )}
          {configSuccess && (
            <div className="mb-2">
              <Alert tone="success">{configSuccess}</Alert>
            </div>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <textarea
              className="form-input font-mono text-xs h-64"
              value={runtimeConfigText}
              onChange={(e) => setRuntimeConfigText(e.target.value)}
              spellCheck={false}
            />
            <JSONBlock data={runtimeConfig} label="Current config (server)" />
          </div>
        </div>

        {/* UI Settings */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="text-sm font-medium text-gray-800">UI Settings (/api/v1/settings)</div>
            <div className="flex items-center space-x-2">
              <button
                className="btn btn-secondary btn-sm"
                onClick={async () => {
                  setUiError(null);
                  setUiSuccess(null);
                  try {
                    const s = await getSettings();
                    setUiSettings(s);
                    setUiSettingsText(JSON.stringify(s, null, 2));
                  } catch (e: any) {
                    setUiError(e?.message || 'Failed to refresh UI settings');
                  }
                }}
              >
                Refresh
              </button>
              <button className="btn btn-primary btn-sm" onClick={onPostSettings}>
                Save
              </button>
            </div>
          </div>
          {uiError && (
            <div className="mb-2">
              <Alert tone="error">{uiError}</Alert>
            </div>
          )}
          {uiSuccess && (
            <div className="mb-2">
              <Alert tone="success">{uiSuccess}</Alert>
            </div>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <textarea
              className="form-input font-mono text-xs h-64"
              value={uiSettingsText}
              onChange={(e) => setUiSettingsText(e.target.value)}
              spellCheck={false}
            />
            <JSONBlock data={uiSettings} label="Current settings (server)" />
          </div>
        </div>
      </Section>
    </div>
  );
};

export default ControlCenter;
