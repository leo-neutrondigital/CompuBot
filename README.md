# README - Bot de Cotizaciones IA
### Sistema de Cotizaciones Inteligente para Papelería
### Stack: Python + FastAPI + Supabase + WhatsApp

---

## 🎯 **Descripción del Proyecto**

Bot de inteligencia artificial que automatiza el proceso de cotizaciones para una empresa de papelería a través de WhatsApp. Utiliza conversaciones naturales para recopilar productos, valida contra inventario de WooCommerce y genera cotizaciones profesionales en PDF.

### **Características Principales:**
- 🤖 Conversación natural con ChatGPT-4
- 📱 Integración completa con WhatsApp Business
- 🛒 Sincronización automática con WooCommerce
- 📄 Generación de PDFs profesionales
- 🔐 Autenticación por número telefónico
- 📊 Dashboard de métricas y analytics
- 🔄 Manejo inteligente de interrupciones
- 🎯 Detección automática de intenciones

---

## 📁 **Estructura del Proyecto**

```
computel_bot/
├── app/
│   ├── core/               # Configuración base
│   ├── features/           # Módulos funcionales
│   │   ├── auth/          # Autenticación
│   │   ├── conversation/  # Motor conversacional
│   │   ├── products/      # Gestión productos
│   │   ├── quotes/        # Cotizaciones
│   │   └── woocommerce/   # Integración WC
│   ├── services/          # Servicios externos
│   ├── models/            # Modelos de datos
│   ├── api/               # Endpoints REST
│   └── utils/             # Utilidades
├── docs/                  # Documentación
├── tests/                 # Pruebas
├── migrations/            # Migraciones BD
└── requirements.txt       # Dependencias
```

---

## 🚀 **Setup Rápido**

### **Prerrequisitos:**
- Python 3.11+
- Cuenta Supabase
- API Key OpenAI
- WhatsApp Business API (Meta)
- WooCommerce con API habilitada

### **Instalación:**

```bash
# 1. Clonar repositorio
git clone [repo-url]
cd computel_bot

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# 5. Configurar base de datos
alembic upgrade head

# 6. Ejecutar aplicación
uvicorn app.main:app --reload
```

### **Variables de Entorno (.env):**
```env
# Base de datos
DATABASE_URL=postgresql://user:pass@host:port/db

# OpenAI
OPENAI_API_KEY=sk-...

# WhatsApp
WHATSAPP_TOKEN=your_token
WHATSAPP_VERIFY_TOKEN=your_verify_token

# WooCommerce
WOOCOMMERCE_URL=https://tutienda.com
WOOCOMMERCE_KEY=ck_...
WOOCOMMERCE_SECRET=cs_...

# Configuración
ENVIRONMENT=development
SECRET_KEY=your_secret_key
```

---

## 📊 **Desarrollo por Fases**

### **✅ Fase 1 - MVP (4 semanas)**
- Webhook WhatsApp básico
- Motor conversacional con ChatGPT
- Autenticación por teléfono
- Sincronización WooCommerce
- Generación PDF cotizaciones

### **🔄 Fase 2 - Mejoras (3 semanas)**
- Conversaciones más inteligentes
- Dashboard básico
- Manejo de interrupciones
- Búsqueda fuzzy productos
- Optimización performance

### **📈 Fase 3 - Analytics (4 semanas)**
- Dashboard completo
- Gestión usuarios avanzada
- Sistema notificaciones
- Análisis conversiones
- Configuración avanzada

---

## 🤖 **Flujo de Conversación**

### **Ejemplo de Uso:**
```
Usuario: "Hola, necesito una cotización"
Bot: "¡Hola! Te ayudo con tu cotización. ¿Qué productos necesitas?"

Usuario: "Papel bond y lápices"
Bot: "Encontré:
📄 Papel Bond A4 75g - $2.50/paq
✏️ Lápiz #2 HB - $0.50/pza
¿Cuántos necesitas de cada uno?"

Usuario: "10 paquetes de papel y 50 lápices"
Bot: "Perfecto:
• 10x Papel Bond A4 - $25.00
• 50x Lápiz #2 HB - $25.00
Subtotal: $50.00
¿Necesitas algo más o genero la cotización?"

Usuario: "Genera la cotización"
Bot: "*Envía PDF*
¡Listo! Tu cotización Q2025-001234
Total: $58.00 (incluye IVA)
Válida hasta: 20/11/2025"
```

---

## 🗄️ **Base de Datos**

### **Tablas Principales:**
- **users**: Usuarios autorizados
- **products**: Catálogo sincronizado WooCommerce
- **conversations**: Conversaciones activas
- **quotes**: Cotizaciones generadas
- **quote_items**: Items de cada cotización

Ver documentación completa en [`docs/BASE_DATOS.md`](docs/BASE_DATOS.md)

---

## 🔧 **API Endpoints**

### **Webhooks:**
- `POST /webhooks/whatsapp` - Recibir mensajes WhatsApp
- `GET /webhooks/whatsapp` - Verificación webhook

### **Admin:**
- `GET /admin/dashboard` - Métricas del dashboard
- `GET /admin/users` - Gestión usuarios
- `GET /admin/quotes` - Historial cotizaciones

### **Interno:**
- `POST /internal/sync` - Sincronizar WooCommerce
- `GET /health` - Health check

---

## 🧪 **Testing**

```bash
# Ejecutar todas las pruebas
pytest tests/ -v

# Pruebas específicas
pytest tests/unit/test_conversation/ -v
pytest tests/integration/test_quote_flow.py -v

# Con cobertura
pytest tests/ --cov=app --cov-report=html
```

### **Estructura de Tests:**
```
tests/
├── unit/              # Pruebas unitarias
│   ├── test_auth/
│   ├── test_conversation/
│   └── test_products/
├── integration/       # Pruebas de integración
└── e2e/              # Pruebas end-to-end
```

---

## 📈 **Monitoreo y Logs**

### **Logs Estructurados:**
```python
import logging

logger = logging.getLogger(__name__)

# Configuración por módulo
logger.info("Processing message", extra={
    "user_id": user_id,
    "intent": intent,
    "processing_time": elapsed_time
})
```

### **Métricas Clave:**
- Tiempo respuesta promedio
- Cotizaciones generadas/día
- Tasa de conversión
- Productos más cotizados
- Errores por módulo

---

## 🚀 **Deployment**

### **Render (Recomendado):**
```yaml
# render.yaml
services:
  - type: web
    name: computel-bot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
```

### **Docker:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🔒 **Seguridad**

### **Medidas Implementadas:**
- ✅ Autenticación por número telefónico
- ✅ Validación webhooks META
- ✅ Rate limiting automático
- ✅ Sanitización de inputs
- ✅ Variables sensibles en entorno
- ✅ Logs de auditoría

### **Configuración Rate Limiting:**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/webhooks/whatsapp")
@limiter.limit("60/minute")
async def whatsapp_webhook(request: Request):
    # Endpoint protegido
    pass
```

---

## 📚 **Documentación Adicional**

- [`PLAN_DESARROLLO.md`](docs/PLAN_DESARROLLO.md) - Plan maestro del proyecto
- [`ARQUITECTURA_MODULAR.md`](docs/ARQUITECTURA_MODULAR.md) - Diseño de módulos
- [`BASE_DATOS.md`](docs/BASE_DATOS.md) - Esquema completo BD
- [`AGENTS.md`](AGENTS.md) - Guía de buenas prácticas

---

## 💡 **Comandos Útiles**

```bash
# Desarrollo
uvicorn app.main:app --reload --port 8000

# Migraciones
alembic revision --autogenerate -m "descripción"
alembic upgrade head

# Linting y formato
black app/ tests/
flake8 app/
isort app/ tests/

# Sincronización manual
python -m app.scripts.sync_products

# Backup BD
pg_dump $DATABASE_URL > backup.sql
```

---

## 🤝 **Contribución**

1. Fork el proyecto
2. Crea feature branch (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push branch (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

### **Estándares de Código:**
- Seguir PEP 8
- Tests para nueva funcionalidad
- Documentación de APIs
- Commits descriptivos

---

## 📞 **Soporte**

- **Issues**: GitHub Issues
- **Documentación**: `/docs` folder
- **Email**: [email del equipo]

---

## 📄 **Licencia**

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

---

## 🔄 **Changelog**

### **v1.0.0 - MVP Initial Release**
- ✅ Bot conversacional básico
- ✅ Integración WhatsApp + OpenAI
- ✅ Sincronización WooCommerce
- ✅ Generación PDF cotizaciones
- ✅ Autenticación por teléfono

### **v1.1.0 - Conversaciones Inteligentes**
- 🔄 Manejo interrupciones naturales
- 🔄 Memoria conversaciones anteriores
- 🔄 Dashboard básico métricas

### **v1.2.0 - Analytics y Admin**
- 📈 Dashboard completo
- 📈 Gestión usuarios avanzada
- 📈 Sistema notificaciones

---

*Última actualización: 20 de octubre de 2025*# CompuBot
