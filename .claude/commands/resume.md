---
description: Resume work after crash or new session by reconstructing context from project state files
---

# Session Recovery - Reconstruct Context

You are resuming work on the ICE (Investment Context Engine) project. A previous Claude Code session may have crashed or ended. Your job is to reconstruct context and continue.

## Step 1: Check File Staleness

First, check when key files were last modified:

```bash
echo "=== FILE STALENESS CHECK ===" && \
echo "PROGRESS.md:" && stat -f "%Sm" PROGRESS.md 2>/dev/null || echo "NOT FOUND" && \
echo "" && \
echo "ICE_DEVELOPMENT_TODO.md:" && stat -f "%Sm" ICE_DEVELOPMENT_TODO.md 2>/dev/null || echo "NOT FOUND"
```

**If PROGRESS.md is more than 24 hours old, WARN the user:**
> "⚠️ WARNING: PROGRESS.md appears stale (last updated X). Context may be incomplete. Consider running /recap to analyze recent transcripts."

## Step 2: Read Context Files

Read these files in order:

1. **PROGRESS.md** - Read the "🎯 ACTIVE WORK (This Session)" section (first 200 lines)
   - This tells you: Current sprint, what was being done, blockers, next actions

2. **Serena Memories** - Use `mcp__serena__list_memories` then read the 3 most recent by date (look for `_2025_11_` pattern in names)
   - This tells you: Implementation details, architecture decisions, debugging solutions

3. **ICE_DEVELOPMENT_TODO.md** - Read first 100 lines
   - This tells you: Overall task status (X/140 tasks), current phase

4. **Git Status** - Run `git status` and `git diff --stat`
   - This tells you: Uncommitted changes = work in progress

## Step 3: Synthesize and Report

After reading, provide the user with:

### Recovery Summary
- **Last Session Work**: [What was being worked on based on PROGRESS.md]
- **Implementation Context**: [Key points from recent Serena memories]
- **Task Status**: [X/140 tasks from TODO.md]
- **Uncommitted Changes**: [Files with pending changes from git status]
- **Recommended Next Steps**: [Based on "Next Actions" from PROGRESS.md]

### Staleness Warnings (if any)
- List any files that appear outdated

## Step 4: Remind About Updates

After completing the recovered context summary, remind:

> **IMPORTANT**: When you complete work in this session, you MUST:
> 1. Update `PROGRESS.md` with session summary
> 2. Create/update Serena memory if implementation work was done
>
> This ensures the next `/resume` has fresh context. See CLAUDE.md "SESSION STATE RULE".

---

Now execute these steps and provide the recovery summary.
