# LightRAG Building Workflow (Document Insertion Pipeline)

## Overview

LightRAG implements a **dual-level retrieval system** combining traditional vector RAG with knowledge graph reasoning capabilities. The building workflow transforms raw documents into a comprehensive knowledge graph optimized for rapid and precise retrieval.

### Key Innovation Points
- **Graph-Enhanced Text Indexing**: Constructs graph structures that enable extraction of global information from multi-hop subgraphs
- **6,000x Token Efficiency**: Uses 100 tokens vs GraphRAG's 610,000 tokens
- **1/100th Operational Cost**: Approximately 25-30x cheaper than GraphRAG
- **Incremental Updates**: Supports adding new data without full rebuild (unlike GraphRAG)
- **No Community Detection Required**: Direct entity/relationship indexing vs GraphRAG's clustering approach

## Building Pipeline: Input → Chunking → Entity Extraction → Graph Construction → Storage

---

## Stage 1: Document Input

### Process
- Text documents fed into `insert()` method
- Supports batch processing: `input: str | list[str]`
- Optional document IDs: `ids: str | list[str] | None = None`
- Character-based splitting options: `split_by_character: str | None = None`

### Key Outputs to Monitor
- **Document Count**: Total documents processed
- **Document IDs**: Unique identifiers assigned to each document
- **Total Size**: Character/token count of all input documents
- **File Types**: Document formats and sources (PDF, TXT, MD, etc.)
- **Processing Timestamp**: Ingestion start/end times
- **Input Validation**: Document format compatibility checks

---

## Stage 2: Text Chunking

### Process
- **Optimal chunk size**: 1200 tokens (confirmed by benchmarks for financial documents)
- **Markdown-aware chunking**: Splits on section headers/structured boundaries
- **Performance gain**: 5-10% improvement over fixed-size splits for financial documents
- **Boundary preservation**: Maintains natural thematic breaks (important for SEC filings, risk factors)

### Key Outputs to Monitor
- **Chunks Created**: Number of chunks per document
- **Size Distribution**: Histogram of chunk sizes (min/max/avg/median)
- **Boundary Quality**: Effectiveness of section header detection
- **Overlap Statistics**: If using overlapping chunks, measure overlap sizes
- **Chunking Strategy Performance**: Comparison metrics vs fixed-size splitting
- **Processing Time**: Time per document for chunking operation
- **Memory Usage**: Peak memory during chunking process

### Financial Domain Optimization
- **SEC Filing Sections**: MD&A, Risk Factors, Financial Statements
- **Structured Boundaries**: Company profiles, executive sections, regulatory compliance
- **Metadata Preservation**: Filing dates, form types, company identifiers

---

## Stage 3: Entity & Relationship Extraction

### Process
**Uses GPT-4o-mini with specialized prompts for financial domain**

#### System Prompt Structure
```
---Role---
You are a Knowledge Graph Specialist responsible for extracting entities and relationships from the input text.

---Instructions---
1. **Entity Extraction:** Identify clearly defined and meaningful entities
  - entity_name: Name of the entity (ensure consistency)
  - entity_type: Classification of the entity (uses provided entity_types or 'Other')
  - entity_description: Comprehensive description of entity's attributes and activities

2. **Relationship Extraction:** Identify relationships between entities
  - source_entity: Name of the source entity
  - target_entity: Name of the target entity
  - relationship_keywords: High-level keywords summarizing the relationship
  - relationship_description: Nature of the relationship with clear rationale
```

#### Output Format
- **Entity**: `(entity{delimiter}entity_name{delimiter}entity_type{delimiter}entity_description)`
- **Relationship**: `(relationship{delimiter}source_entity{delimiter}target_entity{delimiter}relationship_keywords{delimiter}relationship_description)`

### Key Outputs to Monitor

#### Entity Extraction Metrics
- **Entity Count by Type**: Distribution across financial entity types
  - Company, Person, Financial_Metric, Risk_Factor
  - Regulation, Market_Sector, Investment_Product
  - Geographic_Region, Time_Period, Economic_Indicator
- **Entity Descriptions**: Quality and completeness of entity attributes
- **Entity Frequency**: Most/least common entities across documents
- **Entity Consistency**: Duplicate detection and normalization effectiveness

#### Relationship Extraction Metrics
- **Relationship Count**: Total relationships extracted
- **Source-Target Pairs**: Unique entity pair combinations
- **Relationship Keywords**: High-level concept summary effectiveness
- **Relationship Strength Scores**: Numeric scores indicating relationship importance
- **Relationship Types**: Distribution of relationship categories (conflict, collaboration, influence, etc.)

#### Performance Metrics
- **API Costs**: OpenAI API usage and costs per document
- **Processing Time**: Extraction time per chunk/document
- **Token Usage**: Prompt and completion tokens consumed
- **Error Rates**: Failed extractions or malformed outputs
- **Quality Scores**: Extraction accuracy and completeness

### Financial Domain Specializations
```python
# Suggested entity types for ICE financial domain
FINANCIAL_ENTITY_TYPES = [
    "Company", "Person", "Financial_Metric", "Risk_Factor",
    "Regulation", "Market_Sector", "Investment_Product",
    "Geographic_Region", "Time_Period", "Economic_Indicator"
]
```

---

## Stage 4: Graph Construction

### Process
- **Graph Building**: `merge_nodes_and_edges()` constructs graph with deduplication
- **Entity Disambiguation**: Merges identical entities from different document segments
- **Relationship Merging**: Combines similar relationships with strength aggregation
- **Incremental Updates**: Dynamic graph modification without full rebuilds
- **No Community Detection**: Direct indexing vs GraphRAG's community clustering

### Key Outputs to Monitor

#### Graph Structure Metrics
- **Total Unique Nodes**: Final entity count after deduplication
- **Total Unique Edges**: Final relationship count after merging
- **Graph Density**: Edge count / (Node count × (Node count - 1))
- **Connected Components**: Number of disconnected subgraphs
- **Largest Component Size**: Percentage of nodes in main connected component

#### Network Analysis Metrics
- **Average Degree Centrality**: Mean connections per node
- **Clustering Coefficient**: Local clustering density
- **Network Diameter**: Longest shortest path between any two nodes
- **Hub Nodes**: Entities with highest degree centrality
- **Bridge Edges**: Relationships connecting different graph regions

#### Deduplication Metrics
- **Duplicate Entities Merged**: Count of identical entities consolidated
- **Duplicate Relationships Merged**: Count of similar relationships combined
- **Merge Accuracy**: Quality of entity/relationship matching
- **Processing Efficiency**: Time saved vs. full rebuild approach

#### Incremental Update Metrics
- **New Nodes Added**: Fresh entities from incremental updates
- **New Edges Added**: Fresh relationships from updates
- **Modified Nodes**: Entities with updated attributes
- **Graph Evolution Rate**: Rate of structural change over time

---

## Stage 5: Storage & Indexing

### Storage Architecture
Data stored in specialized databases for optimal performance:

#### Vector Storage Options
- **NanoVectorDBStorage**: Lightweight, local (recommended for development)
- **PGVectorStorage**: PostgreSQL with pgvector extension
- **MilvusVectorDBStorage**: Scalable vector database
- **ChromaVectorDBStorage**: Open-source embedding database
- **FaissVectorDBStorage**: Facebook's similarity search
- **MongoVectorDBStorage**: MongoDB with vector search
- **QdrantVectorDBStorage**: Vector search engine

#### Key-Value Storage Options
- **JsonKVStorage**: File-based JSON storage
- **PGKVStorage**: PostgreSQL key-value
- **RedisKVStorage**: In-memory data structure store
- **MongoKVStorage**: MongoDB document storage

#### Graph Storage Options
- **NetworkXStorage**: Python graph library (lightweight)
- **Neo4JStorage**: Professional graph database
- **PGGraphStorage**: PostgreSQL graph extensions
- **AGEStorage**: Apache Age graph extension

### Storage Components
- **`chunks_vdb`**: Vector embeddings of text chunks
- **`entities_vdb`**: Vector embeddings of extracted entities
- **`relationships_vdb`**: Vector embeddings of relationships
- **`chunk_entity_relation_graph`**: Graph structure storage

### Key Outputs to Monitor

#### Storage Size Metrics
- **Chunks Vector DB Size**: Storage space for chunk embeddings
- **Entities Vector DB Size**: Storage space for entity embeddings
- **Relationships Vector DB Size**: Storage space for relationship embeddings
- **Graph Database Size**: Storage space for graph structure
- **Total Storage Footprint**: Combined storage across all components

#### Performance Metrics
- **Indexing Time**: Time to create vector indices
- **Write Performance**: Documents/entities indexed per second
- **Memory Usage**: Peak memory during indexing process
- **Disk I/O**: Read/write operations per second during storage
- **Compression Ratios**: Storage efficiency gains from compression

#### Database Configuration
- **Connection Pool Size**: Concurrent database connections
- **Index Configuration**: Vector index parameters (HNSW, IVF, etc.)
- **Caching Strategy**: In-memory cache hit rates
- **Backup Strategy**: Storage redundancy and recovery metrics

### Recommended Configurations

#### Development Setup
```python
# Lightweight configuration for development
vector_storage = NanoVectorDBStorage()
kv_storage = JsonKVStorage()
graph_storage = NetworkXStorage()
```

#### Production Setup
```python
# Scalable configuration for production
vector_storage = QdrantVectorStorage()
kv_storage = RedisKVStorage()
graph_storage = Neo4JStorage()
```

---

## Visualization Opportunities for Building Process

### 1. Entity-Relationship Network Visualization
- **Interactive Graph Display**: Using NetworkX → pyvis conversion
- **Node Size by Importance**: Based on degree centrality or frequency
- **Edge Thickness by Strength**: Relationship strength visualization
- **Color Coding**: Entity types with distinct color schemes
- **Layout Algorithms**: Force-directed, hierarchical, or circular layouts

### 2. Real-Time Building Progress Dashboard
- **Extraction Progress Bar**: Documents processed / total documents
- **Entity Count by Type**: Live bar chart updating during extraction
- **Relationship Growth**: Real-time relationship count increase
- **API Usage Tracker**: Costs and token consumption meters
- **Processing Speed**: Documents/chunks processed per minute

### 3. Statistical Analysis Dashboards
- **Chunk Size Distribution**: Histogram showing chunk size effectiveness
- **Entity Frequency Analysis**: Word cloud or bar chart of most common entities
- **Relationship Type Distribution**: Pie chart of relationship categories
- **Graph Growth Visualization**: Time series of nodes/edges over processing time
- **Storage Utilization**: Storage component size comparison

### 4. Quality Assurance Visualization
- **Deduplication Effectiveness**: Before/after entity counts
- **Extraction Quality Metrics**: Accuracy and completeness scores
- **Graph Connectivity Analysis**: Connected components and isolated nodes
- **Entity Type Coverage**: Coverage across expected financial entity types

### 5. Financial Domain Specializations
- **SEC Filing Section Analysis**: Entity distribution by document section
- **Company Relationship Networks**: Corporate structure visualization
- **Risk Factor Interconnections**: Risk propagation through entity networks
- **Regulatory Compliance Mapping**: Regulation-to-company relationship trees

---

## Implementation Notes

### Critical Requirements
- **Storage Initialization**: Must call `await rag.initialize_storages()` before use
- **Pipeline Status**: Must call `await initialize_pipeline_status()` for proper setup
- **Error Handling**: Common errors include `AttributeError: __aenter__` and `KeyError: 'history_messages'`

### Performance Optimization
- **Financial Documents**: 1200-1500 token chunks optimal for SEC filings
- **Metadata Enhancement**: Include company name, filing date, form type, financial metrics
- **Batch Processing**: Process multiple documents in parallel when possible
- **Memory Management**: Monitor memory usage during large document processing

### Cost Efficiency
- **Local LLM Integration**: Use Ollama for extraction to reduce API costs
- **Incremental Processing**: Only process new/changed documents
- **Caching Strategy**: Cache extraction results to avoid re-processing
- **Optimization Monitoring**: Track cost per document and optimize accordingly