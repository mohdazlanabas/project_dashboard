# ISWMC Dashboard - Project Architecture

## Overview
The ISWMC (Integrated Solid Waste Management Center) Dashboard is a Django-based web application that provides real-time analytics and AI-powered insights for waste management operations. The system aggregates data from MongoDB and presents it through interactive charts, KPIs, and a natural language query interface.

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ISWMC Dashboard Architecture                          │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌──────────────────────────────────────────────────────────┐
│   Client Layer  │    │                    Frontend Layer                        │
└─────────────────┘    └──────────────────────────────────────────────────────────┘
         │                                       │
         │ HTTP/HTMX                            │
         ▼                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Web Browser                                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│  │   Dashboard UI  │  │     Charts      │  │  AI Assistant   │                │
│  │   (TailwindCSS) │  │   (Chart.js)    │  │    (SA'ID)      │                │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                │
└─────────────────────────────────────────────────────────────────────────────────┘
         │                       │                        │
         │ HTMX Requests        │ Data Updates           │ Chat Requests
         ▼                       ▼                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            Django Application Server                            │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                          Application Layer                                  │ │
│  │                                                                             │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │ │
│  │  │   Dashboard     │  │   REST API      │  │   AI Engine     │            │ │
│  │  │   Views         │  │   (DRF)         │  │                 │            │ │
│  │  │                 │  │                 │  │  ┌─────────────┐│            │ │
│  │  │ • dashboard_view│  │ • /api/lorries/ │  │  │Local NLQ    ││            │ │
│  │  │ • aggregated_   │  │ • /api/trans... │  │  │(nlq.py)     ││            │ │
│  │  │   table         │  │ • /api/aggr...  │  │  └─────────────┘│            │ │
│  │  │ • dashboard_chat│  │                 │  │  ┌─────────────┐│            │ │
│  │  └─────────────────┘  └─────────────────┘  │  │Gemini AI    ││            │ │
│  │                                             │  │(gemini.py)  ││            │ │
│  │                                             │  └─────────────┘│            │ │
│  │                                             └─────────────────┘            │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                           Business Logic Layer                             │ │
│  │                                                                             │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │ │
│  │  │   Models        │  │   Utilities     │  │   AI Tools      │            │ │
│  │  │   (models.py)   │  │   (timeutils.py)│  │   (ai_tools.py) │            │ │
│  │  │                 │  │                 │  │                 │            │ │
│  │  │ • Lorry        │  │ • parse_delivery│  │ • list_collect..│            │ │
│  │  │ • Transaction  │  │   _time()       │  │ • describe_coll.│            │ │
│  │  │                 │  │ • get_window()  │  │ • totals_by_... │            │ │
│  │  │                 │  │ • trial windows │  │ • table_by_...  │            │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘            │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                           Data Access Layer                                │ │
│  │                                                                             │ │
│  │  ┌─────────────────┐  ┌─────────────────┐                                 │ │
│  │  │   Serializers   │  │   Djongo ORM    │                                 │ │
│  │  │ (serializers.py)│  │   (Database     │                                 │ │
│  │  │                 │  │    Abstraction) │                                 │ │
│  │  │ • LorrySerial.. │  │                 │                                 │ │
│  │  │ • TransactionS..│  │ • Model mapping │                                 │ │
│  │  └─────────────────┘  │ • Query builder │                                 │ │
│  │                       └─────────────────┘                                 │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
         │                                       │
         │ Database Queries                     │ External API Calls
         ▼                                       ▼
┌─────────────────────────────────────┐  ┌─────────────────────────────────────┐
│            MongoDB Atlas            │  │        Google Cloud Platform       │
│                                     │  │                                     │
│  ┌─────────────────┐                │  │  ┌─────────────────┐               │
│  │   Collections   │                │  │  │   Vertex AI     │               │
│  │                 │                │  │  │   (Gemini)      │               │
│  │ • deliveries    │                │  │  │                 │               │
│  │   (transactions)│                │  │  │ • Function      │               │
│  │ • lorries       │                │  │  │   Calling       │               │
│  │   (fleet data)  │                │  │  │ • NL Processing │               │
│  └─────────────────┘                │  │  └─────────────────┘               │
└─────────────────────────────────────┘  └─────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Static Assets                                     │
│                                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│  │   TailwindCSS   │  │     Images      │  │   JavaScript    │                │
│  │   (Compiled)    │  │   (Logos)       │  │   (Chart.js,    │                │
│  │                 │  │                 │  │    HTMX)        │                │
│  │ • styles.css    │  │ • mbsp.png      │  │                 │                │
│  │ • utilities     │  │ • gssb.png      │  │ • chart.min.js  │                │
│  └─────────────────┘  └─────────────────┘  │ • htmx.min.js   │                │
│                                             └─────────────────┘                │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. Presentation Layer
```
┌─────────────────────────────────────────────────────────────────┐
│                      Presentation Layer                        │
├─────────────────────────────────────────────────────────────────┤
│ Templates                │ Static Assets       │ Frontend Tech  │
├─────────────────────────────────────────────────────────────────┤
│ • index.html             │ • TailwindCSS       │ • HTMX         │
│ • _aggregated_table.html │ • Chart.js          │ • Chart.js     │
│                          │ • Logo images       │ • JavaScript   │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Application Layer
```
┌─────────────────────────────────────────────────────────────────┐
│                     Application Layer                          │
├─────────────────────────────────────────────────────────────────┤
│ Views Module (views.py)                                         │
├─────────────────────────────────────────────────────────────────┤
│ • dashboard_view()        → Main dashboard rendering            │
│ • aggregated_table()      → HTMX partial updates              │
│ • dashboard_chat()        → AI assistant interface            │
├─────────────────────────────────────────────────────────────────┤
│ API Views (REST Framework)                                     │
├─────────────────────────────────────────────────────────────────┤
│ • LorryViewSet           → Fleet data API                     │
│ • TransactionViewSet     → Transaction data API               │
│ • AggregatedDataAPIView  → Analytics API                      │
└─────────────────────────────────────────────────────────────────┘
```

### 3. AI Engine Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                        AI Engine                               │
├─────────────────────────────────────────────────────────────────┤
│ Entry Point: gemini.py                                         │
├─────────────────────────────────────────────────────────────────┤
│ • ask_gemini()           → Main AI interface                  │
│ • _vertex_available()    → Check Gemini availability          │
├─────────────────────────────────────────────────────────────────┤
│ Local NLQ Engine: nlq.py                                      │
├─────────────────────────────────────────────────────────────────┤
│ • process_nlq()          → Natural language processing        │
│ • Intent matching        → Route to appropriate tools         │
├─────────────────────────────────────────────────────────────────┤
│ AI Tools: ai_tools.py                                         │
├─────────────────────────────────────────────────────────────────┤
│ • list_collections()     → Database introspection            │
│ • describe_collection()  → Schema information                │
│ • totals_by_period()     → Aggregated metrics                │
│ • table_by_period()      → Tabular data                      │
│ • deliveries_by_type()   → Fleet analytics                   │
└─────────────────────────────────────────────────────────────────┘
```

### 4. Data Layer Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                        Data Layer                              │
├─────────────────────────────────────────────────────────────────┤
│ Models (models.py)                                             │
├─────────────────────────────────────────────────────────────────┤
│ • Lorry Model            → Fleet vehicle data                 │
│   - lorry_id (PK)        - types_id                          │
│   - client_id            - make_id                            │
│                                                                │
│ • Transaction Model      → Delivery transactions              │
│   - transaction_id       - lorry_id (FK)                     │
│   - weight               - delivery_time                      │
├─────────────────────────────────────────────────────────────────┤
│ Database Mapping (Djongo ORM)                                 │
├─────────────────────────────────────────────────────────────────┤
│ Django Models ←→ MongoDB Collections                           │
│ • Lorry       ←→ lorries                                      │
│ • Transaction ←→ deliveries                                   │
├─────────────────────────────────────────────────────────────────┤
│ Serializers (serializers.py)                                  │
├─────────────────────────────────────────────────────────────────┤
│ • LorrySerializer        → API data formatting               │
│ • TransactionSerializer  → Enhanced with computed fields     │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Architecture

### 1. Dashboard View Flow
```
User Request → Django URLs → dashboard_view() →
  ↓
MongoDB Query (via Djongo) → Data Aggregation →
  ↓
Template Rendering → HTML Response → Browser
```

### 2. HTMX Partial Update Flow
```
Period Change → HTMX Request → aggregated_table() →
  ↓
Data Re-aggregation → Partial Template →
  ↓
HTMX DOM Update → Chart Re-rendering
```

### 3. AI Assistant Flow
```
User Question → dashboard_chat() → ask_gemini() →
  ↓
┌─────────────────┐    ┌──────────────────┐
│ Vertex AI       │ or │ Local NLQ        │
│ (if configured) │    │ (fallback)       │
└─────────────────┘    └──────────────────┘
  ↓                      ↓
Google Cloud API      process_nlq() → ai_tools functions
  ↓                      ↓
AI Response ← ─ ─ ─ ─ ─ ─ ┘
  ↓
HTML Response → Chat Interface Update
```

### 4. API Data Flow
```
REST API Request → DRF ViewSet →
  ↓
Model Query → Serializer →
  ↓
JSON Response → External Consumers
```

## Key Design Patterns

### 1. **Repository Pattern** (via Django ORM/Djongo)
- Models abstract MongoDB collections
- ViewSets provide standardized data access
- Serializers handle data transformation

### 2. **Strategy Pattern** (AI Backend Selection)
- `ask_gemini()` chooses between Vertex AI and Local NLQ
- Graceful fallback mechanism
- Environment-based configuration

### 3. **Template Method Pattern** (Data Aggregation)
- `get_window()` provides period-based date ranges
- Consistent aggregation patterns across views
- Reusable time utility functions

### 4. **Facade Pattern** (AI Tools Interface)
- `ai_tools.py` provides simplified interface to complex operations
- Hides database query complexity
- Standardized function signatures for AI calling

## Technology Stack Details

### Backend Technologies
- **Django 3.2.25**: Web framework
- **Django REST Framework**: API development
- **Djongo 1.3.6**: MongoDB ORM adapter
- **PyMongo 3.12.3**: MongoDB driver

### Frontend Technologies
- **HTMX**: Dynamic page updates without JavaScript
- **TailwindCSS**: Utility-first CSS framework
- **Chart.js**: Data visualization
- **Vanilla JavaScript**: Chart rendering and interactions

### Database & AI
- **MongoDB Atlas**: Cloud database
- **Google Cloud Vertex AI**: Advanced AI capabilities
- **Local NLQ Engine**: Fallback natural language processing

### Development & Deployment
- **Python 3.x**: Runtime environment
- **Virtual Environment**: Dependency isolation
- **dotenv**: Environment configuration
- **Gunicorn**: Production server (configured)

## Security & Configuration

### Environment Variables
```
MONGO_DB_URL=mongodb+srv://user:pass@cluster/
MONGO_DB_NAME=mongodb_iswmc
GOOGLE_CLOUD_PROJECT=your-project-id
GEMINI_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

### Security Features
- Environment-based configuration
- No hardcoded credentials
- CSRF protection enabled
- MongoDB connection encryption

## Scalability Considerations

### Current Limitations
- Fixed trial window (Jan 2025)
- In-memory data joins (Python-side)
- Single-server deployment

### Scaling Strategies
- Add Redis for caching aggregated data
- Implement database-side aggregation
- Add load balancing for multiple Django instances
- Separate AI processing into microservice