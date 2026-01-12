# Observability Cultural Rules

## The Prime Directive

**If a decision affects memory, retrieval, routing, or context, it must be inspectable. No black boxes. No "the model decided."**

## Core Principles

### 1. Transparency Over Magic
- Every decision must be explainable
- No "black box" behavior in production
- Users can inspect and understand system behavior
- Decisions are based on observable criteria, not hidden heuristics

### 2. Auditability
- All significant system decisions are logged
- Retrieval traces show exactly what models saw
- Memory promotion events are tracked
- Write-time decisions are recorded with full context

### 3. Debuggability
- System problems can be diagnosed through observability data
- Good vs bad answers can be compared and analyzed
- Memory contradictions can be detected and resolved
- Performance bottlenecks can be identified

### 4. Accountability
- No "the model decided" excuses
- Every automated decision has traceable reasoning
- System behavior is predictable and explainable
- Human oversight remains possible for critical decisions

## Implementation Guidelines

### Logging Standards
- Use structured logging with correlation IDs
- Include full context for every decision
- Redact sensitive content appropriately
- Maintain observability data retention policies

### Debug Surface Design
- `/ops/memory/user/{id}` - Inspect user's long-term memory
- `/ops/retrieval/trace/{request_id}` - Full retrieval trace for any request
- `/ops/write/decisions/{conversation_id}` - Message-by-message write decisions
- `/ops/alerts` - System health and critical alerts

### Memory Management Rules
- Long-term memory must be boring, stable, and provable
- No emotional content in permanent memory
- Preferences and facts can be promoted, emotions cannot
- All promotion events are logged and reviewable

### Retrieval Transparency
- Every retrieval operation is traced
- Users can see exactly what context was assembled
- Token allocation and scoring is documented
- Budget constraints and their impact are visible

### Alert Thresholds
- Memory promotion rejection rate > 80%
- Retrieval hit rate < 10%
- Token budget exceeded > 95%
- Memory contradiction rate > 10%

## Cultural Enforcement

### Code Review
- All new features must include observability
- No decisions without logging
- Debug surfaces are required for complex operations

### Testing
- Observability data must be validated in tests
- Debug endpoints are tested for correctness
- Alert systems are verified

### Documentation
- System behavior is documented through examples
- Debug workflows are clearly explained
- Observability data interpretation guides

## Anti-Patterns to Avoid

❌ **"The model decided"** - Always provide reasoning
❌ **Silent failures** - Log all errors and anomalies  
❌ **Untraceable decisions** - Every decision must be explainable
❌ **Hidden heuristics** - All scoring and ranking must be visible
❌ **Unmonitored memory growth** - Track memory health metrics

## Positive Patterns to Encourage

✅ **Full traceability** - Every operation can be traced end-to-end
✅ **Rich context** - Decisions include comprehensive metadata
✅ **User visibility** - Users can inspect system behavior
✅ **Gradual improvement** - Data-driven optimization over guesses
✅ **Human oversight** - Critical decisions remain reviewable

## Emergency Procedures

### Memory Corruption
1. Check `/ops/alerts` for contradiction alerts
2. Review recent memory promotions in `/ops/memory/user/{id}`
3. Identify conflicting facts through retrieval traces
4. Manually resolve or remove conflicting memories

### Poor Retrieval Quality
1. Analyze retrieval traces in `/ops/retrieval/trace/{request_id}`
2. Check token allocation and scoring breakdowns
3. Review context assembly snapshots
4. Adjust retrieval parameters based on evidence

### System Performance Issues
1. Monitor alert thresholds
2. Review token utilization metrics
3. Check cache hit rates
4. Analyze retrieval efficiency patterns

## Success Metrics

- **Transparency Score**: % of operations with complete observability data
- **Debug Time**: Average time to diagnose issues through observability
- **User Trust**: Understanding of system behavior through inspection
- **System Reliability**: Reduced incidents through proactive monitoring