# Query Graph Visualization Implementation - 2025-10-27

## Context
Added knowledge graph visualization capability to the querying cell in `ice_building_workflow.ipynb`. This allows users to see which entities and relationships from the knowledge graph were used to answer their query, making LightRAG's reasoning transparent.

## Implementation Location
**File**: `ice_building_workflow.ipynb`
**Position**: Cell 31 (inserted immediately after the query testing cell at position 30)
**Total Code**: ~210 lines of embedded visualization code

## Design Decisions

### Approach: Parse Answer Text (Not only_need_context)
**Decision**: Extract entities by matching answer text against graph nodes
**Why**: Simpler, more direct, avoids additional LightRAG query overhead
**Rejected**: Using `only_need_context=True` parameter - adds complexity

### Visualization Library: NetworkX + Matplotlib (Not pyvis)
**Decision**: Static matplotlib visualizations with NetworkX layouts
**Why**: 
- Notebook-friendly (inline display)
- Simple, reliable, well-documented
- No HTML/JavaScript complexity
**Rejected**: pyvis interactive graphs - more complex, less stable in notebooks

### Subgraph Strategy: k-hop Neighborhood
**Parameters**:
- `max_hops=2` (default) - Balance context with clarity
- `max_nodes=30` (default) - Prevent cluttered visualizations
**Algorithm**: Breadth-first expansion from seed entities with budget limits

### Visual Design
**Color Coding**:
- Red (#FF6B6B): Seed entities (mentioned in answer)
- Teal (#4ECDC4): 2-hop neighbors (context)
**Layout**: Spring layout (force-directed) with k=2, iterations=50
**Elements**: Node labels, edge labels (relationships), legend

## Key Functions

### 1. extract_entities_from_answer(answer_text, graph)
**Purpose**: Find which graph entities are mentioned in the query answer
**Strategy**:
1. Organize graph nodes by entity_type
2. Search priority types first (Organization, Person, Product, Technology)
3. Use word boundary regex matching (case-insensitive)
4. Fallback to all entity types if no priority matches
**Returns**: List of entity node IDs

### 2. build_subgraph(graph, seed_entities, max_hops, max_nodes)
**Purpose**: Create focused subgraph around seed entities
**Strategy**:
1. Verify seed entities exist in graph
2. Expand via breadth-first search with hop limit
3. Budget control to prevent overwhelming visualizations
**Returns**: NetworkX subgraph

### 3. Main Visualization Block
**Structure**:
```python
if result.get('status') == 'success':
    # Load graph from GraphML
    # Extract entities from answer
    # Build subgraph
    # Create matplotlib visualization
    # Show with legend
```

## Error Handling

### No Entities Found
**Message**: "⚠️ No entities found in answer to visualize"
**Tip**: "Try queries mentioning specific companies, people, or products"

### No Subgraph
**Message**: "⚠️ No connected subgraph found for these entities"
**Cause**: Isolated entities with no relationships in k-hop neighborhood

### Graph File Missing
**Message**: "⚠️ Graph file not found: {path}"
**Solution**: "Make sure REBUILD_GRAPH=True was used to create the graph"

### Visualization Error
**Message**: "⚠️ Visualization error: {e}"
**Context**: Graph exists but visualization failed (rare)

## Usage Pattern

### Standard Workflow
1. Run query cell (Cell 30): Enter query + mode
2. Visualization cell (Cell 31) runs automatically
3. If query succeeds → Graph visualization appears
4. If query fails → Skips visualization

### Example Queries That Work Well
- "What is Tencent's business?" (Organization entity)
- "Who is Jia Jun?" (Person entity)
- "What are NVDA's biggest risks?" (Multiple entities)
- "How does China risk impact TSMC?" (Relationship-focused)

### Queries That May Struggle
- High-level summaries without specific entities
- Generic questions ("What is the market?")
- Queries where answer doesn't mention entity names directly

## Integration Points

### Graph Storage
**File**: `ice_lightrag/storage/graph_chunk_entity_relation.graphml`
**Format**: NetworkX GraphML
**Node Attributes**: entity_type, entity_name, description, source_id
**Edge Attributes**: description, keywords

### Query Result Object
**Required**: `result` dictionary from `ice.core.query()`
**Used Keys**: 
- `status` (success check)
- `answer` (entity extraction source)

### Dependencies
- `networkx` (graph operations)
- `matplotlib.pyplot` (visualization)
- `re` (pattern matching)
- `pathlib` (file handling)

## Testing Strategy

### Test Scenarios
1. **Successful query with entities**: Verify visualization appears
2. **Query with no entities**: Check graceful handling
3. **Different query modes**: Test naive/local/global/hybrid/mix
4. **Large subgraphs**: Verify max_nodes limit works
5. **Missing graph file**: Verify error message

### Validation Checklist
- [ ] Red nodes appear for entities in answer
- [ ] Teal nodes appear for neighbors
- [ ] Edge labels show relationship descriptions
- [ ] Legend displays correctly
- [ ] Title shows query text
- [ ] No crashes on edge cases

## Future Enhancements (Optional)

### Interactive Exploration
- Add pyvis for HTML interactive graphs
- Click nodes to see full descriptions
- Filter by entity type

### Advanced Filtering
- Control which entity types to show
- Adjust hop count dynamically
- Highlight critical paths

### Export Options
- Save visualization as PNG/SVG
- Export subgraph as GraphML
- Generate visualization report

## Related Files
- `ice_building_workflow.ipynb` (Cell 31) - Main implementation
- `ice_lightrag/storage/graph_chunk_entity_relation.graphml` - Knowledge graph
- `project_information/about_lightrag/lightrag_query_workflow.md` - Query modes documentation

## Maintenance Notes
- Visualization is self-contained in single notebook cell
- No external dependencies beyond standard libraries
- Conditionally runs only on successful queries
- Graceful degradation on errors
