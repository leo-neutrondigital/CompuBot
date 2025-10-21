# ARQUITECTURA MODULAR - Bot de Cotizaciones
### Diseño de Módulos y Componentes
### Fecha: 20 de octubre de 2025

---

## 🏗️ **PRINCIPIOS DE ARQUITECTURA MODULAR**

### **Objetivos del Diseño:**
- ✅ **Escalabilidad**: Cada módulo puede crecer independientemente
- ✅ **Mantenibilidad**: Código organizado y fácil de debuggear
- ✅ **Reutilización**: Componentes que sirven para múltiples casos
- ✅ **Testabilidad**: Módulos aislados fáciles de probar
- ✅ **Desacoplamiento**: Dependencias mínimas entre módulos

---

## 📁 **ESTRUCTURA DETALLADA DE MÓDULOS**

### **1. CORE - Fundación del Sistema**
```python
app/core/
├── config.py           # Configuración centralizada
├── database.py         # Conexión y sesiones BD
├── security.py         # Autenticación y tokens
├── exceptions.py       # Excepciones personalizadas
├── dependencies.py     # Dependencias FastAPI
└── middleware.py       # Middleware personalizado
```

**Responsabilidades:**
- Gestión de configuración de entorno
- Conexiones a base de datos
- Autenticación y autorización
- Manejo centralizado de errores
- Middleware de logging y monitoreo

### **2. FEATURES - Módulos Funcionales**

#### **2.1 Auth Module**
```python
app/features/auth/
├── __init__.py
├── models.py           # User, Permission models
├── schemas.py          # Pydantic schemas
├── service.py          # Lógica de autenticación
├── repository.py       # Acceso a datos
└── router.py           # Endpoints API
```

**Funcionalidades:**
- Validación número telefónico
- Gestión de usuarios registrados
- Permisos y roles
- Sesiones de usuarios

#### **2.2 Conversation Module**
```python
app/features/conversation/
├── __init__.py
├── models.py           # Conversation, Message models
├── schemas.py          # Schemas de conversación
├── engine.py           # Motor conversacional principal
├── states.py           # Estados y transiciones
├── intents.py          # Detección de intenciones
├── memory.py           # Memoria y contexto
├── service.py          # Lógica de negocio
├── repository.py       # Persistencia
└── router.py           # API endpoints
```

**Componentes Clave:**
```python
# engine.py - Motor principal
class ConversationEngine:
    def __init__(self):
        self.state_manager = StateManager()
        self.intent_detector = IntentDetector()
        self.memory_manager = MemoryManager()
        
    async def process_message(self, user_id, message):
        # 1. Detectar intención
        intent = await self.intent_detector.analyze(message)
        
        # 2. Obtener contexto
        context = await self.memory_manager.get_context(user_id)
        
        # 3. Procesar según estado actual
        response = await self.state_manager.handle(intent, context)
        
        # 4. Actualizar memoria
        await self.memory_manager.update(user_id, response)
        
        return response

# states.py - Gestión de estados
class StateManager:
    STATES = {
        'conversando': ConversandoState(),
        'recopilando': RecopilandoState(),
        'validando': ValidandoState(),
        'cotizando': CotizandoState()
    }
    
    async def transition_to(self, new_state, context):
        # Lógica de transición entre estados
        pass

# intents.py - Detección de intenciones
class IntentDetector:
    async def analyze(self, message, context=None):
        # Usar OpenAI para detectar intención
        # Clasificar: AGREGAR, MODIFICAR, COTIZAR, etc.
        pass
```

#### **2.3 Products Module**
```python
app/features/products/
├── __init__.py
├── models.py           # Product model
├── schemas.py          # Product schemas
├── search.py           # Motor de búsqueda
├── validator.py        # Validación productos
├── service.py          # Lógica de negocio
├── repository.py       # Acceso a datos
└── router.py           # API endpoints
```

**Funcionalidades:**
```python
# search.py - Búsqueda inteligente
class ProductSearchEngine:
    def __init__(self):
        self.fuzzy_matcher = FuzzyMatcher()
        self.category_matcher = CategoryMatcher()
        
    async def search(self, query, filters=None):
        # 1. Búsqueda exacta
        exact_matches = await self.exact_search(query)
        
        # 2. Búsqueda fuzzy
        fuzzy_matches = await self.fuzzy_search(query)
        
        # 3. Búsqueda por categoría
        category_matches = await self.category_search(query)
        
        return self.rank_results(exact_matches, fuzzy_matches, category_matches)

# validator.py - Validación contra catálogo
class ProductValidator:
    async def validate_product_list(self, products):
        # Validar que todos los productos existan
        # Verificar disponibilidad
        # Sugerir alternativas si no están disponibles
        pass
```

#### **2.4 Quotes Module**
```python
app/features/quotes/
├── __init__.py
├── models.py           # Quote, QuoteItem models
├── schemas.py          # Quote schemas
├── calculator.py       # Cálculos de precios
├── generator.py        # Generación de cotizaciones
├── service.py          # Lógica de negocio
├── repository.py       # Persistencia
└── router.py           # API endpoints
```

**Componentes:**
```python
# calculator.py - Cálculos
class QuoteCalculator:
    def __init__(self):
        self.tax_rate = 0.16  # 16% IVA
        self.shipping_calculator = ShippingCalculator()
        
    def calculate_totals(self, items):
        subtotal = sum(item.quantity * item.unit_price for item in items)
        tax_amount = subtotal * self.tax_rate
        shipping = self.shipping_calculator.calculate(items)
        total = subtotal + tax_amount + shipping
        
        return {
            'subtotal': subtotal,
            'tax_amount': tax_amount,
            'shipping': shipping,
            'total': total
        }

# generator.py - Generación
class QuoteGenerator:
    def __init__(self):
        self.pdf_service = PDFService()
        self.template_service = TemplateService()
        
    async def generate_quote(self, quote_data):
        # 1. Preparar datos
        template_data = await self.prepare_template_data(quote_data)
        
        # 2. Generar PDF
        pdf_path = await self.pdf_service.generate(template_data)
        
        # 3. Guardar en BD
        await self.save_quote(quote_data, pdf_path)
        
        return pdf_path
```

#### **2.5 WooCommerce Module**
```python
app/features/woocommerce/
├── __init__.py
├── client.py           # Cliente API WooCommerce
├── sync.py             # Sincronización de datos
├── mapper.py           # Mapeo datos WC → BD local
├── service.py          # Lógica de sincronización
└── scheduler.py        # Jobs automáticos
```

### **3. SERVICES - Servicios Externos**

#### **3.1 OpenAI Service**
```python
app/services/openai_service.py

class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.prompts = PromptsManager()
        
    async def chat_completion(self, messages, context=None):
        # Inyectar contexto del catálogo
        enhanced_messages = self.prompts.inject_context(messages, context)
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=enhanced_messages,
            temperature=0.7
        )
        
        return self.parse_response(response)
    
    async def detect_intent(self, message, context):
        # Prompt específico para detección de intenciones
        pass
    
    async def validate_response(self, response, available_products):
        # Validar que no se inventen productos
        pass
```

#### **3.2 WhatsApp Service**
```python
app/services/whatsapp_service.py

class WhatsAppService:
    def __init__(self):
        self.base_url = settings.WHATSAPP_API_URL
        self.token = settings.WHATSAPP_TOKEN
        
    async def send_message(self, to, message):
        # Enviar mensaje de texto
        pass
    
    async def send_document(self, to, file_path, caption=None):
        # Enviar PDF de cotización
        pass
    
    async def process_webhook(self, webhook_data):
        # Procesar mensaje entrante
        pass
```

#### **3.3 PDF Service**
```python
app/services/pdf_service.py

class PDFService:
    def __init__(self):
        self.template_dir = "templates/pdf/"
        
    async def generate_quote_pdf(self, quote_data):
        # Generar PDF usando ReportLab
        # Template profesional con logo, datos empresa
        pass
```

### **4. MODELS - Modelos de Datos**
```python
app/models/
├── __init__.py
├── base.py             # Modelo base con timestamps
├── user.py             # Usuario
├── product.py          # Producto
├── conversation.py     # Conversación
├── quote.py            # Cotización
└── message.py          # Mensaje
```

### **5. API - Endpoints**
```python
app/api/
├── __init__.py
├── webhooks/
│   └── whatsapp.py     # Webhook WhatsApp
├── admin/
│   ├── dashboard.py    # Dashboard endpoints
│   ├── users.py        # Gestión usuarios
│   └── quotes.py       # Gestión cotizaciones
└── internal/
    ├── sync.py         # Endpoints sincronización
    └── health.py       # Health checks
```

---

## 🔗 **FLUJO DE DATOS ENTRE MÓDULOS**

### **Proceso de Mensaje WhatsApp:**
```
1. WhatsApp → Webhook → WhatsApp Service
2. WhatsApp Service → Auth Module (validar usuario)
3. Auth Module → Conversation Engine
4. Conversation Engine → Intent Detector
5. Intent Detector → Products Module (si necesita productos)
6. Products Module → Quote Module (si va a cotizar)
7. Quote Module → PDF Service
8. PDF Service → WhatsApp Service (enviar cotización)
```

### **Sincronización WooCommerce:**
```
1. Scheduler → WooCommerce Service
2. WooCommerce Service → WooCommerce Client
3. WooCommerce Client → Mapper (transformar datos)
4. Mapper → Products Repository
5. Products Repository → Database
```

---

## 🧪 **ESTRATEGIA DE TESTING**

### **Pruebas por Módulo:**
```python
tests/
├── unit/
│   ├── test_auth/
│   ├── test_conversation/
│   ├── test_products/
│   ├── test_quotes/
│   └── test_services/
├── integration/
│   ├── test_conversation_flow.py
│   ├── test_quote_generation.py
│   └── test_woocommerce_sync.py
└── e2e/
    └── test_complete_workflow.py
```

### **Mocks y Fixtures:**
```python
# conftest.py
@pytest.fixture
def mock_openai():
    with patch('app.services.openai_service.OpenAI') as mock:
        yield mock

@pytest.fixture
def mock_whatsapp():
    with patch('app.services.whatsapp_service.WhatsAppService') as mock:
        yield mock

@pytest.fixture
def sample_products():
    return [
        Product(name="Papel Bond A4", price=2.50),
        Product(name="Lápiz #2", price=0.50)
    ]
```

---

## 📊 **MONITOREO Y LOGS**

### **Logging por Módulo:**
```python
import logging

# Configuración por módulo
logger = logging.getLogger(__name__)

class ConversationEngine:
    async def process_message(self, user_id, message):
        logger.info(f"Processing message for user {user_id}")
        
        try:
            result = await self._process(message)
            logger.info(f"Message processed successfully: {result.intent}")
            return result
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise
```

### **Métricas por Módulo:**
- **Auth**: Intentos de login, usuarios bloqueados
- **Conversation**: Tiempo por conversación, intenciones detectadas
- **Products**: Búsquedas, productos no encontrados
- **Quotes**: Cotizaciones generadas, errores en PDF

---

## 🚀 **DESPLIEGUE MODULAR**

### **Estructura de Deployment:**
```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./uploads:/app/uploads
      
  worker:
    build: .
    command: python -m app.workers.sync_worker
    
  scheduler:
    build: .
    command: python -m app.workers.scheduler
```

### **Variables por Módulo:**
```env
# Core
DATABASE_URL=
SECRET_KEY=

# Auth
JWT_SECRET_KEY=
JWT_ALGORITHM=HS256

# OpenAI
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4

# WhatsApp
WHATSAPP_TOKEN=
WHATSAPP_VERIFY_TOKEN=

# WooCommerce
WOOCOMMERCE_URL=
WOOCOMMERCE_KEY=
WOOCOMMERCE_SECRET=
```

---

## 🔧 **CONFIGURACIÓN DE DESARROLLO**

### **Setup Inicial:**
```bash
# 1. Clonar y configurar
git clone [repo]
cd computel_bot
python -m venv venv
source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 3. Configurar BD
alembic upgrade head

# 4. Variables de entorno
cp .env.example .env
# Editar .env con tus valores

# 5. Ejecutar
uvicorn app.main:app --reload
```

### **Comandos Útiles:**
```bash
# Testing
pytest tests/ -v

# Linting
black app/
flake8 app/

# Migraciones
alembic revision --autogenerate -m "descripción"
alembic upgrade head

# Sincronización manual
python -m app.scripts.sync_products
```

---

*Documento actualizado: 20 de octubre de 2025*
*Versión: 1.0*