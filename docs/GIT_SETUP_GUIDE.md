# 🚀 Guía Rápida: Setup Git y Branch para Arquitectura V2

## 📦 Paso 1: Inicializar repositorio Git

```bash
cd /Users/leonardocgordillo/Proyectosnext/Computel_bot

# Inicializar Git (si no está inicializado)
git init

# Verificar estado
git status
```

## 📝 Paso 2: Commit inicial (main branch)

```bash
# Agregar todos los archivos
git add .

# Crear commit inicial
git commit -m "Initial commit: MVP Bot Computel

- Conversational engine v1 (actual)
- Quote generation system
- WhatsApp webhook integration
- Test endpoints and chat simulator
- PDF generation with ReportLab
- OpenAI integration for intent detection
- Supabase/SQLite database support"

# Verificar commit
git log --oneline
```

## 🌿 Paso 3: Crear repositorio en GitHub

**Opción A: Desde la web**
1. Ve a https://github.com/new
2. Nombre: `computel-bot`
3. Descripción: "Chatbot de cotizaciones para Computel con WhatsApp"
4. Private (recomendado para MVP)
5. NO inicializar con README (ya lo tenemos)
6. Create repository

**Opción B: Desde CLI (si tienes gh)**
```bash
gh repo create computel-bot --private --source=. --remote=origin
```

## 🔗 Paso 4: Conectar con repositorio remoto

```bash
# Agregar remote (reemplaza TU_USUARIO)
git remote add origin https://github.com/TU_USUARIO/computel-bot.git

# Verificar remote
git remote -v

# Push inicial
git push -u origin main
```

## 🌱 Paso 5: Crear branch para Arquitectura V2

```bash
# Crear y cambiar a nueva branch
git checkout -b feature/conversation-engine-v2

# Verificar branch actual
git branch

# Push de la branch al remoto
git push -u origin feature/conversation-engine-v2
```

## 📋 Paso 6: Verificación

```bash
# Verificar que estás en la branch correcta
git branch
# Debería mostrar: * feature/conversation-engine-v2

# Ver archivos no trackeados
git status

# Ver últimos commits
git log --oneline -5
```

## 🔄 Workflow recomendado durante desarrollo

### Mientras trabajas en v2:

```bash
# Ver cambios
git status

# Ver diff de cambios
git diff

# Agregar archivos modificados
git add app/services/conversation_engine_v2.py
git add app/api/test.py
git add docs/ARCHITECTURE_V2_PLAN.md

# O agregar todos los cambios
git add .

# Commit con mensaje descriptivo
git commit -m "feat: implement conversation_engine_v2 core structure

- Add ConversationEngineV2 class with GPT-first approach
- Implement _analyze_message() for intent detection
- Implement _add_products() with smart product search
- Add endpoint /test-conversation-v2 for testing"

# Push a la branch
git push origin feature/conversation-engine-v2
```

### Mensajes de commit recomendados:

```bash
# Features nuevos
git commit -m "feat: add GPT-based product search"

# Corrección de bugs
git commit -m "fix: handle empty cart when generating quote"

# Refactoring
git commit -m "refactor: simplify _execute_action method"

# Documentación
git commit -m "docs: update ARCHITECTURE_V2_PLAN with test results"

# Tests
git commit -m "test: add integration tests for v2 engine"
```

## 🔍 Paso 7: Ver progreso

```bash
# Ver todos los commits en tu branch
git log --oneline --graph --all

# Ver diferencias con main
git diff main..feature/conversation-engine-v2

# Ver archivos modificados vs main
git diff --name-only main
```

## ✅ Paso 8: Cuando esté listo para PR (Pull Request)

```bash
# Asegurarte que todo está commiteado
git status

# Actualizar con main (por si hay cambios)
git checkout main
git pull origin main
git checkout feature/conversation-engine-v2
git merge main

# Resolver conflictos si hay (Git te avisará)

# Push final
git push origin feature/conversation-engine-v2
```

Luego en GitHub:
1. Ve al repositorio
2. Click en "Pull requests" → "New pull request"
3. Base: `main` ← Compare: `feature/conversation-engine-v2`
4. Título: "feat: Implement GPT-first Conversation Engine V2"
5. Descripción: Copiar desde `docs/ARCHITECTURE_V2_PLAN.md`
6. Create pull request

## 🚨 Comandos útiles de emergencia

```bash
# Deshacer último commit (pero mantener cambios)
git reset --soft HEAD~1

# Descartar cambios en un archivo
git checkout -- archivo.py

# Ver qué branch está trackeando tu branch
git branch -vv

# Cambiar de branch sin perder cambios
git stash
git checkout otra-branch
git checkout feature/conversation-engine-v2
git stash pop

# Limpiar archivos no trackeados
git clean -fd
```

## 📊 Checklist antes de cada push

- [ ] Código funciona (probado localmente)
- [ ] Sin archivos sensibles (.env, .db, etc.)
- [ ] Mensaje de commit descriptivo
- [ ] Archivos innecesarios no incluidos (verificar .gitignore)
- [ ] Tests pasan (cuando los haya)

## 🎯 Estado actual del proyecto

**Branch:** `feature/conversation-engine-v2`
**Estado:** Listo para comenzar desarrollo
**Archivo principal:** `docs/ARCHITECTURE_V2_PLAN.md`

---

¡Ya puedes comenzar a desarrollar! 🚀
