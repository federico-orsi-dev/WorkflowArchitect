"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CheckCircle2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

const MIN_TEXT_LENGTH = 5;

const PLAN_HISTORY_KEY = "workflowarchitect.plan.history";
const PLAN_ACTIVE_KEY = "workflowarchitect.plan.active";
const COMMIT_HISTORY_KEY = "workflowarchitect.commit.history";
const PR_SESSION_KEY = "workflowarchitect.pr.session";

type Risk = "low" | "med" | "high";

type PlanTask = {
  id: string;
  title: string;
  details: string;
  estimate_minutes: number;
  risk: Risk;
  definition_of_done: string[];
  completed?: boolean;
};

type PlanResult = {
  tasks: PlanTask[];
  total_estimate_minutes: number;
  notes: string;
};

type CommitResult = {
  commit_message: string;
  labels: string[];
};

type PullRequestResult = {
  pr_title: string;
  pr_body_markdown: string;
  changelog_entry: string;
  labels: string[];
};

type PlanRun = {
  id: string;
  createdAt: string;
  goal: string;
  context: string;
  constraints: string;
  techStack: string;
  input: string;
  result: PlanResult;
};

type CommitRun = {
  id: string;
  createdAt: string;
  input: string;
  result: CommitResult;
  plan_id?: string | null;
  task_id?: string | null;
};

type PrSession = {
  commits: CommitRun[];
};

const changeTypes = ["feat", "fix", "refactor", "chore", "docs", "test"] as const;

type ChangeType = (typeof changeTypes)[number];

type TabValue = "plan" | "commit";

type TaskSelection = {
  planId: string;
  taskId: string;
};

function loadHistory<T>(key: string): T[] {
  if (typeof window === "undefined") return [];
  const raw = window.localStorage.getItem(key);
  if (!raw) return [];
  try {
    return JSON.parse(raw) as T[];
  } catch {
    return [];
  }
}

function saveHistory<T>(key: string, entries: T[]) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(key, JSON.stringify(entries.slice(0, 10)));
}

function loadActivePlan(): PlanRun | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(PLAN_ACTIVE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as PlanRun;
  } catch {
    return null;
  }
}

function loadPrSession(): PrSession {
  if (typeof window === "undefined") return { commits: [] };
  const raw = window.localStorage.getItem(PR_SESSION_KEY);
  if (!raw) return { commits: [] };
  try {
    const parsed = JSON.parse(raw) as PrSession;
    if (!parsed?.commits || !Array.isArray(parsed.commits)) {
      return { commits: [] };
    }
    return { commits: parsed.commits };
  } catch {
    return { commits: [] };
  }
}

function savePrSession(session: PrSession) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(PR_SESSION_KEY, JSON.stringify(session));
}

function saveActivePlan(plan: PlanRun | null) {
  if (typeof window === "undefined") return;
  if (!plan) {
    window.localStorage.removeItem(PLAN_ACTIVE_KEY);
    return;
  }
  window.localStorage.setItem(PLAN_ACTIVE_KEY, JSON.stringify(plan));
}

function copyToClipboard(label: string, value: string) {
  navigator.clipboard
    .writeText(value)
    .then(() => toast.success(`${label} copied`))
    .catch(() => toast.error(`Failed to copy ${label.toLowerCase()}`));
}

export default function HomePage() {
  const [tab, setTab] = useState<TabValue>("plan");

  const [goal, setGoal] = useState("");
  const [context, setContext] = useState("");
  const [constraints, setConstraints] = useState("");
  const [techStack, setTechStack] = useState("");

  const [changeType, setChangeType] = useState<ChangeType | undefined>(undefined);
  const [scope, setScope] = useState("");
  const [what, setWhat] = useState("");
  const [why, setWhy] = useState("");
  const [breakingChange, setBreakingChange] = useState(false);

  const [planHistory, setPlanHistory] = useState<PlanRun[]>([]);
  const [commitHistory, setCommitHistory] = useState<CommitRun[]>([]);
  const [activePlanId, setActivePlanId] = useState<string | null>(null);
  const [selectedTask, setSelectedTask] = useState<TaskSelection | null>(null);

  const [commitResult, setCommitResult] = useState<CommitResult | null>(null);
  const [showPrMarkdownPreview, setShowPrMarkdownPreview] = useState(false);

  const [isLoading, setIsLoading] = useState(false);
  const [isPrLoading, setIsPrLoading] = useState(false);

  const [prSession, setPrSession] = useState<PrSession>({ commits: [] });
  const [prResult, setPrResult] = useState<PullRequestResult | null>(null);

  const commitResultsRef = useRef<HTMLDivElement | null>(null);

  const activePlan = useMemo(
    () => planHistory.find((plan) => plan.id === activePlanId) ?? null,
    [planHistory, activePlanId],
  );

  const restorePlanInputs = useCallback((plan: PlanRun) => {
    setGoal(plan.goal ?? "");
    setContext(plan.context ?? "");
    setConstraints(plan.constraints ?? "");
    setTechStack(plan.techStack ?? "");
  }, []);

  useEffect(() => {
    const storedPlans = loadHistory<PlanRun>(PLAN_HISTORY_KEY);
    const storedCommits = loadHistory<CommitRun>(COMMIT_HISTORY_KEY);
    const storedActive = loadActivePlan();
    const storedPrSession = loadPrSession();

    let mergedPlans = storedPlans;
    if (storedActive && !storedPlans.some((plan) => plan.id === storedActive.id)) {
      mergedPlans = [storedActive, ...storedPlans].slice(0, 10);
    }

    setPlanHistory(mergedPlans);
    setCommitHistory(storedCommits);
    setPrSession(storedPrSession);

    if (storedActive) {
      setActivePlanId(storedActive.id);
      restorePlanInputs(storedActive);
    }
  }, [restorePlanInputs]);

  useEffect(() => {
    if (commitResult && tab === "commit") {
      commitResultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [commitResult, tab]);

  const prompt = useMemo(() => {
    const fields = [
      `Goal: ${goal}`,
      context ? `Context: ${context}` : null,
      constraints ? `Constraints: ${constraints}` : null,
      techStack ? `Tech stack: ${techStack}` : null,
    ].filter(Boolean);
    return fields.join("\n");
  }, [goal, context, constraints, techStack]);

  const commitSummary = useMemo(() => {
    if (!changeType) {
      return "";
    }
    const scopeText = scope ? `(${scope})` : "";
    const breaking = breakingChange ? "Breaking change: yes" : "Breaking change: no";
    return [
      `Type: ${changeType}${scopeText}`,
      `What: ${what}`,
      `Why: ${why}`,
      breaking,
    ].join("\n");
  }, [changeType, scope, what, why, breakingChange]);

  const updatePlanHistory = (nextHistory: PlanRun[], activeOverride?: PlanRun | null) => {
    setPlanHistory(nextHistory);
    saveHistory(PLAN_HISTORY_KEY, nextHistory);
    if (activeOverride) {
      saveActivePlan(activeOverride);
      return;
    }
    if (activePlanId) {
      const active = nextHistory.find((plan) => plan.id === activePlanId);
      if (active) {
        saveActivePlan(active);
      }
    }
  };

  const updatePrSession = (nextSession: PrSession) => {
    setPrSession(nextSession);
    savePrSession(nextSession);
  };

  const markTaskCompleted = (planId: string, taskId: string) => {
    setPlanHistory((prev) => {
      const updated = prev.map((plan) => {
        if (plan.id !== planId) return plan;
        const updatedTasks = plan.result.tasks.map((task) =>
          task.id === taskId ? { ...task, completed: true } : task,
        );
        return { ...plan, result: { ...plan.result, tasks: updatedTasks } };
      });
      saveHistory(PLAN_HISTORY_KEY, updated);
      const active = updated.find((plan) => plan.id === activePlanId);
      if (active) {
        saveActivePlan(active);
      }
      return updated;
    });
  };

  const handleSelectPlan = (plan: PlanRun) => {
    setActivePlanId(plan.id);
    saveActivePlan(plan);
    restorePlanInputs(plan);
    setSelectedTask(null);
  };

  const handleGeneratePlan = async () => {
    if (goal.trim().length < MIN_TEXT_LENGTH) {
      toast.error(`Goal must be at least ${MIN_TEXT_LENGTH} characters.`);
      return;
    }
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/plan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt }),
      });
      if (!response.ok) {
        throw new Error(`Plan failed (${response.status})`);
      }
      const data = (await response.json()) as { result: PlanResult };
      const run: PlanRun = {
        id: crypto.randomUUID(),
        createdAt: new Date().toISOString(),
        goal,
        context,
        constraints,
        techStack,
        input: prompt,
        result: data.result,
      };
      const updated = [run, ...planHistory].slice(0, 10);
      updatePlanHistory(updated, run);
      setActivePlanId(run.id);
      setSelectedTask(null);
      toast.success("Plan generated.");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Plan failed.";
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUseForCommit = (task: PlanTask) => {
    if (!activePlanId) {
      toast.error("Select a plan first.");
      return;
    }
    setSelectedTask({ planId: activePlanId, taskId: task.id });
    setTab("commit");
    setWhat(`${task.title}. ${task.details}`);
    const done = task.definition_of_done.join("; ");
    setWhy(`Risk: ${task.risk}. Definition of done: ${done}`);
    setCommitResult(null);
    toast.message("Task copied into Commit form.");
  };

  const handleGenerateCommit = async () => {
    if (!changeType) {
      toast.error("Select a change type.");
      return;
    }
    if (what.trim().length < MIN_TEXT_LENGTH) {
      toast.error(`What must be at least ${MIN_TEXT_LENGTH} characters.`);
      return;
    }
    if (why.trim().length < MIN_TEXT_LENGTH) {
      toast.error(`Why must be at least ${MIN_TEXT_LENGTH} characters.`);
      return;
    }
    setIsLoading(true);
    try {
      const payload: { message: string; plan_id?: string; task_id?: string } = {
        message: commitSummary,
      };
      if (selectedTask) {
        payload.plan_id = selectedTask.planId;
        payload.task_id = selectedTask.taskId;
      }
      const response = await fetch(`${API_BASE}/api/commit`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        throw new Error(`Commit failed (${response.status})`);
      }
      const data = (await response.json()) as { result: CommitResult };
      setCommitResult(data.result);
      const run: CommitRun = {
        id: crypto.randomUUID(),
        createdAt: new Date().toISOString(),
        input: commitSummary,
        result: data.result,
        plan_id: selectedTask?.planId ?? null,
        task_id: selectedTask?.taskId ?? null,
      };
      const updated = [run, ...commitHistory].slice(0, 10);
      setCommitHistory(updated);
      saveHistory(COMMIT_HISTORY_KEY, updated);
      const planId = selectedTask?.planId;
      const taskId = selectedTask?.taskId;
      if (planId && taskId) {
        markTaskCompleted(planId, taskId);
      }
      setSelectedTask(null);
      toast.success("Commit assets generated.");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Commit failed.";
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const applyPlanExample = () => {
    setGoal("Improve API reliability for daily peak usage.");
    setContext("SLO misses for /api/commit under load.");
    setConstraints("Must ship in 1 week, no new services.");
    setTechStack("FastAPI, Redis, Next.js");
  };

  const applyCommitExample = () => {
    setChangeType("refactor");
    setScope("api");
    setWhat("Refactor commit pipeline to reuse shared validation and reduce retries.");
    setWhy("Improve maintainability and reduce latency spikes during peak loads.");
    setBreakingChange(false);
    setSelectedTask(null);
  };

  const addCommitToPrSession = (run: CommitRun) => {
    if (prSession.commits.some((entry) => entry.id === run.id)) {
      toast.message("Commit already added to PR.");
      return;
    }
    const updated = { commits: [run, ...prSession.commits] };
    updatePrSession(updated);
    setPrResult(null);
    toast.success("Commit added to PR session.");
  };

  const removeCommitFromPrSession = (commitId: string) => {
    const updated = {
      commits: prSession.commits.filter((run) => run.id !== commitId),
    };
    updatePrSession(updated);
    setPrResult(null);
  };

  const handleGeneratePr = async () => {
    if (prSession.commits.length === 0) {
      toast.error("Add at least one commit to the PR session.");
      return;
    }
    setIsPrLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/pr`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          commits: prSession.commits.map((run) => run.result),
        }),
      });
      if (!response.ok) {
        throw new Error(`PR aggregation failed (${response.status})`);
      }
      const data = (await response.json()) as { result: PullRequestResult };
      setPrResult(data.result);
      toast.success("PR description generated.");
    } catch (error) {
      const message = error instanceof Error ? error.message : "PR aggregation failed.";
      toast.error(message);
    } finally {
      setIsPrLoading(false);
    }
  };

  const loadCommitIntoForm = (run: CommitRun) => {
    const parsed = parseCommitInput(run.input);
    setChangeType(parsed.changeType);
    setScope(parsed.scope ?? "");
    setWhat(parsed.what ?? "");
    setWhy(parsed.why ?? "");
    setBreakingChange(parsed.breakingChange ?? false);
    setCommitResult(run.result);
    setSelectedTask(null);
  };

  const getCommitOriginLabel = (run: CommitRun) => {
    const planId = run.plan_id;
    if (!planId) return null;
    const plan = planHistory.find((entry) => entry.id === planId);
    const task = plan?.result.tasks.find((entry) => entry.id === run.task_id);
    if (task?.title) {
      return `Generated from: ${task.title}`;
    }
    if (plan?.goal) {
      return `Generated from plan: ${plan.goal}`;
    }
    return `Generated from plan ${planId}`;
  };

  return (
    <main className="min-h-screen bg-background">
      <div className="container py-10">
        <div className="mb-8 flex items-center justify-between">
          <h1 className="text-2xl font-semibold">WorkflowArchitect</h1>
        </div>

        <Tabs value={tab} onValueChange={(value) => setTab(value as TabValue)}>
          <TabsList>
            <TabsTrigger value="plan">Plan</TabsTrigger>
            <TabsTrigger value="commit">Commit</TabsTrigger>
          </TabsList>

          <TabsContent value="plan">
            <div className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
              <Card>
                <CardHeader>
                  <CardTitle>Plan inputs</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Goal</label>
                    <Textarea
                      placeholder="Ship a reliability improvement for the API."
                      value={goal}
                      onChange={(event) => setGoal(event.target.value)}
                    />
                  </div>
                  <div className="grid gap-4 md:grid-cols-3">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Context</label>
                      <Input
                        placeholder="What matters"
                        value={context}
                        onChange={(event) => setContext(event.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Constraints</label>
                      <Input
                        placeholder="Time, scope, dependencies"
                        value={constraints}
                        onChange={(event) => setConstraints(event.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Tech stack</label>
                      <Input
                        placeholder="FastAPI, Next.js"
                        value={techStack}
                        onChange={(event) => setTechStack(event.target.value)}
                      />
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-3">
                    <Button onClick={handleGeneratePlan} disabled={isLoading}>
                      {isLoading ? "Generating..." : "Generate plan"}
                    </Button>
                    <Button variant="outline" onClick={applyPlanExample} disabled={isLoading}>
                      Use example
                    </Button>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Recent plans</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm text-muted-foreground">
                  {planHistory.length === 0 && <p>No plan history yet.</p>}
                  {planHistory.map((run) => {
                    const isActive = run.id === activePlanId;
                    return (
                      <button
                        key={run.id}
                        type="button"
                        onClick={() => handleSelectPlan(run)}
                        disabled={isLoading}
                        className={`w-full rounded-md border p-3 text-left transition disabled:cursor-not-allowed disabled:opacity-60 ${
                          isActive ? "border-primary bg-muted/40" : "border-border"
                        }`}
                      >
                        <div className="font-medium text-foreground">{run.result.notes}</div>
                        <div className="text-xs">{new Date(run.createdAt).toLocaleString()}</div>
                      </button>
                    );
                  })}
                </CardContent>
              </Card>
            </div>

            <div className="mt-6 space-y-4">
              {!activePlan && (
                <Card>
                  <CardContent className="p-6 text-sm text-muted-foreground">
                    No plan generated yet. Add a goal and generate a plan to see tasks here.
                  </CardContent>
                </Card>
              )}
              {activePlan?.result.tasks.map((task) => (
                <Card key={task.id} className={task.completed ? "border-dashed border-primary/40" : ""}>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <span className={task.completed ? "text-muted-foreground" : ""}>
                        {task.title}
                      </span>
                      <span className="text-sm font-normal text-muted-foreground">
                        {task.estimate_minutes} min - {task.risk}
                      </span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className={`space-y-3 ${task.completed ? "text-muted-foreground" : ""}`}>
                    <p className="text-sm text-muted-foreground">{task.details}</p>
                    <div className="text-sm">
                      <div className="font-medium">Definition of done</div>
                      <ul className="list-disc pl-5 text-muted-foreground">
                        {task.definition_of_done.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="flex items-center justify-between">
                      <Button
                        variant="outline"
                        onClick={() => handleUseForCommit(task)}
                        disabled={isLoading}
                      >
                        Use for commit
                      </Button>
                      {task.completed && (
                        <span className="flex items-center gap-1 text-xs text-muted-foreground">
                          <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                          Completed
                        </span>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="commit">
            <div className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
              <Card>
                <CardHeader>
                  <CardTitle>Commit inputs</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Change type</label>
                      <Select
                        key={changeType || "uncontrolled"}
                        {...(changeType ? { value: changeType } : {})}
                        onValueChange={(value) => setChangeType(value as ChangeType)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select change type" />
                        </SelectTrigger>
                        <SelectContent>
                          {changeTypes.map((type) => (
                            <SelectItem key={type} value={type}>
                              {type}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Scope (optional)</label>
                      <Input
                        placeholder="api"
                        value={scope}
                        onChange={(event) => setScope(event.target.value)}
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">What</label>
                    <Textarea value={what} onChange={(event) => setWhat(event.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Why</label>
                    <Textarea value={why} onChange={(event) => setWhy(event.target.value)} />
                  </div>
                  <div className="flex items-center gap-3">
                    <Switch checked={breakingChange} onCheckedChange={setBreakingChange} />
                    <span className="text-sm">Breaking change</span>
                  </div>
                  <div className="flex flex-wrap gap-3">
                    <Button onClick={handleGenerateCommit} disabled={isLoading}>
                      {isLoading ? "Generating..." : "Generate commit assets"}
                    </Button>
                    <Button variant="outline" onClick={applyCommitExample} disabled={isLoading}>
                      Use example
                    </Button>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Recent commits</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm text-muted-foreground">
                  {commitHistory.length === 0 && <p>No commit history yet.</p>}
                  {commitHistory.map((run) => (
                    <div
                      key={run.id}
                      role="button"
                      tabIndex={0}
                      onClick={() => loadCommitIntoForm(run)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault();
                          loadCommitIntoForm(run);
                        }
                      }}
                      className="flex cursor-pointer flex-wrap items-start justify-between gap-3 rounded-md border border-border p-3 transition hover:border-primary/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
                    >
                      <div>
                        <div className="font-medium text-foreground">{run.result.commit_message}</div>
                        {getCommitOriginLabel(run) && (
                          <div className="text-xs">{getCommitOriginLabel(run)}</div>
                        )}
                        <div className="text-xs">{new Date(run.createdAt).toLocaleString()}</div>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(event) => {
                          event.stopPropagation();
                          addCommitToPrSession(run);
                        }}
                      >
                        Add to PR
                      </Button>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>

            {!commitResult && (
              <Card className="mt-6">
                <CardContent className="p-6 text-sm text-muted-foreground">
                  No commit assets yet. Generate a commit to see the outputs.
                </CardContent>
              </Card>
            )}

            {commitResult && (
              <div ref={commitResultsRef} className="mt-6 grid gap-4 lg:grid-cols-2">
                <Card className="border-primary/40 bg-muted/40">
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      Commit message
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard("Commit message", commitResult.commit_message)}
                      >
                        Copy
                      </Button>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="text-sm text-muted-foreground">
                    {commitResult.commit_message}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Labels</CardTitle>
                  </CardHeader>
                  <CardContent className="flex flex-wrap gap-2 text-sm text-muted-foreground">
                    {commitResult.labels.length === 0 && <span>No labels suggested.</span>}
                    {commitResult.labels.map((label) => (
                      <span key={label} className="rounded-full border border-border px-2 py-1">
                        {label}
                      </span>
                    ))}
                  </CardContent>
                </Card>
              </div>
            )}

            <Card className="mt-6">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  PR Builder
                  <span className="text-sm font-normal text-muted-foreground">
                    {prSession.commits.length} commits
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {prSession.commits.length === 0 && (
                  <p className="text-sm text-muted-foreground">
                    No commits in the PR session yet. Add commit outputs to build your PR.
                  </p>
                )}
                {prSession.commits.length > 0 && (
                  <div className="space-y-3">
                    {prSession.commits.map((run) => (
                      <div
                        key={run.id}
                        className="flex flex-wrap items-start justify-between gap-3 rounded-md border border-border p-3"
                      >
                        <div>
                          <div className="font-medium text-foreground">
                            {run.result.commit_message}
                          </div>
                          {getCommitOriginLabel(run) && (
                            <div className="text-xs text-muted-foreground">
                              {getCommitOriginLabel(run)}
                            </div>
                          )}
                          <div className="text-xs text-muted-foreground">
                            {new Date(run.createdAt).toLocaleString()}
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeCommitFromPrSession(run.id)}
                        >
                          Remove
                        </Button>
                      </div>
                    ))}
                  </div>
                )}

                <div className="flex flex-wrap gap-3">
                    <Button
                      onClick={handleGeneratePr}
                      disabled={prSession.commits.length === 0 || isPrLoading}
                    >
                      {isPrLoading ? "Generating..." : "Generate PR Description"}
                    </Button>
                </div>

                {!prResult && (
                  <div className="text-sm text-muted-foreground">
                    Generate a unified PR title and body once you have your commits.
                  </div>
                )}

                {prResult && (
                  <div className="grid gap-4 lg:grid-cols-2">
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center justify-between">
                          PR title
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => copyToClipboard("PR title", prResult.pr_title)}
                          >
                            Copy
                          </Button>
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="text-sm text-muted-foreground">
                        {prResult.pr_title}
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center justify-between">
                          Changelog entry
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              copyToClipboard("Changelog entry", prResult.changelog_entry)
                            }
                          >
                            Copy
                          </Button>
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="text-sm text-muted-foreground">
                        {prResult.changelog_entry}
                      </CardContent>
                    </Card>

                    <Card className="lg:col-span-2">
                      <CardHeader>
                        <CardTitle className="flex flex-wrap items-center justify-between gap-3">
                          PR body markdown
                          <div className="flex items-center gap-2">
                            <Button
                              variant={showPrMarkdownPreview ? "outline" : "ghost"}
                              size="sm"
                              onClick={() => setShowPrMarkdownPreview(false)}
                            >
                              Raw
                            </Button>
                            <Button
                              variant={showPrMarkdownPreview ? "ghost" : "outline"}
                              size="sm"
                              onClick={() => setShowPrMarkdownPreview(true)}
                            >
                              Preview
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => copyToClipboard("PR body", prResult.pr_body_markdown)}
                            >
                              Copy
                            </Button>
                          </div>
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="text-sm text-muted-foreground">
                        {showPrMarkdownPreview ? (
                          <div className="space-y-3">
                            <ReactMarkdown>{prResult.pr_body_markdown}</ReactMarkdown>
                          </div>
                        ) : (
                          <div className="whitespace-pre-wrap">{prResult.pr_body_markdown}</div>
                        )}
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle>Labels</CardTitle>
                      </CardHeader>
                      <CardContent className="flex flex-wrap gap-2 text-sm text-muted-foreground">
                        {prResult.labels.length === 0 && <span>No labels suggested.</span>}
                        {prResult.labels.map((label) => (
                          <span key={label} className="rounded-full border border-border px-2 py-1">
                            {label}
                          </span>
                        ))}
                      </CardContent>
                    </Card>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </main>
  );
}

function parseCommitInput(input: string): {
  changeType?: ChangeType;
  scope?: string;
  what?: string;
  why?: string;
  breakingChange?: boolean;
} {
  const lines = input.split("\n");
  const typeLine = lines.find((line) => line.startsWith("Type:"));
  const whatLine = lines.find((line) => line.startsWith("What:"));
  const whyLine = lines.find((line) => line.startsWith("Why:"));
  const breakingLine = lines.find((line) => line.startsWith("Breaking change:"));

  let changeType: ChangeType | undefined;
  let scope: string | undefined;

  if (typeLine) {
    const match = typeLine.match(/^Type:\s*([a-z]+)(?:\(([^)]+)\))?/i);
    const type = match?.[1]?.toLowerCase();
    if (type && changeTypes.includes(type as ChangeType)) {
      changeType = type as ChangeType;
    }
    if (match?.[2]) {
      scope = match[2];
    }
  }

  const breaking = breakingLine?.toLowerCase().includes("yes") ?? false;

  return {
    changeType,
    scope,
    what: whatLine ? whatLine.replace(/^What:\s*/, "") : "",
    why: whyLine ? whyLine.replace(/^Why:\s*/, "") : "",
    breakingChange: breaking,
  };
}
