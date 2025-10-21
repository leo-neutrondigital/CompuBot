# PLAN DE DESARROLLO - Bot de Cotizaciones IA
### Proyecto: Bot WhatsApp para Papelería con IA
### Stack: Python + FastAPI + Supabase + Render
### Fecha: 20 de octubre de 2025

---

## 📋 **RESUMEN EJECUTIVO**

Bot de inteligencia artificial para generar cotizaciones de papelería a través de WhatsApp, con conversaciones naturales, validación de productos contra WooCommerce y generación automática de PDFs.

### **Objetivos Principales:**
- ✅ Automatizar proceso de cotizaciones
- ✅ Reducir tiempo de respuesta a clientes
- ✅ Mantener conversaciones naturales y fluidas
- ✅ Validar productos contra inventario real
- ✅ Generar cotizaciones profesionales en PDF

---

## 🏗️ **ARQUITECTURA MODULAR**

### **Estructura del Proyecto:**
```
computel_bot/
├── app/
│   ├── core/                    # Configuración base
│   │   ├── config.py           # Variables de entorno
│   │   ├── database.py         # Conexión BD
│   │   └── security.py         # Autenticación
│   │
│   ├── features/               # Módulos funcionales
│   │   ├── auth/              # Autenticación usuarios
│   │   ├── conversation/      # Motor conversacional
│   │   ├── products/          # Gestión productos
│   │   ├── quotes/            # Cotizaciones
│   │   └── woocommerce/       # Integración WooCommerce
│   │
│   ├── services/              # Servicios externos
│   │   ├── openai_service.py  # ChatGPT API
│   │   ├── whatsapp_service.py # WhatsApp API
│   │   ├── pdf_service.py     # Generación PDF
│   │   └── cache_service.py   # Cache inteligente
│   │
│   ├── models/                # Modelos de datos
│   │   ├── user.py
│   │   ├── product.py
│   │   ├── conversation.py
│   │   └── quote.py
│   │
│   ├── api/                   # Endpoints API
│   │   ├── webhooks/          # WhatsApp webhooks
│   │   ├── admin/             # Panel administración
│   │   └── internal/          # APIs internas
│   │
│   └── utils/                 # Utilidades
│       ├── validators.py
│       ├── formatters.py
│       └── helpers.py
│
├── docs/                      # Documentación
├── tests/                     # Pruebas automatizadas
├── migrations/                # Migraciones BD
└── requirements.txt           # Dependencias
```

---

## 🎯 **DESARROLLO POR FASES**

## **FASE 1 - MVP INICIAL (3-4 semanas)**
*Objetivo: Bot funcional para smalltalk y cotizaciones básicas*

### **Week 1: Infraestructura Base**
- [x] **Configuración del proyecto Python + FastAPI**
- [x] **Conexión Supabase (PostgreSQL)**
- [x] **Webhook básico WhatsApp (recibir/enviar)**
- [x] **Integración inicial OpenAI ChatGPT**
- [x] **Sistema de autenticación por número telefónico**

### **Week 2: Motor Conversacional**
- [x] **Sistema de estados conversacionales**
- [x] **Detección de intenciones básica**
- [x] **Smalltalk controlado**
- [x] **Manejo de sesiones temporales**

### **Week 3: Productos y WooCommerce**
- [x] **Conexión API WooCommerce**
- [x] **Sincronización productos a BD local**
- [x] **Búsqueda y validación productos**
- [x] **Cache inteligente de consultas**

### **Week 4: Cotizaciones**
- [x] **Recopilación de productos en conversación**
- [x] **Cálculos básicos (subtotal + impuestos)**
- [x] **Generación PDF simple**
- [x] **Envío cotización por WhatsApp**

### **Entregables MVP:**
✅ Bot que autentica usuarios registrados  
✅ Conversación natural para recopilar productos  
✅ Validación contra catálogo WooCommerce  
✅ Generación cotización PDF básica  
✅ Envío automático por WhatsApp  

---

## **FASE 2 - MEJORAS CONVERSACIONALES (3-4 semanas)**
*Objetivo: Conversaciones más inteligentes y robustas*

### **Funcionalidades:**
- 🔄 **Sistema de interrupciones naturales**
- 🧠 **Memoria de conversaciones anteriores**
- 🔍 **Búsqueda fuzzy avanzada de productos**
- 📊 **Dashboard básico de métricas**
- ⚡ **Optimización de performance**
- 🛡️ **Manejo robusto de errores**

---

## **FASE 3 - ANALYTICS Y ADMINISTRACIÓN (4-5 semanas)**
*Objetivo: Panel de control y análisis avanzado*

### **Funcionalidades:**
- 📈 **Dashboard completo con KPIs**
- 👥 **Gestión de usuarios y permisos**
- 🔔 **Sistema de notificaciones**
- 📋 **Historial de cotizaciones**
- 🎯 **Análisis de conversiones**
- 🔧 **Configuración avanzada del bot**

---

## 🗄️ **ESQUEMA DE BASE DE DATOS**

### **Tablas Principales:**

```sql
-- Usuarios autorizados
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(20) DEFAULT 'employee',
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Productos sincronizados de WooCommerce
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    woo_id INTEGER UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock_quantity INTEGER DEFAULT 0,
    category VARCHAR(100),
    sku VARCHAR(100),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    
    -- Índices para búsqueda rápida
    CONSTRAINT products_name_idx GIN (to_tsvector('spanish', name)),
    CONSTRAINT products_sku_idx BTREE (sku)
);

-- Conversaciones activas
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    whatsapp_chat_id VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'active', -- active, paused, completed, cancelled
    current_state VARCHAR(30) DEFAULT 'conversando',
    context JSONB DEFAULT '{}',
    started_at TIMESTAMP DEFAULT now(),
    last_activity TIMESTAMP DEFAULT now(),
    completed_at TIMESTAMP
);

-- Cotizaciones generadas
CREATE TABLE quotes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    user_id UUID REFERENCES users(id),
    quote_number VARCHAR(20) UNIQUE NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    tax_rate DECIMAL(5,2) DEFAULT 16.00,
    tax_amount DECIMAL(10,2) NOT NULL,
    shipping_cost DECIMAL(10,2) DEFAULT 0,
    total DECIMAL(10,2) NOT NULL,
    pdf_path VARCHAR(255),
    status VARCHAR(20) DEFAULT 'draft', -- draft, sent, viewed, expired
    valid_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT now(),
    sent_at TIMESTAMP
);

-- Items de cada cotización
CREATE TABLE quote_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quote_id UUID REFERENCES quotes(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id),
    product_name VARCHAR(255) NOT NULL, -- Snapshot del nombre
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);

-- Historial de mensajes (opcional, para debugging)
CREATE TABLE conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    message_type VARCHAR(20) NOT NULL, -- user, bot, system
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT now()
);

-- Log de sincronización WooCommerce
CREATE TABLE sync_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sync_type VARCHAR(50) NOT NULL, -- products, inventory
    status VARCHAR(20) NOT NULL, -- success, error, partial
    records_processed INTEGER DEFAULT 0,
    errors JSONB DEFAULT '[]',
    started_at TIMESTAMP DEFAULT now(),
    completed_at TIMESTAMP
);
```

### **Índices para Performance:**

```sql
-- Búsqueda rápida de productos
CREATE INDEX idx_products_search ON products USING GIN (to_tsvector('spanish', name || ' ' || description));
CREATE INDEX idx_products_category ON products(category) WHERE active = true;
CREATE INDEX idx_products_price ON products(price) WHERE active = true;

-- Conversaciones activas
CREATE INDEX idx_conversations_active ON conversations(user_id, status) WHERE status = 'active';
CREATE INDEX idx_conversations_activity ON conversations(last_activity DESC);

-- Cotizaciones por usuario y fecha
CREATE INDEX idx_quotes_user_date ON quotes(user_id, created_at DESC);
CREATE INDEX idx_quotes_status ON quotes(status, created_at DESC);
```

---

## ⚙️ **STACK TECNOLÓGICO DETALLADO**

### **Backend:**
- **Python 3.11+** (Lenguaje principal)
- **FastAPI** (Framework web)
- **SQLAlchemy** (ORM)
- **Alembic** (Migraciones BD)
- **Pydantic** (Validación datos)

### **Base de Datos:**
- **Supabase** (PostgreSQL managed)
- **Redis** (Cache - si necesario en Fase 2)

### **Servicios Externos:**
- **OpenAI GPT-4** (Motor conversacional)
- **WhatsApp Business API** (META)
- **WooCommerce REST API** (Productos)

### **Hosting y Deploy:**
- **Render** (Backend hosting)
- **GitHub Actions** (CI/CD)
- **Supabase** (Base de datos)

### **Librerías Clave:**
```python
# requirements.txt
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
pydantic==2.5.0
supabase==2.0.0
openai==1.3.0
requests==2.31.0
reportlab==4.0.7        # Generación PDF
python-multipart==0.0.6 # Form data
python-jose[cryptography]==3.3.0  # JWT tokens
passlib[bcrypt]==1.7.4   # Hash passwords
fuzzywuzzy==0.18.0       # Búsqueda fuzzy
python-levenshtein==0.23.0  # Distancia strings
```

---

## 🚀 **PLAN DE IMPLEMENTACIÓN MVP**

### **Tareas Prioritarias (Semana 1):**

1. **Setup Inicial del Proyecto**
   ```bash
   mkdir computel_bot
   cd computel_bot
   python -m venv venv
   source venv/bin/activate
   pip install fastapi uvicorn sqlalchemy alembic
   ```

2. **Configuración Supabase**
   - Crear proyecto en Supabase
   - Configurar variables de entorno
   - Setup inicial de tablas

3. **Webhook WhatsApp Básico**
   - Endpoint para recibir mensajes
   - Validación tokens META
   - Respuesta básica

4. **Integración OpenAI**
   - Cliente API ChatGPT
   - Prompts iniciales
   - Manejo de respuestas

### **Configuración de Entorno:**

```env
# .env
DATABASE_URL=postgresql://[user]:[password]@[host]:[port]/[database]
OPENAI_API_KEY=sk-...
WHATSAPP_TOKEN=...
WHATSAPP_VERIFY_TOKEN=...
WOOCOMMERCE_URL=https://tutienda.com
WOOCOMMERCE_KEY=ck_...
WOOCOMMERCE_SECRET=cs_...
ENVIRONMENT=development
```

---

## 📊 **MÉTRICAS Y KPIs**

### **MVP (Fase 1):**
- ✅ Usuarios autenticados correctamente
- ✅ Tiempo respuesta < 3 segundos
- ✅ Cotizaciones generadas exitosamente
- ✅ Uptime > 95%

### **Fase 2:**
- 📈 Tiempo promedio de conversación
- 📈 Productos agregados vs removidos
- 📈 Tasa de abandono en conversaciones
- 📈 Precisión en búsqueda de productos

### **Fase 3:**
- 🎯 Conversión cotización → venta
- 🎯 Satisfacción del usuario
- 🎯 Volumen de cotizaciones por día
- 🎯 ROI del bot vs proceso manual

---

## 🔒 **CONSIDERACIONES DE SEGURIDAD**

- ✅ Autenticación por número telefónico
- ✅ Validación de webhooks META
- ✅ Rate limiting en APIs
- ✅ Sanitización de inputs
- ✅ Logs de auditoría
- ✅ Variables sensibles en entorno

---

## 💰 **ESTIMACIÓN DE COSTOS**

### **MVP (mensual):**
- Supabase: $0 (tier gratuito)
- Render: $0 (tier gratuito inicial)
- OpenAI: $20-50 (según uso)
- WhatsApp: $0 (primeros 1000 mensajes)
- **Total: $20-50/mes**

### **Producción (mensual):**
- Supabase Pro: $25
- Render Pro: $25
- OpenAI: $100-200
- WhatsApp: $10-30
- **Total: $160-280/mes**

---

## 📅 **CRONOGRAMA DETALLADO**

### **Noviembre 2025:**
- Semana 1-2: MVP infraestructura + webhook
- Semana 3-4: Motor conversacional + productos

### **Diciembre 2025:**
- Semana 1-2: Cotizaciones + PDF
- Semana 3-4: Testing + mejoras MVP

### **Enero 2026:**
- Fase 2: Conversaciones avanzadas

### **Febrero 2026:**
- Fase 3: Dashboard + analytics

---

## 🎯 **CRITERIOS DE ÉXITO MVP**

✅ **Funcional:**
- Bot responde 24/7 sin intervención
- Genera cotizaciones precisas en < 5 min
- Valida productos contra WooCommerce
- PDF professional y completo

✅ **Técnico:**
- 0 downtime durante horario laboral
- < 3 segundos tiempo respuesta
- 100% mensajes WhatsApp procesados
- Base de datos consistente

✅ **Negocio:**
- Reduce 70% tiempo manual cotizaciones
- Aumenta satisfacción cliente
- Elimina errores en productos/precios
- Facilita seguimiento de solicitudes

---

*Documento actualizado: 20 de octubre de 2025*
*Versión: 1.0*
*Autor: Equipo de Desarrollo*