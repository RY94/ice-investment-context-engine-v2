# ICE User Personas - Detailed Profiles

> **Location**: `/project_information/user_research/ICE_USER_PERSONAS_DETAILED.md`
> **Purpose**: Complete user persona profiles for product planning and stakeholder presentations
> **Last Updated**: 2025-01-22
> **Related**: `ICE_PRD.md` (contains concise persona summaries for AI development)

---

## Overview

This document contains detailed user persona profiles for the Investment Context Engine (ICE). These personas represent the primary users within boutique hedge funds and guide product development, feature prioritization, and user experience design.

**For AI Development**: See `ICE_PRD.md` Section 3 for concise persona summaries focused on technical requirements, use cases, and success metrics.

**For Product Planning**: Use these detailed profiles to understand user motivations, workflows, and pain points in depth.

---

## Persona 1: Portfolio Manager (Primary Decision Maker)

**Profile**: Sarah Chen, Portfolio Manager
- **Role**: Makes final investment decisions for boutique long/short equity fund
- **Experience**: 15 years, previously at larger fund, now running $100M AUM boutique
- **Team**: 2 analysts, managing 25-40 positions

**Goals**:
- Maximize alpha through early signal identification
- Manage portfolio-level risk across correlated positions
- Validate investment theses with comprehensive context
- Minimize time on data gathering, maximize time on thinking

**Pain Points**:
- Information overload from multiple data sources
- Missed signals due to fragmented context
- Difficulty tracking interconnected portfolio risks
- Time-consuming manual research synthesis

**Key Use Cases**:
1. **Portfolio Risk Analysis**: "What are the top 3 risks across my current portfolio?"
2. **Opportunity Identification**: "Find companies with improving margins in my coverage universe"
3. **Thesis Validation**: "What signals support or contradict my NVDA bull thesis?"
4. **Correlation Discovery**: "How does China regulatory risk impact my tech holdings?"

**Success Criteria**:
- Reduce research synthesis time by 60%
- Identify 2-3 actionable insights per week that weren't previously visible
- Complete portfolio risk review in <30 minutes vs 2+ hours

---

## Persona 2: Research Analyst (Research & Deep Analysis)

**Profile**: David Kim, Senior Research Analyst
- **Role**: Deep research on technology and industrial sectors
- **Experience**: 8 years, covering 15-20 companies
- **Responsibilities**: Build investment theses, monitor portfolio positions

**Goals**:
- Build comprehensive, differentiated investment theses
- Find non-consensus insights before market catches on
- Efficiently monitor portfolio companies for inflection points
- Connect macro trends to individual company impacts

**Pain Points**:
- Time-consuming manual reading of transcripts and filings
- Difficulty connecting dots across company relationships
- Hard to track historical analyst sentiment changes
- Repetitive work extracting key data points

**Key Use Cases**:
1. **Company Deep-Dive**: "Summarize TSMC's customer concentration risk over last 2 years"
2. **Sector Analysis**: "How are semiconductor supply chain dynamics evolving?"
3. **Relationship Mapping**: "What companies are exposed to NVDA's success?"
4. **Thesis Building**: "Build investment thesis for company X based on all available data"

**Success Criteria**:
- Complete company deep-dive in 2 hours vs 8 hours
- Identify 3-5 relationship insights not obvious from single sources
- Track 20+ companies without missing critical developments

---

## Persona 3: Junior Analyst (Data Triage & Monitoring)

**Profile**: Alex Rodriguez, Junior Analyst
- **Role**: Initial research, data gathering, news monitoring
- **Experience**: 2 years, learning from senior team
- **Responsibilities**: Triage news flow, preliminary research, monitoring alerts

**Goals**:
- Quickly extract relevant signals from high-volume news flow
- Efficiently triage which information needs senior attention
- Learn investment frameworks by seeing how insights connect
- Build research skills by understanding relationship patterns

**Pain Points**:
- Overwhelming daily news volume (100+ articles)
- Unclear which signals are important vs noise
- Difficulty understanding second-order implications
- Time pressure to deliver quality research quickly

**Key Use Cases**:
1. **News Monitoring**: "What are the top 5 most important developments today?"
2. **Signal Extraction**: "Are there any BUY/SELL recommendations for our portfolio?"
3. **Preliminary Research**: "Quick summary of company X's latest earnings call"
4. **Learning**: "Show me how this news about China impacts our holdings"

**Success Criteria**:
- Triage 100+ daily news items in <30 minutes
- 90%+ accuracy in flagging important signals for senior review
- Deliver preliminary research 3x faster than manual approach

---

## Usage Guidelines

### When to Reference This Document
- **Product Planning**: Understanding user motivations and workflows
- **Feature Prioritization**: Evaluating which capabilities matter most to which personas
- **Stakeholder Presentations**: Communicating target user needs and pain points
- **User Experience Design**: Designing interfaces that match user mental models

### When to Reference ICE_PRD.md Instead
- **AI Development**: Technical requirements, query patterns, success metrics
- **Sprint Planning**: Immediate development priorities and acceptance criteria
- **Integration Work**: Understanding what capabilities to build and how to validate them

---

**Document Version**: 1.0
**Last Updated**: 2025-01-22
**Next Review**: After user validation sessions or major product pivots
