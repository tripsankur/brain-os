#!/usr/bin/env python3
"""Brain OS engine: automatic capture + generated views for the Obsidian vault.

Layers (see Claude/workflow.md in the vault):
  events   Claude/_system/events.jsonl   append-only truth: one line per session part / job event
  views    Claude/journal/YYYY-MM-DD.md  daily journal (rendered from events)
           Projects/{p}/{p}-activity.md  per-project activity (rendered from events)
           Projects/{p}/{p}-auto-status.md  mirror of a job's own status file
           Claude/projects-index.md      AUTO block (phase / state / last activity)
           Claude/health.md              drift, stale jobs, failed tasks, backup state
  curated  {p}-status / -session-log / -decisions   written by /brain end, never by this script

Commands:
  session-start          SessionStart hook: prints project context (stdin = hook JSON)
  session-end            SessionEnd hook: journals the session (stdin = hook JSON)
  log -p PROJECT MSG     write-back for scheduled jobs / scripts (--source NAME)
  sweep                  journal every transcript not yet (fully) journaled
  sync [--no-git]        sweep + mirrors + views + health + git commit/pull --rebase/push
  health                 print health report
  resolve [CWD]          print the vault project for a directory

Hooks must never block Claude: every hook path swallows errors and exits 0.
"""
import argparse
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys
import traceback

VAULT = os.environ.get("BRAIN_VAULT", "{{VAULT_PATH}}")
CLAUDE_HOME = os.environ.get("BRAIN_CLAUDE_HOME", "{{CLAUDE_PATH}}")
SYS_DIR = os.path.join(VAULT, "Claude", "_system")
EVENTS = os.path.join(SYS_DIR, "events.jsonl")
REGISTRY = os.path.join(VAULT, "Claude", "registry.md")
LOGFILE = os.path.join(CLAUDE_HOME, "brain-engine.log")
AUTO_BEGIN, AUTO_END = "<!-- AUTO:BEGIN -->", "<!-- AUTO:END -->"
MAX_PROMPTS, PROMPT_CHARS, MAX_FILES = 8, 220, 25
STATES = ["live", "active", "paused", "concluded", "archived"]

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------- utilities

def now_local():
    return dt.datetime.now().astimezone()


def to_local(ts):
    try:
        return dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
    except Exception:
        return None


def rel(path, base):
    try:
        return os.path.relpath(path, base).replace("\\", "/")
    except ValueError:
        return path.replace("\\", "/")


def norm(p):
    return os.path.normcase(os.path.normpath(p.replace("/", os.sep))) if p else ""


def key(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def read(path, default=""):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return default


def write_if_changed(path, text):
    if read(path, None) == text:
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return True


def log(msg):
    try:
        with open(LOGFILE, "a", encoding="utf-8") as f:
            f.write(f"{now_local():%Y-%m-%d %H:%M:%S} {msg}\n")
    except OSError:
        pass


SECRET_PATTERNS = [
    re.compile(r"\b(sk-[A-Za-z0-9_\-]{16,}|sk-ant-[A-Za-z0-9_\-]{16,})"),
    re.compile(r"\b(ghp|gho|ghu|ghs|github_pat)_[A-Za-z0-9_]{16,}"),
    re.compile(r"\b(xox[abpr]-[A-Za-z0-9\-]{10,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_\-]{30,}|dapi[0-9a-f]{20,})"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]{16,}"),
    re.compile(r"(?i)\b(api[_-]?key|token|secret|password|passwd|pwd)\b\s*[:=]\s*[\"']?[^\s\"']{6,}"),
    re.compile(r"\b[0-9a-fA-F]{32,}\b"),
    re.compile(r"(?=[A-Za-z0-9+/_\-]*\d)(?=[A-Za-z0-9+/_\-]*[A-Z])(?=[A-Za-z0-9+/_\-]*[a-z])\b[A-Za-z0-9+/_\-]{40,}={0,2}"),
]


def redact(text):
    for pat in SECRET_PATTERNS:
        text = pat.sub("[REDACTED]", text)
    return text


def one_line(text, limit=PROMPT_CHARS):
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


# ---------------------------------------------------------------- registry

def load_registry():
    """Parse Claude/registry.md table -> list of dicts. Hand-edited; the join key repo<->vault."""
    rows, header = [], None
    for line in read(REGISTRY).splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip().strip("`").strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            header = [c.lower() for c in cells]
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        row = dict(zip(header, cells))
        row["repos"] = [r.strip().strip("`") for r in row.get("repo", "").split(";") if r.strip() and r.strip() != "-"]
        row["watch"] = [w.strip().strip("`") for w in row.get("watch", "").split(";") if w.strip() and w.strip() != "-"]
        row["tasks"] = [t.strip() for t in row.get("tasks", "").split(";") if t.strip() and t.strip() != "-"]
        rows.append(row)
    return rows


def vault_projects():
    base = os.path.join(VAULT, "Projects")
    return sorted(d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d)) and not d.startswith((".", "_")))


def resolve_project(cwd, registry=None):
    """cwd -> vault project name, or None. Order: registry repo prefix, vault path, basename match, CLAUDE.local.md pointer."""
    if not cwd:
        return None
    registry = registry if registry is not None else load_registry()
    ncwd = norm(cwd)
    nproj = norm(os.path.join(VAULT, "Projects"))
    if ncwd.startswith(nproj + os.sep):
        return os.path.relpath(ncwd, nproj).split(os.sep)[0]
    best, best_len = None, -1
    for row in registry:
        for repo in row["repos"]:
            nr = norm(repo)
            if (ncwd == nr or ncwd.startswith(nr + os.sep)) and len(nr) > best_len:
                best, best_len = row.get("project"), len(nr)
    if best:
        return best
    projects = vault_projects()
    by_key = {key(p): p for p in projects}
    part = cwd
    for _ in range(4):
        hit = by_key.get(key(os.path.basename(part.rstrip("/\\"))))
        if hit:
            return hit
        m = re.search(r"Projects/([^/`\s]+)/", read(os.path.join(part, "CLAUDE.local.md")))
        if m and m.group(1) in projects:
            return m.group(1)
        parent = os.path.dirname(part.rstrip("/\\"))
        if parent == part:
            break
        part = parent
    return None


# ---------------------------------------------------------------- transcripts

def human_prompts_and_work(path):
    """Parse a Claude Code transcript -> summary dict. Tool outputs are never read."""
    s = {"prompts": [], "files": [], "commits": [], "title": "", "cwd": "", "entry": "",
         "start": None, "end": None, "session_id": os.path.splitext(os.path.basename(path))[0]}
    seen_files = set()
    s["touched"] = []
    try:
        fh = open(path, encoding="utf-8", errors="replace")
    except OSError:
        return None
    with fh:
        for line in fh:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            t = d.get("type")
            if t == "ai-title" and d.get("aiTitle"):
                s["title"] = d["aiTitle"]
            ts = d.get("timestamp")
            if ts and t in ("user", "assistant"):
                s["start"] = s["start"] or ts
                s["end"] = ts
            if t == "user":
                s["cwd"] = s["cwd"] or d.get("cwd", "")
                s["entry"] = s["entry"] or d.get("entrypoint", "")
                if d.get("isMeta") or d.get("toolUseResult") is not None or d.get("isSidechain"):
                    continue
                c = d.get("message", {}).get("content")
                if isinstance(c, list):
                    if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in c):
                        continue
                    c = " ".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
                if not isinstance(c, str) or not c.strip():
                    continue
                cmd = re.search(r"<command-name>([^<]+)</command-name>", c)
                if cmd:
                    args = re.search(r"<command-args>([^<]*)</command-args>", c)
                    c = cmd.group(1).strip() + (" " + args.group(1).strip() if args and args.group(1).strip() else "")
                elif c.lstrip().startswith(("<local-command", "<system-reminder", "<task-notification", "Caveat:", "[Request interrupted")):
                    continue
                s["prompts"].append(c)
            elif t == "assistant" and not d.get("isSidechain"):
                for b in d.get("message", {}).get("content", []) or []:
                    if not isinstance(b, dict) or b.get("type") != "tool_use":
                        continue
                    inp = b.get("input") or {}
                    if b.get("name") in ("Write", "Edit", "NotebookEdit", "MultiEdit"):
                        fp = inp.get("file_path") or inp.get("notebook_path")
                        if fp and fp not in seen_files:
                            seen_files.add(fp)
                            s["files"].append(fp)
                    elif b.get("name") in ("Read", "Grep", "Glob"):
                        tp = inp.get("file_path") or inp.get("path")
                        if tp:
                            s["touched"].append(tp)
                    if b.get("name") in ("Bash", "PowerShell"):
                        s["touched"].append(inp.get("command", ""))
                        for m in re.finditer(r"git\b[^\n]*?\bcommit\b[^\n]*?-(?:q)?m\s+(\"[^\"]+\"|'[^']+')", inp.get("command", "")):
                            s["commits"].append(m.group(1).strip("\"'"))
    return s


def load_events():
    out, seen = [], set()
    for line in read(EVENTS).splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        k = (e.get("session_id"), e.get("part")) if e.get("kind") == "session" else None
        if k and k in seen:  # a hook and a sweep raced on the same part
            continue
        if k:
            seen.add(k)
        out.append(e)
    return out


def append_events(evs):
    if not evs:
        return
    os.makedirs(SYS_DIR, exist_ok=True)
    with open(EVENTS, "a", encoding="utf-8", newline="\n") as f:
        for e in evs:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


def session_progress(events):
    """session_id -> (parts, prompts_logged, files_logged set, commits_logged)."""
    prog = {}
    for e in events:
        if e.get("kind") != "session":
            continue
        p = prog.setdefault(e["session_id"], [0, 0, set(), 0])
        p[0] += 1
        p[1] += e.get("n_prompts", 0)
        p[2].update(e.get("files_all", []))
        p[3] += len(e.get("commits", []))
    return prog


def journal_transcript(path, events=None, registry=None, reason=""):
    """Create the next session-part event for a transcript, or None if nothing new."""
    s = human_prompts_and_work(path)
    if not s or not s["start"]:
        return None
    events = events if events is not None else load_events()
    parts, done_prompts, done_files, done_commits = session_progress(events).get(s["session_id"], [0, 0, set(), 0])
    new_prompts = s["prompts"][done_prompts:]
    new_files = [f for f in s["files"] if f not in done_files]
    new_commits = s["commits"][done_commits:]
    if not new_prompts and not new_files and not new_commits:
        return None
    registry = registry if registry is not None else load_registry()
    private = any(touches_personal(p) for p in s["files"] + s["touched"] + [s["cwd"]])
    end = to_local(s["end"]) or now_local()
    home = os.path.expanduser("~")
    return {
        "kind": "session", "session_id": s["session_id"], "part": parts + 1,
        "date": end.strftime("%Y-%m-%d"), "start": (to_local(s["start"]) or end).isoformat(timespec="minutes"),
        "end": end.isoformat(timespec="minutes"), "project": resolve_project(s["cwd"], registry),
        "cwd": rel(s["cwd"], home) if s["cwd"] else "", "entry": s["entry"] or "cli", "reason": reason,
        "title": one_line(redact(s["title"]), 90),
        "n_prompts": len(new_prompts),
        "prompts": [] if private else [one_line(redact(p)) for p in new_prompts[:MAX_PROMPTS]],
        "files": [rel(f, home) for f in new_files[:MAX_FILES]], "n_files": len(new_files),
        "files_all": new_files, "commits": [one_line(redact(c), 120) for c in new_commits],
        "private": private,
    }


def touches_personal(text):
    t = text.replace("\\", "/").lower()
    return "/personal/" in t + "/" and VAULT.replace("\\", "/").lower().rstrip("/").split("/")[-1] in t


def all_transcripts():
    return sorted(glob.glob(os.path.join(CLAUDE_HOME, "projects", "*", "*.jsonl")), key=os.path.getmtime)


def sweep(quiet=False):
    events, registry = load_events(), load_registry()
    new = []
    for path in all_transcripts():
        e = journal_transcript(path, events + new, registry, reason="sweep")
        if e:
            new.append(e)
    append_events(new)
    if not quiet:
        print(f"sweep: {len(new)} session part(s) journaled")
    return new


# ---------------------------------------------------------------- views

def plink(project):
    return f"[[Projects/{project}/{project}|{project}]]" if project else "unassigned"


def render_event(e, with_project=True):
    t = e.get("end", "")[11:16]
    head = f"### {t}"
    if with_project:
        head += f" · {plink(e.get('project'))}"
    if e["kind"] == "session":
        head += f" · {e.get('title') or 'session'}" + (f" (part {e['part']})" if e.get("part", 1) > 1 else "")
        lines = [head, f"- `{e['session_id'][:8]}` · {e.get('entry')} · `{e.get('cwd')}` · {e.get('start', '')[11:16]}–{t} · {e['n_prompts']} prompt(s)"]
        if e.get("private"):
            lines.append("- content withheld (touched Personal/)")
        for p in e.get("prompts", []):
            lines.append(f"- asked: {p}")
        if e["n_prompts"] > len(e.get("prompts", [])):
            lines.append(f"- … {e['n_prompts'] - len(e.get('prompts', []))} more prompt(s)")
        if e.get("files"):
            more = f" (+{e['n_files'] - len(e['files'])} more)" if e.get("n_files", 0) > len(e["files"]) else ""
            lines.append("- edited: " + ", ".join(f"`{f}`" for f in e["files"]) + more)
        for c in e.get("commits", []):
            lines.append(f"- commit: {c}")
    else:
        lines = [head + f" · {e.get('source', 'job')}", f"- {e.get('message', '')}"]
    return "\n".join(lines)


def render_views(events):
    changed = 0
    by_day, by_proj = {}, {}
    for e in events:
        by_day.setdefault(e["date"], []).append(e)
        if e.get("project"):
            by_proj.setdefault(e["project"], []).append(e)
    for day, evs in by_day.items():
        evs.sort(key=lambda e: e.get("end", ""))
        projects = sorted({e["project"] for e in evs if e.get("project")})
        body = [f"---\ndate: {day}\ntype: journal\n---", f"# Journal {day}",
                "> Auto-generated by Brain OS from `Claude/_system/events.jsonl`. Do not edit — curate with `/brain end`.",
                "> See also: [[log]] | [[projects-index]] | [[health]]", "",
                "Projects touched: " + (", ".join(plink(p) for p in projects) or "none"), ""]
        body += [render_event(e) + "\n" for e in evs]
        changed += write_if_changed(os.path.join(VAULT, "Claude", "journal", f"{day}.md"), "\n".join(body))
    existing = set(vault_projects())
    for proj, evs in by_proj.items():
        if proj not in existing:
            continue
        evs.sort(key=lambda e: e.get("end", ""), reverse=True)
        body = [f"# {proj} — Activity",
                f"> Auto-generated from the journal. Curated history: [[{proj}-session-log]] · status: [[{proj}-status]] · [[{proj}]]",
                f"> {len(evs)} event(s); newest first; last 60 shown.", ""]
        day = None
        for e in evs[:60]:
            if e["date"] != day:
                day = e["date"]
                body.append(f"## [[{day}]]")
            body.append(render_event(e, with_project=False) + "\n")
        changed += write_if_changed(os.path.join(VAULT, "Projects", proj, f"{proj}-activity.md"), "\n".join(body))
    return changed


def mirror_watch(registry, write=True):
    """Copy job-owned status .md files into the vault; record freshness of other watched files."""
    fresh, changed = {}, 0
    for row in registry:
        proj = row.get("project")
        for w in row["watch"]:
            path = w.replace("/", os.sep)
            if not os.path.exists(path):
                fresh[(proj, w)] = None
                continue
            mtime = dt.datetime.fromtimestamp(os.path.getmtime(path)).astimezone()
            fresh[(proj, w)] = mtime
            if write and path.lower().endswith(".md") and proj in vault_projects():
                text = (f"# {proj} — Auto Status (mirror)\n> Mirrored by Brain OS sync from `{w}` "
                        f"(modified {mtime:%Y-%m-%d %H:%M}). Owned by the job — do not edit here. "
                        f"See [[{proj}-status]] | [[{proj}-activity]].\n\n") + read(path)
                changed += write_if_changed(os.path.join(VAULT, "Projects", proj, f"{proj}-auto-status.md"), text)
    return fresh, changed


# ---------------------------------------------------------------- status parsing

def current_section(text):
    m = re.search(r"^##\s+Current\b.*$", text, re.M)
    if not m:
        return ""
    rest = text[m.end():]
    n = re.search(r"^##\s+(?!#)", rest, re.M)
    return (m.group(0) + rest[: n.start()] if n else m.group(0) + rest).strip()


def parse_phase(text):
    # the Current section is overwritten every session; frontmatter often goes stale, so it is last resort
    for pat in (r"\*\*Phase:\*\*\s*(.+)", r"^##\s+Current Phase:\s*(.+)$", r"^##\s+Current\s*\([^)]*\)\s*[—-]+\s*(.+)$",
                r"^##\s+Current\s*[—-]+\s*(.+)$", r"^Phase:\s*(.+)$"):
        m = re.search(pat, text, re.M)
        if m:
            return m.group(1).strip()
    fm = re.match(r"---\n(.*?)\n---", text, re.S)
    if fm:
        m = re.search(r"^phase:\s*(.+)$", fm.group(1), re.M)
        if m:
            return m.group(1).strip()
    cur = current_section(text).splitlines()[1:]
    for line in cur:
        line = line.strip(" >#-*")
        if line and not line.lower().startswith("see also"):
            return line
    return "?"


def clean_phase(p, limit=90):
    p = re.sub(r"\[\[([^\]|]+\|)?([^\]]+)\]\]", r"\2", p)
    p = re.sub(r"[*`]", "", p).replace("|", "/")
    return one_line(p, limit)


def last_curated(proj):
    dates = re.findall(r"^#+\s*\[?(20\d\d-\d\d-\d\d)", read(os.path.join(VAULT, "Projects", proj, f"{proj}-session-log.md")), re.M)
    return max(dates) if dates else ""


# ---------------------------------------------------------------- health

def git(repo, *args, timeout=60):
    try:
        r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()
    except Exception as ex:
        return 1, str(ex)


def task_result(name):
    try:
        r = subprocess.run(["schtasks", "/query", "/tn", name, "/v", "/fo", "list"], capture_output=True, text=True, timeout=20)
    except Exception:
        return None
    if r.returncode != 0:
        return {"missing": True}
    info = {}
    for line in r.stdout.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            info[k.strip()] = v.strip()
    return info


def build_health(registry, events, fresh):
    warn, info = [], []
    reg_names = {r.get("project") for r in registry}
    projects = vault_projects()
    for p in projects:
        if p not in reg_names:
            warn.append(f"`{p}` has no row in [[registry]] — add one (repo, state, cluster)")
        for suffix in ("status", "session-log"):
            if not os.path.exists(os.path.join(VAULT, "Projects", p, f"{p}-{suffix}.md")):
                warn.append(f"`{p}` missing `{p}-{suffix}.md`")
    for r in registry:
        if r.get("project") and r["project"] not in projects:
            warn.append(f"registry row `{r['project']}` has no vault folder")
    # sessions captured but not curated
    latest = {}
    for e in events:
        if e.get("project") and e["kind"] == "session":
            latest.setdefault(e["project"], []).append(e["date"])
    for p, dates in sorted(latest.items()):
        lc = last_curated(p)
        pending = [d for d in dates if d > lc]
        if pending and p in projects:
            warn.append(f"`{p}`: {len(pending)} session part(s) since last curated entry ({lc or 'never'}) → `/brain end` in that repo "
                        f"(see [[{p}-activity]])")
    unassigned = [e for e in events if e["kind"] == "session" and not e.get("project")]
    if unassigned:
        cwds = sorted({e.get("cwd") for e in unassigned})
        info.append(f"{len(unassigned)} session part(s) with no mapped project, cwd: " + ", ".join(f"`{c}`" for c in cwds[:8]))
    now = now_local()
    for r in registry:
        state = r.get("state", "")
        for w in r["watch"]:
            m = fresh.get((r.get("project"), w))
            if m is None:
                warn.append(f"`{r.get('project')}` watched file missing: `{w}`")
            elif state == "live" and (now - m).total_seconds() > 3 * 86400:
                warn.append(f"`{r.get('project')}` live but `{os.path.basename(w)}` not updated for {(now - m).days}d")
        for t in r["tasks"]:
            ti = task_result(t)
            if ti is None:
                continue
            if ti.get("missing"):
                warn.append(f"`{r.get('project')}` scheduled task `{t}` not found")
                continue
            res = ti.get("Last Result", "")
            if res not in ("0", "267009", "267011"):  # 0 ok, 0x41301 running, 0x41303 never run
                warn.append(f"`{r.get('project')}` task `{t}` last result {res} at {ti.get('Last Run Time', '?')}")
            if "No Start On Batteries" in ti.get("Power Management", ""):
                info.append(f"`{t}` will not start on battery (Power Management: {ti['Power Management']})")
    code, out = git(VAULT, "status", "--porcelain")
    dirty = len([l for l in out.splitlines() if l.strip()]) if code == 0 else -1
    code2, ahead = git(VAULT, "rev-list", "--count", "@{u}..HEAD")
    _, last = git(VAULT, "log", "-1", "--format=%ci")
    info.append(f"vault git (measured before this sync commits+pushes): {dirty} changed files, {ahead if code2 == 0 else '?'} unpushed, last commit {last}")
    for r in registry:
        for repo in r["repos"]:
            if r.get("state") in ("live", "active") and os.path.isdir(repo):
                if not os.path.exists(os.path.join(repo, ".git")) and not glob.glob(os.path.join(repo, "*", ".git")):
                    warn.append(f"`{r['project']}` repo `{repo}` is not under git — no backup")
    return warn, info


# ---------------------------------------------------------------- index / status views

def replace_auto(path, block, header_if_new):
    text = read(path, None)
    if text is None:
        text = header_if_new + f"\n{AUTO_BEGIN}\n{AUTO_END}\n"
    if AUTO_BEGIN not in text:
        text = text.rstrip() + f"\n\n{AUTO_BEGIN}\n{AUTO_END}\n"
    pre, rest = text.split(AUTO_BEGIN, 1)
    post = rest.split(AUTO_END, 1)[1] if AUTO_END in rest else ""
    return write_if_changed(path, f"{pre}{AUTO_BEGIN}\n{block.strip()}\n{AUTO_END}{post}")


def render_index(registry, events):
    last_act = {}
    for e in events:
        if e.get("project"):
            last_act[e["project"]] = max(last_act.get(e["project"], ""), e["date"])
    rows_by_state = {}
    reg = {r.get("project"): r for r in registry}
    for p in vault_projects():
        r = reg.get(p, {})
        state = r.get("state") or "unregistered"
        text = read(os.path.join(VAULT, "Projects", p, f"{p}-status.md"))
        phase = clean_phase(parse_phase(text)) if text else "no status file"
        last = max(last_curated(p), last_act.get(p, ""))
        rows_by_state.setdefault(state, []).append((last, p, r.get("cluster", ""), phase))
    out = [f"_Generated {now_local():%Y-%m-%d %H:%M} by `brain.py sync` from each project's status file, "
           "the session logs and the journal. Edit [[registry]] (state/cluster/repo) or the status files — not this block._", ""]
    for state in STATES + ["unregistered"]:
        rows = sorted(rows_by_state.get(state, []), reverse=True)
        if not rows:
            continue
        out += [f"### {state.capitalize()} ({len(rows)})", "", "| Project | Cluster | Phase (from status) | Last activity |",
                "|---|---|---|---|"]
        out += [f"| [[Projects/{p}/{p}\\|{p}]] | {c} | {ph} | {last or '—'} |" for last, p, c, ph in rows]
        out.append("")
    return "\n".join(out)


def render_health(warn, info):
    lines = [f"_Generated {now_local():%Y-%m-%d %H:%M} by `brain.py sync`._", "",
             f"**{'✅ healthy' if not warn else f'⚠ {len(warn)} warning(s)'}**", ""]
    lines += [f"- ⚠ {w}" for w in warn] + [f"- ℹ {i}" for i in info]
    return "\n".join(lines)


def cmd_sync(args):
    registry = load_registry()
    new = sweep(quiet=True)
    events = load_events()
    fresh, mchanged = mirror_watch(registry)
    vchanged = render_views(events)
    warn, info = build_health(registry, events, fresh)
    replace_auto(os.path.join(VAULT, "Claude", "health.md"), render_health(warn, info),
                 "# Brain Health\n> See also: [[workflow]] | [[projects-index]] | [[registry]] | [[log]]\n")
    replace_auto(os.path.join(VAULT, "Claude", "projects-index.md"), render_index(registry, events),
                 "# Projects Index\n> See also: [[workflow]] | [[registry]] | [[health]]\n")
    summary = f"sync: {len(new)} new session part(s), {vchanged} view(s), {mchanged} mirror(s), {len(warn)} warning(s)"
    if not args.no_git:
        summary += " | " + git_backup()
    print(summary)
    log(summary)


def git_backup():
    code, _ = git(VAULT, "add", "-A")
    code, out = git(VAULT, "diff", "--cached", "--quiet")
    msg = "nothing to commit"
    if code == 1:
        c, out = git(VAULT, "commit", "-q", "-m", f"brain sync {now_local():%Y-%m-%d %H:%M}")
        msg = "committed" if c == 0 else f"COMMIT FAILED: {one_line(out, 120)}"
    c, out = git(VAULT, "pull", "--rebase", "--autostash", "-q", timeout=120)
    if c != 0:
        git(VAULT, "rebase", "--abort")
        return msg + f"; PULL FAILED (resolve by hand, never force): {one_line(out, 160)}"
    c, out = git(VAULT, "push", "-q", timeout=120)
    return msg + ("; pushed" if c == 0 else f"; PUSH FAILED: {one_line(out, 160)}")


# ---------------------------------------------------------------- hooks

def hook_input():
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def cmd_session_end(args):
    h = hook_input()
    path = h.get("transcript_path")
    if not path or not os.path.exists(path):
        return
    e = journal_transcript(path, reason=h.get("reason", ""))
    if e:
        append_events([e])
        render_views(load_events())


def cmd_session_start(args):
    h = hook_input()
    if os.environ.get("CLAUDE_CODE_ENTRYPOINT", "").startswith("sdk"):
        return  # headless jobs (claude -p): no injected context — it would leak into bot replies; SessionEnd still journals
    cwd = h.get("cwd") or os.getcwd()
    registry = load_registry()
    proj = resolve_project(cwd, registry)
    reg = {r.get("project"): r for r in registry}
    out = ["[Brain] Vault: " + VAULT.replace("/", "\\") + " | protocol: Claude/workflow.md | prefs: Claude/preferences.md"]
    if proj:
        r = reg.get(proj, {})
        text = read(os.path.join(VAULT, "Projects", proj, f"{proj}-status.md"))
        out.append(f"Project: {proj} ({r.get('state', 'unregistered')}) — phase: {clean_phase(parse_phase(text), 160) if text else 'no status file'}")
        cur = [l for l in current_section(text).splitlines()[1:] if l.strip()][:14]
        if cur:
            out.append("Status excerpt (Projects/%s/%s-status.md):" % (proj, proj))
            out += ["  " + one_line(l, 200) for l in cur]
        lc = last_curated(proj)
        pending = [e for e in load_events() if e.get("project") == proj and e["kind"] == "session" and e["date"] > lc]
        if pending:
            out.append(f"Uncurated: {len(pending)} journaled session part(s) since last session-log entry ({lc or 'never'}) — "
                       f"summarise via /brain end (raw: Projects/{proj}/{proj}-activity.md).")
        if os.path.exists(os.path.join(VAULT, "Projects", proj, f"{proj}-auto-status.md")):
            out.append(f"Job-owned status mirror: Projects/{proj}/{proj}-auto-status.md")
    else:
        live = [r["project"] for r in registry if r.get("state") == "live"]
        out.append(f"No vault project mapped for {cwd}. Live: {', '.join(live) or 'none'}. Map it in Claude/registry.md or /brain new-project.")
    health = read(os.path.join(VAULT, "Claude", "health.md"))
    warns = [l for l in health.splitlines() if l.startswith("- ⚠")]
    if warns:
        mine = [w for w in warns if proj and f"`{proj}`" in w]
        out.append(f"Health: {len(warns)} warning(s) in Claude/health.md" + (":" if mine else "."))
        out += ["  " + w[2:] for w in mine[:4]]
    print("\n".join(out))


def cmd_log(args):
    ts = now_local()
    append_events([{"kind": "job", "session_id": "", "date": ts.strftime("%Y-%m-%d"), "end": ts.isoformat(timespec="minutes"),
                    "project": args.project, "source": args.source, "message": one_line(redact(" ".join(args.message)), 400)}])
    render_views(load_events())


def main():
    ap = argparse.ArgumentParser(description="Brain OS engine")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("session-start")
    sub.add_parser("session-end")
    sub.add_parser("sweep")
    sub.add_parser("health")
    s = sub.add_parser("sync")
    s.add_argument("--no-git", action="store_true")
    l = sub.add_parser("log")
    l.add_argument("-p", "--project", required=True)
    l.add_argument("--source", default="job")
    l.add_argument("message", nargs="+")
    r = sub.add_parser("resolve")
    r.add_argument("cwd", nargs="?", default=os.getcwd())
    args = ap.parse_args()
    hook = args.cmd in ("session-start", "session-end")
    try:
        if args.cmd == "session-start":
            cmd_session_start(args)
        elif args.cmd == "session-end":
            cmd_session_end(args)
        elif args.cmd == "sweep":
            sweep()
        elif args.cmd == "sync":
            cmd_sync(args)
        elif args.cmd == "log":
            cmd_log(args)
        elif args.cmd == "resolve":
            print(resolve_project(args.cwd) or "")
        elif args.cmd == "health":
            registry = load_registry()
            fresh, _ = mirror_watch(registry, write=False)
            warn, info = build_health(registry, load_events(), fresh)
            print(render_health(warn, info))
    except Exception:
        log(f"{args.cmd} FAILED\n{traceback.format_exc()}")
        if not hook:
            raise
    if hook:
        sys.exit(0)


if __name__ == "__main__":
    main()
