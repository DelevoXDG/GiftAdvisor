# List of Design Patterns Used in the Project

---

### 1. **Active Record**
- **Files**:  
  - [`core/models.py`](../core/models.py) (classes: `GiftIdea`, `Recipient`, `PurchaseRecord`)
- **Rationale & Benefits**:  
  - Directly maps domain objects to database tables (e.g., `GiftIdea` ↔ `core_giftidea` table).
  - Simplifies CRUD operations via Django ORM, reducing boilerplate code.

---

### 2. **Service Layer**
- **Classes**:
  - [`AIProcessor`](../core/services/ai_processor.py)
- **Rationale & Benefits**:  
  - Decouples business logic from views and other layers.
  - Allows swapping implementations (e.g., changing AI providers) without modifying higher layers.
---

### 3. **Mapper**
- **Files**:  
  - [`core/services/ai_processor.py`](../core/services/ai_processor.py) (`AIProcessor` class)
  - [`core/services/metadata_extractor.py`](../core/services/metadata_extractor.py) (`MetadataExtractor` class)
- **Rationale & Benefits**:  
  - Converts data between formats (e.g., external API responses to structured JSON).
  - Encapsulates transformation logic, keeping core logic cleaner and reusable.

---

### 4. **Template View**
- **Files**:  
  - [`core/views.py`](../core/views.py) (`IndexView`, `RecipientsView`)  
  - HTML templates (e.g., [`templates/dashboard.html`](../templates/dashboard.html))  
- **Rationale & Benefits**:  
  - Combines templates with dynamic data passed via `context`.
  - Separates presentation logic from business logic, improving maintainability.

---

### 5. **Registry**
- **Files**:  
  - [`core/admin.py`](../core/admin.py) (`GiftIdeaAdmin`, `RecipientAdmin`, etc.)
- **Rationale & Benefits**:  
  - Centralizes model registration in Django Admin (e.g., `@admin.register(Tag)`).

---

### 6. **Lazy Loading**
- **Files**:  
  - [`templates/dashboard.html`](../templates/dashboard.html)
  - [`templates/gift_detail.html`](../templates/gift_detail.html)
  - [`templates/recipient_profile.html`](../templates/recipient_profile.html)
- **Rationale & Benefits**:  
  - Defers loading of off-screen images (using `loading="lazy"`).
  - Improves page load performance and reduces bandwidth usage.

---

### 7. **Database Session State**
- **Files**:  
  - [`config/settings.py`](../config/settings.py)
  - [`core/views.py`](../core/views.py)
- **Rationale & Benefits**:  
  - Stores session data securely in the database.
  - Ensures session data is persistent across server restarts.

---

### 8. **Client Session State**
- **Files**:  
  - [`templates/index.html`](../templates/index.html)
  - [`static/js/dashboard.js`](../static/js/dashboard.js)
- **Rationale & Benefits**:  
  - Stores certain state information (e.g., filter preferences) on the client side.
  - Improves performance by reducing unnecessary server requests.

---

### 9. **Unit of Work**
- **Classes**:  
  - [`PurchaseRecord`](../core/models.py)
- **Rationale & Benefits**:  
  - Ensures multiple database changes occur together or not at all.
  - Prevents half-finished operations during failures.

---

### 10. **Query Object**
- **Files**:  
  - [`core/views.py`](../core/views.py)
- **Classes**:  
  - TODO: Add classes  
- **Rationale & Benefits**:  
  - Encapsulates complex queries into reusable objects.
  - Simplifies search logic while keeping queries efficient.

---

### 11. **Layer Supertype**
- **Files**:  
  - [`core/views.py`](../core/views.py)
  - [`core/models.py`](../core/models.py)
- **Classes**:  
  - [`IndexView`](../core/views.py), [`GiftIdea`](../core/models.py), etc.
- **Rationale & Benefits**:  
  - Provides shared behavior for views (auth, rendering) and models (CRUD operations).
  - Reduces code duplication by defining common functionality in superclasses.

---

### 12. **Identity Field**
- **Files**:  
  - [`core/models.py`](../core/models.py)
- **Classes**:  
  - [`GiftIdea`](../core/models.py), [`Recipient`](../core/models.py)
- **Rationale & Benefits**:  
  - Supports linking objects (e.g., in URLs) seamlessly.
  - Allows for easy implementation of endpoints that require an ID.

---
