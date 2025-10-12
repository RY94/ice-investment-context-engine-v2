# CLAUDE.md TodoWrite Rules Enforcement Strategy

## Date
2025-10-09

## Context
User requested refinement of CLAUDE.md to ensure file synchronization and Serena memory update rules are ALWAYS included in every TodoWrite list as final todos.

## Problem
Previous implementation had rules buried in Section 3.6 and 3.7 (mid-document), making them easy to miss when creating TodoWrite lists mid-task.

## Solution: 80/20 Triple Reinforcement Strategy
Applied Pareto principle: 20% of changes drive 80% of impact through strategic placement.

### Three High-Impact Changes (~38 lines = ~5% of file)

#### Change 1: Section 1.3 "Current Sprint Priorities" - Prominent Box
**Location**: Lines 106-110 (right after heading)
**Impact**: Seen FIRST when starting any development session
```markdown
> **⚠️ TODOWRITE MANDATORY RULES** (See Section 4.1 for complete details)
>
> Every TodoWrite list MUST include these final two todos:
> 1. 📋 Review & update 6 core files + 2 notebooks if changes warrant sync
> 2. 🧠 Update Serena server memory if work warrants documentation
```

#### Change 2: Section 4 - New Mandatory Subsection
**Location**: Lines 364-392 (NEW Section 4.1, BEFORE "File Header Requirements")
**Impact**: Elevates from workflow guidance to mandatory development standard
**Contents**:
- Complete checklists for sync and memory updates
- Explains why rules exist
- Clarifies when to skip
- Emphasizes "This is not optional"

#### Change 3: Sections 3.6 & 3.7 - Cross-References
**Location**: Lines 261 and 303
**Impact**: Redirects readers from detailed workflows to mandatory rules
```markdown
⚠️ **MANDATORY RULE**: See Section 4.1 'TodoWrite Requirements' for required final todos in every TodoWrite list.
```

## Reinforcement Pattern
Three-layer strategy ensures visibility:
1. **Layer 1 (Section 1)**: Quick reminder in first section read
2. **Layer 2 (Section 4)**: Mandatory standard where coding rules live
3. **Layer 3 (Section 3)**: Detailed workflow guidance with cross-reference

## Key Insight
Development standards (Section 4) is where rules about HOW to code live. TodoWrite is a coding practice, so its mandatory requirements should be elevated to Section 4, not buried in Section 3's workflow details.

## Files Modified
1. `/CLAUDE.md` - Three strategic edits (lines 106-110, 364-392, 261, 303)
2. `/PROJECT_CHANGELOG.md` - Added entry #29 documenting changes

## Expected Outcome
Every TodoWrite list will include synchronization and memory update todos as final items, preventing documentation drift and preserving institutional knowledge across Claude Code sessions.

## Pattern for Future Use
When enforcing mandatory practices in CLAUDE.md:
1. Add quick reminder in Section 1 (high visibility)
2. Create/elevate to Section 4 as mandatory standard (where rules live)
3. Keep detailed guidance in Section 3 with cross-references (for implementation)
