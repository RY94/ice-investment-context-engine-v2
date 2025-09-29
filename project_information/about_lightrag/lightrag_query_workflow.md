# LightRAG Query Workflow (Retrieval Pipeline)

## Overview

LightRAG's query workflow implements a sophisticated dual-level retrieval system that combines entity-focused and relationship-based search strategies. The system achieves superior performance through adaptive mode selection and graph-enhanced context assembly.

### Performance Benchmarks vs GraphRAG
- **Token Efficiency**: 100 tokens vs 610,000 tokens (6,000x improvement)
- **API Calls**: Single retrieval call vs GraphRAG's multiple community calls
- **Response Time**: 200ms average response time
- **Cost**: 1/100th of GraphRAG operational costs
- **Win Rates**: 80% vs baseline methods on large datasets
- **Quality Metrics**: Superior on Comprehensiveness, Diversity, Empowerment, Overall

## Query Pipeline: Query → Mode Selection → Keyword Generation → Retrieval → LLM Generation → Response

---

## Stage 1: Query Input

### Process
- Natural language query submitted to `aquery()` method
- Optional pre-computed embeddings for query optimization
- Session context integration (if available)
- Query complexity analysis for mode selection

### Key Outputs to Monitor
- **Query Text**: Original natural language input
- **Query Length**: Character and token count
- **Query Embedding Vector**: Semantic representation of the query
- **Query Timestamp**: Submission time for session tracking
- **Session Context**: Related previous queries or conversation state
- **Query Type Classification**: Factual, analytical, comparative, etc.
- **Complexity Score**: Estimated difficulty/scope of the query

### Query Preprocessing
- **Text Cleaning**: Remove special characters, normalize whitespace
- **Intent Recognition**: Classify query intent (entity-specific, relationship-based, analytical)
- **Entity Detection**: Identify specific entities mentioned in the query
- **Temporal Context**: Extract time-related constraints or preferences

---

## Stage 2: Mode Selection

LightRAG supports 5 distinct query modes, each optimized for different types of information needs.

### Query Modes - Detailed Analysis

#### **Naive Mode** (`mode="naive"`)
- **Implementation**: Direct vector similarity search against chunk embeddings
- **Process**: Query embedding → chunk_vdb similarity search → top-k chunks
- **Performance**: Fast execution, minimal computational overhead
- **Best For**: Simple factual queries, quick searches, direct information lookup
- **Use Cases**:
  - "What is Apple's current stock price?"
  - "When was Tesla founded?"
- **Limitation**: Lacks graph-based context and relationship insights
- **Token Usage**: Lowest token consumption
- **Response Time**: ~50-100ms

#### **Local Mode** (`mode="local"`)
- **Implementation**: Entity-focused retrieval from immediate graph neighborhood
- **Process**: Query → entities_vdb search → traverse chunk_entity_relation_graph → retrieve relevant chunks
- **Algorithm**:
  1. Find relevant entities based on query
  2. Expand to immediate neighbors (1-hop)
  3. Retrieve chunks connected to entity neighborhood
- **Best For**: Detailed, entity-specific queries requiring precise information
- **Use Cases**:
  - "What are Apple's Q3 revenue figures and breakdown?"
  - "Tesla's specific manufacturing challenges in 2023"
  - "Amazon's cloud services market share details"
- **Performance**: Most effective for entity-specific analysis
- **Limitation**: May miss broader contextual relationships
- **Response Time**: ~150-200ms

#### **Global Mode** (`mode="global"`)
- **Implementation**: Relationship-focused retrieval using high-level concepts
- **Process**: Query → generate high-level keywords → relationships_vdb search → retrieve connected chunks
- **Algorithm**:
  1. Extract high-level themes from query
  2. Search relationship embeddings for relevant concepts
  3. Retrieve chunks connected to matching relationships
- **Best For**: High-level thematic queries and overarching concepts
- **Use Cases**:
  - "What are the main market trends in tech stocks?"
  - "How do supply chain issues affect automotive industry?"
  - "Regulatory impacts on fintech companies"
- **Performance**: Most effective for global relationship queries
- **Limitation**: May lack specific entity detail depth
- **Response Time**: ~180-250ms

#### **Hybrid Mode** (`mode="hybrid"`) - **RECOMMENDED DEFAULT**
- **Implementation**: Combines strengths of local and global retrieval
- **Process**: Simultaneous entity-specific + relationship-level retrieval with result fusion
- **Algorithm**:
  1. Parallel execution of Local and Global modes
  2. Intelligent result fusion and ranking
  3. Balanced entity detail + relationship context
- **Best For**: Complex queries requiring both detail and context
- **Performance**: Excels across all evaluation criteria
- **Use Cases**:
  - "Should I invest in Tesla considering market conditions and company fundamentals?"
  - "How do Apple's recent partnerships affect its competitive position?"
  - "Analyze Netflix's content strategy impact on subscriber growth"
- **Advantage**: Provides both breadth and analytical depth
- **Token Usage**: Higher but provides maximum value
- **Response Time**: ~200-300ms

#### **Mix Mode** (`mode="mix"`)
- **Implementation**: Combines vector chunk search with graph-based retrieval
- **Process**: Traditional RAG chunk retrieval + graph context enrichment
- **Algorithm**:
  1. Standard vector similarity search on chunks
  2. Graph-based context expansion
  3. Merge and rank combined results
- **Use Cases**: When both chunk-level detail and graph relationships are needed
- **Performance**: Balanced approach between speed and comprehensiveness
- **Response Time**: ~150-250ms

### Mode Selection Outputs to Monitor
- **Selected Mode**: Which mode was chosen for the query
- **Mode Selection Reasoning**: Why this mode was optimal
- **Query Complexity Score**: Metric influencing mode choice
- **Expected Strategy**: Anticipated retrieval approach
- **Fallback Mode**: Alternative mode if primary fails
- **Mode Performance History**: Success rates for similar queries

---

## Stage 3: Keyword Generation

### Process
LLM generates relevant search terms for targeted retrieval based on selected mode.

### Keyword Types
- **Low-Level Keywords (ll_keywords)**: Specific, entity-focused terms
- **High-Level Keywords (hl_keywords)**: Conceptual, relationship-focused terms

### Generation Algorithm
```
Input: Query text + Selected mode
LLM Process:
  1. Analyze query intent and scope
  2. Extract specific entities and concepts
  3. Generate mode-appropriate keywords
  4. Rank keywords by relevance
Output: Structured keyword lists with relevance scores
```

### Key Outputs to Monitor
- **Low-Level Keywords**: Entity names, specific terms, identifiers
- **High-Level Keywords**: Concepts, themes, relationship types
- **Keyword Relevance Scores**: Similarity to original query
- **Semantic Similarity**: Keywords' relation to query embedding
- **Generation Time**: Time spent on keyword extraction
- **Token Usage**: Tokens consumed in keyword generation
- **Keyword Quality Metrics**: Effectiveness in retrieval results

### Financial Domain Keyword Examples
```
Query: "How do Tesla's supply chain challenges affect profitability?"

Low-Level Keywords:
- Tesla, supply chain, profitability, manufacturing, costs, margins

High-Level Keywords:
- automotive industry, supply chain disruption, operational efficiency,
  financial performance, manufacturing challenges, cost management
```

---

## Stage 4: Retrieval

The retrieval stage executes mode-specific search strategies to gather relevant information.

### Mode-Specific Retrieval Strategies

#### Local Mode Retrieval
**Process**: Entity-focused neighborhood search
- **Entity Identification**: Find entities matching query keywords
- **Graph Traversal**: Explore immediate entity neighborhoods
- **Hop Depth**: Typically 1-2 hops for precision
- **Chunk Collection**: Gather chunks connected to relevant entities

**Outputs to Monitor**:
- **Entities Retrieved**: Number and types of relevant entities found
- **Neighborhood Size**: Total nodes in expanded graph region
- **Hop Depth Traversed**: Maximum relationship distance explored
- **Entity Relevance Scores**: Ranking of entity importance to query
- **Connected Chunks**: Number of text chunks linked to entities

#### Global Mode Retrieval
**Process**: High-level concept and relationship search
- **Concept Matching**: Find relationships matching high-level keywords
- **Relationship Traversal**: Explore conceptually similar relationships
- **Theme Aggregation**: Collect information around common themes
- **Context Assembly**: Build comprehensive thematic context

**Outputs to Monitor**:
- **Relationships Retrieved**: Number of relevant relationships found
- **Concept Coverage**: Breadth of high-level themes addressed
- **Relationship Types**: Distribution of relationship categories
- **Theme Coherence**: Consistency of retrieved thematic content
- **Global Context Size**: Total information gathered from relationships

#### Hybrid Mode Retrieval
**Process**: Combined local + global approach with intelligent fusion
- **Parallel Execution**: Simultaneous Local and Global retrieval
- **Result Fusion**: Merge and rank results from both approaches
- **Duplicate Elimination**: Remove redundant information
- **Balance Optimization**: Ensure both detail and context representation

**Outputs to Monitor**:
- **Local Results**: Entity-specific information retrieved
- **Global Results**: Relationship-based context retrieved
- **Fusion Effectiveness**: Quality of result combination
- **Balance Score**: Ratio of entity detail vs. relationship context
- **Duplicate Removal**: Redundant information eliminated

### Universal Retrieval Metrics
- **Retrieval Scores**: Relevance rankings for all retrieved content
- **Total Chunks Retrieved**: Number of text chunks gathered
- **Content Diversity**: Variety of information sources
- **Retrieval Time**: Time spent on search operations
- **Search Efficiency**: Results quality vs. computational cost

---

## Stage 5: Context Assembly

### Process
Transform retrieved chunks into structured LLM prompt format with proper source attribution and evidence chains.

### Context Assembly Components
- **Query Integration**: Incorporate original query into context
- **Source Attribution**: Link each piece of information to original documents
- **Evidence Chain Construction**: Build logical reasoning paths
- **Confidence Scoring**: Assign reliability scores to information pieces
- **Context Optimization**: Organize information for optimal LLM processing

### Key Outputs to Monitor
- **Context Prompt Size**: Total tokens in assembled prompt
- **Source Documents Included**: Number and types of original documents
- **Evidence Chain Quality**: Strength of reasoning path construction
- **Source Attribution Coverage**: Percentage of information with proper attribution
- **Confidence Score Distribution**: Range and average confidence levels
- **Context Coherence**: Logical flow and organization quality
- **Token Efficiency**: Information density per token used

### Context Structure
```
Context Prompt Format:
1. Query Restatement
2. Relevant Entity Information
   - Entity details with source attribution
   - Confidence scores per entity fact
3. Relationship Information
   - Connection descriptions with evidence
   - Relationship strength indicators
4. Supporting Evidence
   - Direct quotes from source documents
   - Document metadata (date, type, source)
5. Confidence and Attribution Summary
```

### Financial Context Specializations
- **Temporal Context**: Time-sensitive financial information prioritization
- **Regulatory Context**: Compliance and regulatory requirement inclusion
- **Market Context**: Industry and market condition integration
- **Risk Context**: Risk factor and mitigation strategy inclusion

---

## Stage 6: LLM Generation

### Process
Generate comprehensive answer using assembled context with GPT-4o-mini (default model).

### Generation Parameters
- **Model**: GPT-4o-mini (configurable)
- **Temperature**: Optimized for factual accuracy
- **Max Tokens**: Based on query complexity
- **Stop Sequences**: Configured for clean response termination

### Key Outputs to Monitor
- **Response Text**: Generated answer content
- **Generation Time**: Time spent on LLM inference
- **Tokens Used**:
  - Prompt tokens (context + query)
  - Completion tokens (generated response)
  - Total tokens consumed
- **Cost Calculation**: API costs based on token usage
- **Response Quality Metrics**:
  - Relevance to original query
  - Factual accuracy
  - Completeness of answer
  - Clarity and readability

### Response Enhancement Features
- **Source Attribution**: Each claim linked to source documents
- **Confidence Scoring**: Reliability indicators for different facts
- **Multi-Perspective**: Balanced viewpoints when applicable
- **Uncertainty Handling**: Clear indication of uncertain information
- **Follow-up Suggestions**: Related queries that might be useful

### Financial Domain Response Optimization
- **Investment Implications**: Clear business/investment insights
- **Risk Assessment**: Explicit risk factor analysis
- **Quantitative Context**: Financial metrics and numerical context
- **Temporal Relevance**: Time-sensitive information highlighting
- **Regulatory Compliance**: Relevant compliance considerations

---

## Visualization Opportunities for Query Process

### 1. Query Path Visualization
- **Multi-Hop Reasoning Paths**: Visual representation of reasoning chains
- **Entity Traversal Animation**: Show how query moves through knowledge graph
- **Relationship Path Highlighting**: Emphasize key relationship connections
- **Decision Point Markers**: Show where reasoning branches or converges
- **Confidence Heat Maps**: Color-code paths by confidence levels

### 2. Real-Time Query Analytics Dashboard
- **Mode Selection Display**: Show which mode was chosen and why
- **Retrieval Progress**: Real-time search progress across different databases
- **Token Usage Meter**: Live tracking of token consumption
- **Response Time Tracker**: Query processing speed monitoring
- **Cost Calculator**: Real-time API cost accumulation

### 3. Interactive Subgraph Exploration
- **Query-Specific Subgraph**: Show only relevant portion of knowledge graph
- **Interactive Node Expansion**: Click to explore entity neighborhoods
- **Relationship Detail Panels**: Hover for relationship descriptions
- **Source Document Links**: Direct access to original source material
- **Evidence Trail Navigation**: Follow reasoning from query to conclusion

### 4. Performance Analytics Visualization
- **Mode Performance Comparison**: Success rates across different modes
- **Query Type Analysis**: Performance by question category
- **Response Quality Trends**: Quality metrics over time
- **Efficiency Metrics**: Cost vs. quality trade-off analysis
- **User Satisfaction Tracking**: Query success and user feedback

### 5. Source Attribution and Confidence Visualization
- **Source Document Network**: Show which documents contributed to answer
- **Confidence Score Distribution**: Histogram of confidence levels
- **Evidence Strength Indicators**: Visual strength of supporting evidence
- **Source Reliability Metrics**: Trust scores for different information sources
- **Attribution Flow Diagram**: Trace facts back to original sources

### 6. Financial Domain Specialized Views
- **Investment Decision Tree**: Show factors contributing to investment insights
- **Risk Assessment Radar**: Visual risk profile based on retrieved information
- **Market Context Timeline**: Temporal context visualization
- **Company Relationship Network**: Corporate structure and partnership views
- **Regulatory Impact Analysis**: Compliance requirement visualization

---

## Query Mode Optimization Guidelines

### When to Use Each Mode

#### Use **Naive Mode** for:
- Simple factual lookups
- Quick information retrieval
- When speed is prioritized over depth
- Basic Q&A scenarios

#### Use **Local Mode** for:
- Company-specific analysis
- Entity-focused deep dives
- Detailed financial metric queries
- Specific executive or product information

#### Use **Global Mode** for:
- Market trend analysis
- Industry-wide insights
- Thematic research queries
- Broad conceptual understanding

#### Use **Hybrid Mode** for:
- Investment decision support
- Complex analytical queries
- Multi-faceted research needs
- Comprehensive company analysis

#### Use **Mix Mode** for:
- Balanced detail and context needs
- When both chunk precision and graph insights are valuable
- Experimental query approaches

### Performance Optimization Strategies

#### Query Preprocessing
- **Intent Classification**: Automatically detect optimal mode
- **Entity Pre-extraction**: Identify key entities for Local mode optimization
- **Complexity Scoring**: Use query complexity to guide mode selection

#### Retrieval Optimization
- **Caching Strategy**: Cache frequent query results
- **Parallel Processing**: Concurrent execution where possible
- **Adaptive Top-K**: Dynamic adjustment of retrieval limits

#### Context Optimization
- **Token Budget Management**: Optimize context size for token limits
- **Relevance Filtering**: Remove low-relevance information
- **Source Prioritization**: Emphasize high-quality sources

---

## Implementation Integration Points

### ICE-Specific Configuration
```python
from lightrag import LightRAG, QueryParam

# Optimal configuration for ICE
rag = LightRAG(
    working_dir="./ice_lightrag_storage",
    chunk_token_size=1200,  # Optimal for financial documents
    llm_model_func=ollama_model_complete,  # Local LLM for cost efficiency
    embedding_func=ollama_embed
)

# Query execution examples
company_analysis = await rag.aquery(
    "What are Tesla's key financial risks?",
    param=QueryParam(mode="local", top_k=10)
)

market_trends = await rag.aquery(
    "What are the main trends in EV market?",
    param=QueryParam(mode="global", top_k=15)
)

investment_analysis = await rag.aquery(
    "Should I invest in Tesla considering market conditions?",
    param=QueryParam(mode="hybrid", top_k=20)
)
```

### Error Handling and Monitoring
```python
try:
    # Primary query with comprehensive mode
    result = await rag.aquery(query, param=QueryParam(mode="hybrid"))
except Exception as e:
    logger.error(f"LightRAG query failed: {e}")
    # Fallback to simpler mode
    result = await rag.aquery(query, param=QueryParam(mode="naive"))
```

### Performance Monitoring Integration
- **Query Logging**: Log all queries with mode, performance metrics
- **Success Rate Tracking**: Monitor query success/failure rates
- **Cost Optimization**: Track and optimize API usage costs
- **Quality Assessment**: Implement response quality scoring
- **User Feedback**: Collect and analyze user satisfaction data

---

## Financial Domain Query Patterns

### Investment Analysis Queries
- **Company Fundamentals**: "Analyze Apple's financial health and growth prospects"
- **Competitive Position**: "How does Tesla compare to other EV manufacturers?"
- **Market Opportunity**: "What is the growth potential in renewable energy sector?"

### Risk Assessment Queries
- **Company-Specific Risks**: "What are the main risks facing Amazon's cloud business?"
- **Market Risks**: "How do interest rate changes affect tech stocks?"
- **Regulatory Risks**: "What regulatory challenges face fintech companies?"

### Market Analysis Queries
- **Trend Analysis**: "What are emerging trends in artificial intelligence investments?"
- **Sector Comparison**: "Compare performance of tech vs healthcare sectors"
- **Economic Impact**: "How does inflation affect different industry sectors?"

### Portfolio Management Queries
- **Diversification Analysis**: "How well diversified is my current portfolio?"
- **Performance Attribution**: "What factors drove my portfolio performance this quarter?"
- **Rebalancing Recommendations**: "Should I rebalance my portfolio given current market conditions?"

These query patterns demonstrate LightRAG's versatility in handling complex financial analysis tasks through its sophisticated dual-level retrieval system.