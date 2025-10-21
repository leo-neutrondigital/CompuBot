# BASE DE DATOS - Esquema Completo
### Diseño de Base de Datos para Bot de Cotizaciones
### Stack: PostgreSQL + Supabase
### Fecha: 20 de octubre de 2025

---

## 🗄️ **ESQUEMA COMPLETO DE BASE DE DATOS**

### **Principios de Diseño:**
- ✅ **Normalización**: Evitar redundancia de datos
- ✅ **Performance**: Índices optimizados para consultas frecuentes
- ✅ **Escalabilidad**: Particionado futuro si es necesario
- ✅ **Auditabilidad**: Timestamps y logs de cambios
- ✅ **Integridad**: Constraints y foreign keys

---

## 📋 **TABLAS PRINCIPALES**

### **1. USUARIOS Y AUTENTICACIÓN**

```sql
-- Usuarios autorizados del sistema
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    role VARCHAR(20) DEFAULT 'employee' CHECK (role IN ('admin', 'manager', 'employee')),
    department VARCHAR(50),
    active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Sesiones activas (opcional, para control avanzado)
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    whatsapp_chat_id VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT now()
);

-- Índices para usuarios
CREATE INDEX idx_users_phone ON users(phone_number) WHERE active = true;
CREATE INDEX idx_users_role ON users(role, active);
CREATE INDEX idx_sessions_active ON user_sessions(user_id, is_active) WHERE is_active = true;
```

### **2. PRODUCTOS Y CATÁLOGO**

```sql
-- Productos sincronizados desde WooCommerce
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    woo_id INTEGER UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    short_description VARCHAR(500),
    price DECIMAL(10,2) NOT NULL,
    sale_price DECIMAL(10,2),
    regular_price DECIMAL(10,2),
    stock_quantity INTEGER DEFAULT 0,
    stock_status VARCHAR(20) DEFAULT 'instock' CHECK (stock_status IN ('instock', 'outofstock', 'onbackorder')),
    sku VARCHAR(100),
    category_id UUID REFERENCES product_categories(id),
    weight DECIMAL(8,2),
    dimensions JSONB, -- {length, width, height}
    image_url VARCHAR(500),
    permalink VARCHAR(500),
    tags TEXT[], -- Array de tags para búsqueda
    attributes JSONB, -- Atributos específicos del producto
    active BOOLEAN DEFAULT true,
    featured BOOLEAN DEFAULT false,
    last_sync TIMESTAMP DEFAULT now(),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Categorías de productos
CREATE TABLE product_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    woo_id INTEGER UNIQUE,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    parent_id UUID REFERENCES product_categories(id),
    description TEXT,
    image_url VARCHAR(500),
    count INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT now()
);

-- Sinónimos para búsqueda inteligente
CREATE TABLE product_synonyms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    synonym VARCHAR(100) NOT NULL,
    type VARCHAR(20) DEFAULT 'manual' CHECK (type IN ('manual', 'auto', 'user_generated')),
    confidence DECIMAL(3,2) DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT now()
);

-- Índices para productos
CREATE INDEX idx_products_search ON products USING GIN (to_tsvector('spanish', name || ' ' || coalesce(description, '') || ' ' || array_to_string(tags, ' ')));
CREATE INDEX idx_products_category ON products(category_id) WHERE active = true;
CREATE INDEX idx_products_price ON products(price) WHERE active = true;
CREATE INDEX idx_products_stock ON products(stock_status, stock_quantity) WHERE active = true;
CREATE INDEX idx_products_sku ON products(sku) WHERE sku IS NOT NULL;
CREATE INDEX idx_synonyms_lookup ON product_synonyms(synonym, product_id);
```

### **3. CONVERSACIONES Y ESTADOS**

```sql
-- Conversaciones activas y historial
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    whatsapp_chat_id VARCHAR(100) NOT NULL,
    whatsapp_message_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed', 'cancelled', 'timeout')),
    current_state VARCHAR(30) DEFAULT 'conversando' CHECK (current_state IN ('conversando', 'recopilando', 'validando', 'revisando', 'cotizando', 'finalizado')),
    intent_history JSONB DEFAULT '[]', -- Historial de intenciones detectadas
    context JSONB DEFAULT '{}', -- Estado actual de la conversación
    products_in_progress JSONB DEFAULT '[]', -- Productos siendo agregados
    conversation_summary TEXT, -- Resumen generado al finalizar
    total_messages INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT now(),
    last_activity TIMESTAMP DEFAULT now(),
    completed_at TIMESTAMP,
    timeout_at TIMESTAMP DEFAULT (now() + INTERVAL '2 hours')
);

-- Mensajes de conversación (para debugging y análisis)
CREATE TABLE conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    message_type VARCHAR(20) NOT NULL CHECK (message_type IN ('user', 'bot', 'system', 'webhook')),
    content TEXT NOT NULL,
    intent_detected VARCHAR(50),
    confidence DECIMAL(3,2),
    processing_time_ms INTEGER,
    metadata JSONB DEFAULT '{}', -- Datos adicionales (tokens, errores, etc.)
    whatsapp_message_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT now()
);

-- Estados de conversación (para análisis de flujos)
CREATE TABLE conversation_state_transitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    from_state VARCHAR(30),
    to_state VARCHAR(30) NOT NULL,
    trigger_intent VARCHAR(50),
    trigger_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT now()
);

-- Índices para conversaciones
CREATE INDEX idx_conversations_active ON conversations(user_id, status) WHERE status = 'active';
CREATE INDEX idx_conversations_activity ON conversations(last_activity DESC);
CREATE INDEX idx_conversations_timeout ON conversations(timeout_at) WHERE status = 'active';
CREATE INDEX idx_messages_conversation ON conversation_messages(conversation_id, created_at DESC);
CREATE INDEX idx_state_transitions ON conversation_state_transitions(conversation_id, created_at);
```

### **4. COTIZACIONES Y ITEMS**

```sql
-- Cotizaciones generadas
CREATE TABLE quotes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    user_id UUID REFERENCES users(id),
    quote_number VARCHAR(20) UNIQUE NOT NULL, -- Q2025-001234
    
    -- Datos del cliente (snapshot en el momento)
    client_info JSONB DEFAULT '{}', -- {name, company, email, phone}
    
    -- Cálculos financieros
    subtotal DECIMAL(12,2) NOT NULL,
    discount_percentage DECIMAL(5,2) DEFAULT 0,
    discount_amount DECIMAL(12,2) DEFAULT 0,
    tax_rate DECIMAL(5,2) DEFAULT 16.00,
    tax_amount DECIMAL(12,2) NOT NULL,
    shipping_cost DECIMAL(12,2) DEFAULT 0,
    total DECIMAL(12,2) NOT NULL,
    
    -- Archivos y documentos
    pdf_path VARCHAR(500),
    pdf_size_bytes INTEGER,
    
    -- Estado y fechas
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'sent', 'viewed', 'accepted', 'rejected', 'expired')),
    version INTEGER DEFAULT 1,
    valid_until TIMESTAMP DEFAULT (now() + INTERVAL '30 days'),
    
    -- Tracking
    view_count INTEGER DEFAULT 0,
    last_viewed TIMESTAMP,
    
    -- Notas y observaciones
    internal_notes TEXT,
    client_notes TEXT,
    
    created_at TIMESTAMP DEFAULT now(),
    sent_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT now()
);

-- Items de cada cotización
CREATE TABLE quote_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quote_id UUID REFERENCES quotes(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id),
    
    -- Snapshot del producto (por si cambia después)
    product_name VARCHAR(255) NOT NULL,
    product_sku VARCHAR(100),
    product_description TEXT,
    
    -- Cantidades y precios
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10,2) NOT NULL,
    discount_percentage DECIMAL(5,2) DEFAULT 0,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    total_price DECIMAL(12,2) NOT NULL,
    
    -- Orden en la cotización
    line_order INTEGER DEFAULT 1,
    
    created_at TIMESTAMP DEFAULT now()
);

-- Historial de versiones de cotizaciones
CREATE TABLE quote_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quote_id UUID REFERENCES quotes(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    changes_description TEXT,
    data_snapshot JSONB NOT NULL, -- Snapshot completo de la cotización
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT now()
);

-- Índices para cotizaciones
CREATE INDEX idx_quotes_user_date ON quotes(user_id, created_at DESC);
CREATE INDEX idx_quotes_status ON quotes(status, created_at DESC);
CREATE INDEX idx_quotes_number ON quotes(quote_number);
CREATE INDEX idx_quotes_expiration ON quotes(valid_until) WHERE status IN ('sent', 'viewed');
CREATE INDEX idx_quote_items_quote ON quote_items(quote_id, line_order);
CREATE INDEX idx_quote_items_product ON quote_items(product_id);
```

### **5. LOGS Y SINCRONIZACIÓN**

```sql
-- Log de sincronización con WooCommerce
CREATE TABLE sync_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sync_type VARCHAR(50) NOT NULL CHECK (sync_type IN ('products', 'categories', 'inventory', 'prices', 'full')),
    status VARCHAR(20) NOT NULL CHECK (status IN ('started', 'success', 'error', 'partial')),
    
    -- Estadísticas de la sincronización
    records_processed INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_created INTEGER DEFAULT 0,
    records_deleted INTEGER DEFAULT 0,
    
    -- Errores y detalles
    errors JSONB DEFAULT '[]',
    warnings JSONB DEFAULT '[]',
    summary TEXT,
    
    -- Timing
    started_at TIMESTAMP DEFAULT now(),
    completed_at TIMESTAMP,
    duration_seconds INTEGER
);

-- Log de errores del sistema
CREATE TABLE error_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    error_type VARCHAR(50) NOT NULL,
    error_code VARCHAR(20),
    message TEXT NOT NULL,
    stack_trace TEXT,
    
    -- Contexto del error
    user_id UUID REFERENCES users(id),
    conversation_id UUID REFERENCES conversations(id),
    endpoint VARCHAR(200),
    request_data JSONB,
    
    -- Severidad y estado
    severity VARCHAR(20) DEFAULT 'error' CHECK (severity IN ('debug', 'info', 'warning', 'error', 'critical')),
    resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP,
    resolved_by UUID REFERENCES users(id),
    
    created_at TIMESTAMP DEFAULT now()
);

-- Métricas y analytics
CREATE TABLE daily_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL UNIQUE,
    
    -- Métricas de conversaciones
    total_conversations INTEGER DEFAULT 0,
    completed_conversations INTEGER DEFAULT 0,
    abandoned_conversations INTEGER DEFAULT 0,
    avg_conversation_duration INTERVAL,
    
    -- Métricas de cotizaciones
    total_quotes INTEGER DEFAULT 0,
    total_quote_value DECIMAL(15,2) DEFAULT 0,
    avg_quote_value DECIMAL(12,2) DEFAULT 0,
    
    -- Métricas de productos
    most_quoted_products JSONB DEFAULT '[]',
    total_products_quoted INTEGER DEFAULT 0,
    
    -- Métricas técnicas
    avg_response_time_ms INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    uptime_percentage DECIMAL(5,2) DEFAULT 100.00,
    
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Índices para logs y métricas
CREATE INDEX idx_sync_logs_date ON sync_logs(started_at DESC);
CREATE INDEX idx_sync_logs_type_status ON sync_logs(sync_type, status);
CREATE INDEX idx_error_logs_date ON error_logs(created_at DESC);
CREATE INDEX idx_error_logs_severity ON error_logs(severity, resolved);
CREATE INDEX idx_daily_metrics_date ON daily_metrics(date DESC);
```

---

## 🔧 **FUNCIONES Y TRIGGERS**

### **Función para actualizar timestamps:**
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Aplicar a tablas que necesiten auto-update
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
CREATE TRIGGER update_quotes_updated_at BEFORE UPDATE ON quotes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### **Función para generar número de cotización:**
```sql
CREATE OR REPLACE FUNCTION generate_quote_number()
RETURNS TRIGGER AS $$
DECLARE
    year_suffix TEXT;
    next_number INTEGER;
    new_quote_number TEXT;
BEGIN
    -- Obtener año actual
    year_suffix := EXTRACT(YEAR FROM now())::TEXT;
    
    -- Obtener siguiente número secuencial
    SELECT COALESCE(MAX(CAST(SUBSTRING(quote_number FROM '\d+$') AS INTEGER)), 0) + 1
    INTO next_number
    FROM quotes
    WHERE quote_number LIKE 'Q' || year_suffix || '%';
    
    -- Generar nuevo número
    new_quote_number := 'Q' || year_suffix || '-' || LPAD(next_number::TEXT, 6, '0');
    
    NEW.quote_number := new_quote_number;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER generate_quote_number_trigger
    BEFORE INSERT ON quotes
    FOR EACH ROW
    WHEN (NEW.quote_number IS NULL)
    EXECUTE FUNCTION generate_quote_number();
```

### **Función para limpiar conversaciones expiradas:**
```sql
CREATE OR REPLACE FUNCTION cleanup_expired_conversations()
RETURNS INTEGER AS $$
DECLARE
    cleaned_count INTEGER;
BEGIN
    UPDATE conversations 
    SET status = 'timeout',
        completed_at = now()
    WHERE status = 'active' 
    AND timeout_at < now();
    
    GET DIAGNOSTICS cleaned_count = ROW_COUNT;
    
    RETURN cleaned_count;
END;
$$ language 'plpgsql';

-- Job programado para ejecutar cada hora
-- (Se configura en la aplicación o con pg_cron si está disponible)
```

---

## 📊 **VISTAS ÚTILES PARA ANALYTICS**

### **Vista de conversaciones activas:**
```sql
CREATE VIEW active_conversations_summary AS
SELECT 
    c.id,
    u.name as user_name,
    u.phone_number,
    c.current_state,
    c.total_messages,
    COUNT(q.id) as quotes_generated,
    c.started_at,
    c.last_activity,
    EXTRACT(EPOCH FROM (now() - c.started_at))/60 as duration_minutes
FROM conversations c
JOIN users u ON c.user_id = u.id
LEFT JOIN quotes q ON c.id = q.conversation_id
WHERE c.status = 'active'
GROUP BY c.id, u.name, u.phone_number, c.current_state, c.total_messages, c.started_at, c.last_activity
ORDER BY c.last_activity DESC;
```

### **Vista de productos más cotizados:**
```sql
CREATE VIEW popular_products AS
SELECT 
    p.id,
    p.name,
    p.sku,
    COUNT(qi.id) as times_quoted,
    SUM(qi.quantity) as total_quantity,
    SUM(qi.total_price) as total_value,
    AVG(qi.unit_price) as avg_price,
    MAX(q.created_at) as last_quoted
FROM products p
JOIN quote_items qi ON p.id = qi.product_id
JOIN quotes q ON qi.quote_id = q.id
WHERE q.created_at >= (now() - INTERVAL '30 days')
GROUP BY p.id, p.name, p.sku
ORDER BY times_quoted DESC, total_value DESC;
```

### **Vista de rendimiento de usuarios:**
```sql
CREATE VIEW user_performance AS
SELECT 
    u.id,
    u.name,
    u.phone_number,
    COUNT(DISTINCT c.id) as total_conversations,
    COUNT(q.id) as total_quotes,
    SUM(q.total) as total_quote_value,
    AVG(q.total) as avg_quote_value,
    COUNT(q.id) FILTER (WHERE q.status = 'accepted') as accepted_quotes
FROM users u
LEFT JOIN conversations c ON u.id = c.user_id
LEFT JOIN quotes q ON c.id = q.conversation_id
WHERE c.created_at >= (now() - INTERVAL '30 days')
GROUP BY u.id, u.name, u.phone_number
ORDER BY total_quote_value DESC NULLS LAST;
```

---

## 🚀 **SETUP INICIAL DE BASE DE DATOS**

### **Script de inicialización:**
```sql
-- setup.sql
-- Ejecutar después de crear la base de datos

-- 1. Habilitar extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- Para búsqueda fuzzy

-- 2. Crear schema para desarrollo
CREATE SCHEMA IF NOT EXISTS computel_bot;
SET search_path TO computel_bot, public;

-- 3. Ejecutar todas las tablas (en orden de dependencias)
-- [Copiar aquí todas las CREATE TABLE statements]

-- 4. Insertar datos iniciales
INSERT INTO users (phone_number, name, role) VALUES
('5551234567', 'Admin Usuario', 'admin'),
('5557654321', 'Manager Test', 'manager');

INSERT INTO product_categories (name, slug) VALUES
('Papelería', 'papeleria'),
('Oficina', 'oficina'),
('Escolar', 'escolar');

-- 5. Configurar permisos (si es necesario)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA computel_bot TO [app_user];
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA computel_bot TO [app_user];
```

### **Alembic migrations (para desarrollo):**
```python
# alembic/versions/001_initial_schema.py
"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2025-10-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Crear todas las tablas
    # [SQL statements para crear tablas]
    pass

def downgrade():
    # Eliminar tablas en orden reverso
    # [SQL statements para eliminar]
    pass
```

---

## 💾 **BACKUP Y MANTENIMIENTO**

### **Estrategia de backup:**
```sql
-- Backup diario (configurar en cron)
pg_dump -h localhost -U user -d computel_bot --format=custom --file=backup_$(date +%Y%m%d).dump

-- Backup solo datos críticos
pg_dump -h localhost -U user -d computel_bot --table=users --table=quotes --table=quote_items --data-only
```

### **Mantenimiento automático:**
```sql
-- Limpiar logs antiguos (ejecutar semanalmente)
DELETE FROM error_logs WHERE created_at < (now() - INTERVAL '90 days');
DELETE FROM conversation_messages WHERE created_at < (now() - INTERVAL '60 days');

-- Actualizar estadísticas
ANALYZE;

-- Reindexar si es necesario
REINDEX DATABASE computel_bot;
```

---

*Documento actualizado: 20 de octubre de 2025*
*Versión: 1.0*