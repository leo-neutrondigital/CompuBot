# Plan de Implementación: Arquitectura Conversacional v2

## 📋 Resumen Ejecutivo

**Objetivo:** Reemplazar el motor conversacional actual (700 líneas, 6 estados) por una arquitectura GPT-first simplificada (150 líneas, flujo natural).

**Problema actual:**
- Conversación robotizada y poco natural
- Búsqueda de productos ineficiente (regex/fuzzy matching)
- Sistema de estados complejo e innecesario
- UX frustrante (preguntas repetitivas)
- Viola principios de AGENTS.md (sobreingeniería)

**Solución propuesta:**
- Delegar lenguaje natural a GPT-4
- Mantener control sobre datos y lógica de negocio
- Conversación fluida y contextual
- Búsqueda inteligente de productos con GPT
- Código simple y mantenible

---

## 🎯 Objetivos de la Nueva Arquitectura

### Funcionales
- ✅ Conversación natural sin scripts rígidos
- ✅ Agregar múltiples productos en un mensaje
- ✅ Quitar/modificar productos fácilmente
- ✅ Consultar estado del carrito en cualquier momento
- ✅ Manejo inteligente de productos no encontrados
- ✅ Selección automática de mejor opción cuando hay duplicados
- ✅ Generación de PDF sin pasos intermedios

### No Funcionales
- ✅ Código < 200 líneas (vs 700 actuales)
- ✅ Máximo 2 estados internos
- ✅ Tiempo de respuesta < 3 segundos
- ✅ Costo OpenAI < $0.02 por mensaje
- ✅ 100% compatible con API actual

---

## 🏗️ Arquitectura Propuesta

### Diagrama de Flujo

```
┌─────────────────────────────────────────┐
│         Usuario envía mensaje           │
│  "Quiero 20 calculadoras, 100 hojas"   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│    ConversationEngineV2.process_message │
│                                          │
│  1. Analizar mensaje con GPT            │
│     → Extraer intención + productos     │
│                                          │
│  2. Ejecutar acción                     │
│     → Agregar/Quitar/Consultar/PDF     │
│                                          │
│  3. Generar respuesta natural (GPT)     │
│     → Confirmar acción + contexto       │
│                                          │
│  4. Guardar estado en DB                │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│       Respuesta natural al usuario      │
│   "Listo ✅ Agregué:                    │
│    • 20x Calculadora Casio ($285)       │
│    • 100x Papel Bond ($2.50)            │
│    Total: $5,950. ¿Algo más?"           │
└─────────────────────────────────────────┘
```

### Componentes Principales

#### 1. ConversationEngineV2
**Ubicación:** `app/services/conversation_engine_v2.py`

**Responsabilidades:**
- Orquestar flujo conversacional
- Delegar análisis de lenguaje a GPT
- Ejecutar acciones (agregar/quitar productos)
- Mantener estado del carrito
- Generar respuestas naturales

**Métodos principales:**
```python
- process_message()          # Punto de entrada principal
- _analyze_message()         # GPT analiza intención
- _execute_action()          # Ejecuta acción detectada
- _add_products()            # Busca y agrega productos
- _remove_products()         # Quita productos del carrito
- _get_cart_summary()        # Resumen actual
- _generate_quote()          # Genera PDF
- _generate_natural_response() # GPT genera respuesta
```

#### 2. OpenAI Service (Mejorado)
**Ubicación:** `app/services/openai_service.py`

**Nuevos métodos necesarios:**
```python
- chat_completion()          # Llamada a GPT-4 con JSON
- get_embedding()            # Embeddings para búsqueda semántica
- extract_products()         # Extraer productos del mensaje
- choose_best_match()        # Elegir mejor producto entre opciones
```

#### 3. Product Repository (Mejorado)
**Ubicación:** `app/repositories/product_repository.py`

**Mejoras necesarias:**
```python
- find_by_embedding()        # Búsqueda por similitud semántica
- search_with_synonyms()     # Búsqueda mejorada con sinónimos
```

---

## 📦 Estructura de Datos

### Conversación (Modelo existente)
```python
{
  "id": "uuid",
  "user_id": "uuid",
  "products_in_progress": [
    {
      "requested": {
        "name": "calculadora",
        "quantity": 20,
        "unit": "piezas"
      },
      "matched_product": {
        "id": "uuid",
        "name": "Calculadora Casio FX-991",
        "price": 285.0,
        "sku": "CALC-CASIO-FX991"
      }
    }
  ],
  "context": {
    "last_intent": "agregar",
    "conversation_summary": "Cliente quiere cotizar material de oficina"
  }
}
```

### Análisis de Mensaje (GPT Output)
```json
{
  "intent": "agregar",
  "products": [
    {
      "name": "calculadora cientifica",
      "quantity": 20,
      "action": "add"
    }
  ],
  "conversation_context": "Cliente necesita material de oficina",
  "needs_clarification": false,
  "clarification_reason": null
}
```

---

## 🔄 Flujos de Uso

### Flujo 1: Agregar Productos (Mensaje Múltiple)

```
Usuario → "Quiero 20 calculadoras, 100 hojas bond y 50 plumas"

[1. Analizar mensaje]
GPT detecta:
- intent: "agregar"
- products: [
    {name: "calculadora", quantity: 20},
    {name: "papel bond", quantity: 100},
    {name: "pluma", quantity: 50}
  ]

[2. Buscar productos]
- Calculadora → Encuentra 1 match → Agrega automáticamente
- Papel bond → Encuentra 2 matches → GPT elige el mejor
- Pluma → Encuentra 2 matches → GPT elige el mejor

[3. Actualizar carrito]
products_in_progress = [calculadora×20, papel×100, pluma×50]

[4. Generar respuesta]
Bot → "Listo ✅ Agregué:
       • 20x Calculadora Casio FX-991 ($285 c/u) = $5,700
       • 100x Papel Bond A4 ($2.50 c/u) = $250
       • 50x Pluma BIC Azul ($1 c/u) = $50
       
       Total: $6,000
       
       ¿Algo más?"
```

### Flujo 2: Consultar Estado

```
Usuario → "¿Cuántos productos llevo?"

[1. Analizar]
intent: "consultar"

[2. Obtener resumen]
3 productos, total $6,000

[3. Respuesta]
Bot → "Tienes 3 productos por $6,000:
       • 20 calculadoras
       • 100 hojas
       • 50 plumas
       
       ¿Quieres generar el PDF?"
```

### Flujo 3: Quitar Producto

```
Usuario → "Quita las plumas"

[1. Analizar]
intent: "quitar"
products: [{name: "pluma", action: "remove"}]

[2. Ejecutar]
Busca "pluma" en carrito → Encuentra y elimina

[3. Respuesta]
Bot → "Listo, quité 50 Plumas BIC ✅
       
       Nuevo total: $5,950 (2 productos)
       
       ¿Algo más?"
```

### Flujo 4: Producto No Encontrado

```
Usuario → "Agrega 5 grapadoras industriales"

[1. Analizar]
intent: "agregar"
products: [{name: "grapadora industrial", quantity: 5}]

[2. Buscar]
No encuentra "grapadora industrial"
Encuentra productos similares: [Engrapadora Metálica, Engrapadora Escritorio]

[3. Respuesta]
Bot → "No tengo 'grapadoras industriales' 😔
       
       ¿Te sirve alguna de estas?
       • Engrapadora Metálica ($15)
       • Engrapadora de Escritorio ($8)
       
       Dime cuál prefieres o si buscas otra cosa"
```

### Flujo 5: Generar Cotización

```
Usuario → "Genera el PDF"

[1. Analizar]
intent: "generar_pdf"

[2. Validar]
Tiene productos en carrito ✅

[3. Generar]
- Crear registro Quote
- Generar PDF con ReportLab
- Guardar pdf_path en BD

[4. Limpiar carrito]
products_in_progress = []

[5. Respuesta]
Bot → "¡Cotización COT-20251021-001 lista! 🎉
       
       📋 3 productos
       💰 Total: $5,950 MXN
       📄 http://localhost:8000/test/quotes/xxx/pdf
       
       ¿Necesitas otra cosa?"
```

---

## 🛠️ Plan de Implementación

### Fase 1: Preparación (30 min)

**Tareas:**
- [ ] Crear branch `feature/conversation-engine-v2`
- [ ] Crear archivo `conversation_engine_v2.py`
- [ ] Revisar y documentar API actual de OpenAI service
- [ ] Identificar métodos reutilizables del engine actual

**Entregables:**
- Branch limpio
- Estructura base del archivo
- Lista de dependencias

### Fase 2: Implementación Core (2 horas)

#### 2.1 OpenAI Service Extensions (30 min)
**Archivo:** `app/services/openai_service.py`

```python
# Agregar métodos:
async def chat_completion(
    messages: List[Dict],
    response_format: Optional[Dict] = None,
    temperature: float = 0.7
) -> str:
    """Llamada genérica a GPT-4 con control de formato"""
    pass

async def extract_structured_data(
    prompt: str,
    schema: Dict
) -> Dict:
    """Extraer datos estructurados del mensaje"""
    pass
```

**Tests:**
```bash
# Test manual
curl -X POST "http://localhost:8000/test/test-openai" \
  -d "prompt=Analiza: Quiero 20 calculadoras"
```

#### 2.2 ConversationEngineV2 - Estructura Base (30 min)
**Archivo:** `app/services/conversation_engine_v2.py`

```python
class ConversationEngineV2:
    """Motor conversacional simplificado"""
    
    async def process_message(self, db, user, conversation, message):
        """Punto de entrada principal"""
        pass
    
    async def _analyze_message(self, message, conversation):
        """GPT analiza mensaje"""
        pass
    
    async def _execute_action(self, db, conversation, analysis):
        """Ejecuta acción detectada"""
        pass
    
    async def _generate_natural_response(self, conversation, analysis, result):
        """GPT genera respuesta natural"""
        pass
```

#### 2.3 Implementar Lógica de Productos (1 hora)
```python
async def _add_products(self, db, conversation, products):
    """Buscar y agregar productos al carrito"""
    pass

async def _remove_products(self, conversation, products):
    """Quitar productos del carrito"""
    pass

async def _choose_best_product(self, requested, options):
    """GPT elige mejor match entre opciones"""
    pass

def _add_to_cart(self, conversation, requested_name, quantity, product):
    """Agregar producto al carrito (helper)"""
    pass
```

### Fase 3: Integración y Testing (1 hora)

#### 3.1 Endpoint de Testing (15 min)
**Archivo:** `app/api/test.py`

```python
@router.post("/test-conversation-v2")
async def test_conversation_v2(
    user_phone: str = Form(...),
    message: str = Form(...),
    db: Session = Depends(get_db)
):
    """Probar nueva versión del motor conversacional"""
    pass
```

#### 3.2 Actualizar Chat Simulator (15 min)
**Archivo:** `app/api/chat_simulator.py`

Agregar botón para probar v2:
```html
<button onclick="useV2Engine()">🧪 Probar Engine V2</button>
```

#### 3.3 Tests Manuales (30 min)

**Casos de prueba:**
```bash
# 1. Agregar múltiples productos
"Quiero 20 calculadoras, 100 hojas y 50 plumas"

# 2. Consultar estado
"¿Qué llevo?"

# 3. Quitar producto
"Quita las plumas"

# 4. Producto no encontrado
"Agrega 10 grapadoras industriales"

# 5. Generar PDF
"Genera la cotización"

# 6. Conversación natural
"No tengo 'lapiceros', ¿tienes plumas?"
```

### Fase 4: Refinamiento (30 min)

**Tareas:**
- [ ] Ajustar prompts según resultados de tests
- [ ] Mejorar manejo de errores
- [ ] Agregar logging estructurado
- [ ] Documentar casos edge

### Fase 5: Migración (si todo funciona bien)

**Decisión:** Comparar v1 vs v2 después de testing

**Criterios de éxito para migrar:**
- ✅ Conversación más natural (feedback usuario)
- ✅ Menos errores en búsqueda de productos
- ✅ Código más mantenible (< 200 líneas)
- ✅ Tiempo de respuesta aceptable (< 3s)
- ✅ Sin bugs críticos

**Si se aprueba migración:**
1. Renombrar `conversation_engine.py` → `conversation_engine_legacy.py`
2. Renombrar `conversation_engine_v2.py` → `conversation_engine.py`
3. Actualizar imports en toda la app
4. Eliminar código legacy después de 1 semana de testing

---

## 📊 Métricas de Éxito

### Antes (v1)
- Código: ~700 líneas
- Estados: 6 (conversando, saludando, recopilando, validando, cotizando, finalizado)
- Mensajes por cotización: ~8-12
- Búsqueda productos: Regex/fuzzy (60% precisión)
- UX: Robotizada, repetitiva
- Mantenibilidad: Baja (código complejo)

### Después (v2 objetivo)
- Código: <200 líneas
- Estados: 2 (con productos / sin productos)
- Mensajes por cotización: 2-4
- Búsqueda productos: GPT + embeddings (90%+ precisión)
- UX: Natural, fluida
- Mantenibilidad: Alta (código simple)

### KPIs a Medir
1. **Tiempo promedio de conversación**: Objetivo < 2 minutos
2. **Precisión búsqueda productos**: Objetivo > 90%
3. **Satisfacción usuario** (encuesta): Objetivo > 4/5
4. **Tasa de abandono**: Objetivo < 10%
5. **Costo por conversación**: Objetivo < $0.05

---

## 🚨 Riesgos y Mitigaciones

### Riesgo 1: Dependencia 100% de OpenAI
**Impacto:** Alto  
**Probabilidad:** Baja  
**Mitigación:**
- Implementar rate limiting
- Caché de respuestas comunes
- Fallback a v1 si API falla
- Timeout de 5s en llamadas GPT

### Riesgo 2: Costos de API elevados
**Impacto:** Medio  
**Probabilidad:** Media  
**Mitigación:**
- Limitar tokens en prompts (max 500 input, 200 output)
- Usar gpt-4o-mini para análisis simple
- Monitorear costos diarios
- Alerta si > $10/día

### Riesgo 3: Respuestas inconsistentes de GPT
**Impacto:** Medio  
**Probabilidad:** Media  
**Mitigación:**
- Prompts muy específicos con ejemplos
- Validación de output (JSON schema)
- Retry con temperature=0 si falla
- Logging de respuestas inesperadas

### Riesgo 4: Performance (latencia)
**Impacto:** Medio  
**Probabilidad:** Baja  
**Mitigación:**
- Streaming de respuestas GPT
- Procesamiento paralelo de búsquedas
- Caché de productos frecuentes
- Timeout agresivo (3s)

---

## 📝 Checklist de Implementación

### Pre-desarrollo
- [ ] Leer y entender AGENTS.md
- [ ] Revisar código actual de conversation_engine.py
- [ ] Crear branch feature/conversation-engine-v2
- [ ] Setup entorno de desarrollo

### Desarrollo
- [ ] Implementar conversation_engine_v2.py (estructura base)
- [ ] Implementar _analyze_message() con GPT
- [ ] Implementar _execute_action() (router de acciones)
- [ ] Implementar _add_products() (búsqueda y agregado)
- [ ] Implementar _remove_products() (eliminación)
- [ ] Implementar _get_cart_summary() (resumen)
- [ ] Implementar _generate_quote() (crear PDF)
- [ ] Implementar _generate_natural_response() (GPT respuesta)
- [ ] Agregar endpoint /test-conversation-v2
- [ ] Agregar botón en chat simulator para v2

### Testing
- [ ] Test: Agregar 1 producto
- [ ] Test: Agregar múltiples productos en 1 mensaje
- [ ] Test: Consultar estado del carrito
- [ ] Test: Quitar producto
- [ ] Test: Producto no encontrado
- [ ] Test: Generar PDF
- [ ] Test: Conversación con contexto complejo
- [ ] Test: Manejo de errores (API down, BD error)
- [ ] Test: Performance (< 3s respuesta)

### Refinamiento
- [ ] Ajustar prompts según feedback
- [ ] Agregar logging estructurado
- [ ] Documentar casos edge
- [ ] Code review
- [ ] Actualizar README con nueva arquitectura

### Despliegue
- [ ] Merge a develop (si aprobado)
- [ ] Testing en staging
- [ ] Feature flag para habilitar v2
- [ ] Monitoreo de métricas
- [ ] Rollback plan documentado

---

## 📚 Referencias

### Documentos Relacionados
- [AGENTS.md](../AGENTS.md) - Guía de buenas prácticas
- [README.md](../README.md) - Documentación general del proyecto

### APIs Utilizadas
- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [OpenAI GPT-4 Guide](https://platform.openai.com/docs/guides/gpt-4)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

### Ejemplos de Código
- Ver implementación en `conversation_engine_v2.py` (cuando esté lista)
- Ver tests en `tests/test_conversation_v2.py` (cuando estén listos)

---

## 🔄 Proceso de Review

### Antes de PR
1. Auto-review con checklist arriba
2. Ejecutar todos los tests
3. Verificar cumplimiento de AGENTS.md
4. Documentar decisiones técnicas importantes

### Durante Review
**Revisar:**
- [ ] Código cumple AGENTS.md (claridad, sin sobreingeniería)
- [ ] Prompts de GPT son específicos y probados
- [ ] Manejo de errores adecuado
- [ ] Logging estructurado presente
- [ ] Performance aceptable (< 3s)
- [ ] Sin dependencias innecesarias

### Después de Aprobación
1. Merge a develop
2. Deploy a staging
3. Testing con usuarios reales (1 semana)
4. Recopilar feedback
5. Decisión: Migrar a producción o iterar

---

## 🎓 Lecciones Aprendidas (Post-Implementación)

*Esta sección se completará después de implementar y probar v2*

### ¿Qué funcionó bien?
- TBD

### ¿Qué podría mejorar?
- TBD

### ¿Qué aprendimos?
- TBD

---

## 📞 Contacto y Soporte

**Mantenedor:** Leonardo Gordillo  
**Proyecto:** Computel Bot  
**Repositorio:** [Pendiente crear]  

**Para preguntas o dudas:**
- Revisar este documento primero
- Consultar AGENTS.md para principios generales
- Crear issue en GitHub con etiqueta `conversation-v2`

---

**Última actualización:** 21 de octubre de 2025  
**Versión del documento:** 1.0  
**Estado:** Planificación → Pendiente implementación
