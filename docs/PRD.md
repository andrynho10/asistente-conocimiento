# Asistente-Conocimiento - Product Requirements Document

**Autor:** Andres Amaya Garces
**Fecha:** 2025-11-10
**Versión:** 1.0

---

## Executive Summary

Este proyecto desarrolla un prototipo de inteligencia artificial generativa diseñado para revolucionar la gestión del conocimiento y la capacitación organizacional en empresas modernas. El sistema automatiza la captura, análisis y distribución del conocimiento corporativo, transformando información dispersa y tácita en conocimiento explícito, estructurado y accesible mediante procesamiento de lenguaje natural.

El prototipo se enmarca en un estudio de prefactibilidad tecnológica académica, aplicando metodología Scrum para validar la viabilidad técnica, operativa y económica de integrar IA generativa como herramienta estratégica en organizaciones como Isapre Banmédica S.A.

### Contexto Académico

**Proyecto de Título:** "Desarrollo de un Prototipo de Inteligencia Artificial para la Capacitación y Apoyo en Procesos Organizacionales"

**Institución:** Universidad de Las Américas - Facultad de Ingeniería y Negocios

**Equipo:** Andres Amaya Garces, Marco Ortiz Plaza, Jorge Santander Hidalgo

**Profesor Guía:** Cristian Rojas Catalan

### Qué Hace Este Producto Especial

**La Magia del Producto:**

> "Transforma el conocimiento invisible (tácito) en conocimiento accesible (explícito) usando IA generativa que no solo responde preguntas, sino que CREA capacitación personalizada en tiempo real, cumpliendo con regulaciones de privacidad chilenas y demostrando viabilidad para empresas latinoamericanas."

**El Momento "WOW":**

Cuando un empleado nuevo pregunta "¿Cómo proceso un reembolso especial?" y el sistema:
1. Responde en menos de 2 segundos con información contextualizada
2. Extrae conocimiento de múltiples fuentes (manuales, documentos, FAQs)
3. GENERA automáticamente un tutorial personalizado, quiz de validación y ruta de aprendizaje
4. Todo cumpliendo con la Ley 19.628 de protección de datos

**¿Por Qué Los Usuarios Amarán Esta Herramienta?**

- **Velocidad brutal:** Respuestas contextualizadas instantáneas (< 2 segundos)
- **Aprendizaje a medida:** Genera quizzes, resúmenes y learning paths personalizados
- **Liberación del conocimiento:** Elimina la dependencia de empleados específicos
- **Eficiencia operativa:** Reduce curvas de aprendizaje y duplicación de tareas

---

## Project Classification

**Tipo Técnico:** Web Application + AI Backend (API-driven)

**Dominio:** Enterprise Software / Knowledge Management + EdTech

**Complejidad:** Alta

**Clasificación del Proyecto:**

- **Arquitectura:** Sistema de 3 capas (Frontend + Backend/Motor IA + Base de Datos)
- **Tecnología Core:** IA Generativa (LLM) + RAG (Retrieval-Augmented Generation)
- **Infraestructura:** Entorno de laboratorio académico (no producción)
- **Stack:** Python + Framework Web + Base de Datos SQL + API REST

### Contexto del Dominio: Gestión del Conocimiento Organizacional

**Problema Fundamental:**

Las organizaciones modernas enfrentan ineficiencias críticas en la gestión del conocimiento:

1. **Conocimiento fragmentado:** Información dispersa en múltiples repositorios, sistemas y en la experiencia de empleados senior
2. **Dependencia del conocimiento tácito:** Pérdida de productividad cuando empleados clave se retiran o rotan
3. **Capacitación rígida e ineficiente:** Métodos presenciales, reactivos y desactualizados que no se adaptan a necesidades individuales
4. **Falta de automatización:** No existen sistemas inteligentes que capturen, clasifiquen y distribuyan conocimiento

**Análisis Causa-Efecto (Diagrama de Ishikawa):**

**Factores Identificados:**

- **Métodos:** Capacitación rígida, falta de retroalimentación, sin trazabilidad
- **Personas:** Dependencia de conocimiento tácito, resistencia al cambio, alta rotación
- **Tecnología:** Sin sistemas integrados de gestión del conocimiento, escasa automatización
- **Gestión:** Desalineación entre capacitación y objetivos estratégicos, sin medición de impacto
- **Entorno:** Aceleración tecnológica, competencia, brecha entre inversión y adopción

**Impacto del Problema:**

- Pérdida de productividad y duplicación de esfuerzos
- Curvas de aprendizaje largas para nuevos empleados
- Costos elevados de capacitación
- Disminución de la capacidad innovadora
- Riesgo operativo por pérdida de conocimiento crítico

**Oportunidad de Mercado:**

Según MarketsandMarkets (2024), el mercado global de IA aplicada a gestión del conocimiento y capacitación empresarial:
- Alcanzará USD $80 mil millones para 2030
- CAGR > 35% (crecimiento anual compuesto)
- Impulsado por: automatización cognitiva, transformación digital post-pandemia, adopción de IA generativa

En América Latina, el BID (2023) reporta que >60% de empresas medianas/grandes están incorporando IA para optimizar procesos internos.

---

## Success Criteria

### Criterios de Éxito del Prototipo

**Éxito Técnico (Prefactibilidad Técnica):**

1. **Funcionalidad Core Operativa:**
   - Motor de IA generativa responde consultas en lenguaje natural con precisión >80%
   - Tiempo de respuesta < 2 segundos (RNF2)
   - Gestión documental (carga, indexación, búsqueda) de PDF y texto funcional
   - Generación automática de contenido (resúmenes, quizzes) operativa

2. **Arquitectura Validada:**
   - Modelo de 3 capas implementado y funcional
   - API REST operativa entre frontend y backend
   - Base de conocimiento estructurada y consultable
   - Sistema de autenticación y control de acceso implementado

3. **Cumplimiento de Requerimientos:**
   - ≥90% de requerimientos funcionales (RF1-RF5) implementados
   - Todos los requerimientos de seguridad (RS1-RS5) cumplidos
   - Requerimientos no funcionales críticos (RNF1-RNF3) validados

**Éxito Operativo (Prefactibilidad Operativa):**

1. **Usabilidad Demostrada:**
   - Interfaz intuitiva validada con pruebas de usabilidad
   - Usuarios pueden consultar conocimiento sin capacitación previa
   - Tasa de satisfacción en pruebas de usabilidad >70%

2. **Gestión del Conocimiento:**
   - Sistema captura y clasifica documentos correctamente
   - Respuestas generadas son contextualizadas y relevantes
   - Retroalimentación de usuarios se registra para mejora continua

**Éxito Académico (Entregables del Proyecto de Título):**

1. **Documentación Completa:**
   - Especificación de Requerimientos (ERS) completa
   - Diagramas UML (Casos de Uso, Componentes, E-R) exhaustivos
   - Documentación técnica del sistema según estándares académicos

2. **Validación Metodológica:**
   - Aplicación rigurosa de Scrum (5 sprints documentados)
   - Evidencia de mejora continua y trazabilidad
   - Coherencia ≥90% entre objetivos y entregables

3. **Análisis de Prefactibilidad:**
   - Informe de prefactibilidad técnica, operativa y económica completo
   - Evaluación de impacto en eficiencia organizacional
   - Conclusiones sobre viabilidad de implementación futura

**Éxito Estratégico (Impacto Organizacional):**

1. **Transformación del Conocimiento:**
   - Demostración clara de conversión conocimiento tácito → explícito
   - Reducción proyectada de tiempos de capacitación (métrica estimada)
   - Potencial de escalabilidad identificado

2. **Alineación con Transformación Digital:**
   - Solución alineada con principios de Industria 4.0
   - Cumplimiento de regulaciones chilenas (Ley 19.628)
   - Modelo replicable para otras organizaciones

### Métricas de Validación

**Métricas Técnicas:**
- Tiempo de respuesta promedio de IA: < 2 segundos
- Precisión de respuestas: >80% (evaluación humana)
- Disponibilidad del sistema en pruebas: >95%
- Tasa de error en indexación de documentos: <5%

**Métricas de Usabilidad:**
- Tasa de satisfacción de usuarios en pruebas: >70%
- Tareas completadas exitosamente sin ayuda: >80%
- Tiempo promedio para primera consulta exitosa: <5 minutos

**Métricas Académicas:**
- Porcentaje de requerimientos implementados: ≥90%
- Cobertura de pruebas funcionales: ≥85%
- Completitud de documentación UML: 100%

---

## Product Scope

### MVP - Minimum Viable Product (Sprint 0-4)

**Alcance del Prototipo Funcional:**

El MVP constituye un sistema funcional que demuestra la prefactibilidad técnica y operativa de la solución. Incluye:

**1. Gestión del Conocimiento (RF1, RF3):**

- **Repositorio de Conocimiento:**
  - Base de datos estructurada para almacenar documentos organizacionales
  - Soporte para formatos: PDF, TXT, documentos de texto
  - Clasificación automática de documentos (metadatos: categoría, fecha, autor)
  - Indexación para búsqueda eficiente

- **Gestión Documental:**
  - Interfaz de administración para cargar documentos
  - Procesamiento y extracción de texto de PDFs
  - Validación de formatos y manejo de errores
  - Visualización de documentos cargados

**2. Motor de IA Generativa (RF2, RF4):**

- **Consultas en Lenguaje Natural:**
  - Interfaz conversacional para usuarios
  - Procesamiento de preguntas en español (lenguaje natural)
  - Generación de respuestas contextualizadas usando RAG (Retrieval-Augmented Generation)
  - Referencia a fuentes de conocimiento en respuestas

- **Generación de Contenido Formativo:**
  - Creación automática de resúmenes de documentos
  - Generación de quizzes/evaluaciones basados en contenido
  - Sugerencia de learning paths (rutas de aprendizaje)
  - Contenido adaptado al contexto de la consulta

**3. Interfaz de Usuario (RNF1):**

- **Frontend Web:**
  - Interfaz intuitiva y responsive
  - Área de consulta conversacional (estilo chat)
  - Panel de gestión documental
  - Visualización de respuestas formateadas

- **Experiencia de Usuario:**
  - Diseño basado en principios UX
  - Feedback visual de estado del sistema
  - Manejo claro de errores
  - Accesibilidad básica

**4. Seguridad y Cumplimiento (RS1-RS5):**

- **Autenticación y Control de Acceso:**
  - Sistema de login con credenciales únicas (RS1)
  - Roles: Administrador y Usuario (RS2)
  - Sesiones seguras con tokens

- **Protección de Datos:**
  - Anonimización de datos sensibles (RS5, Ley 19.628)
  - Cifrado de comunicaciones HTTPS (RS4)
  - Cifrado de base de datos en reposo (RS4)
  - Registro de auditoría de accesos y consultas (RS3)

**5. Arquitectura Escalable (RNF3):**

- **Diseño de 3 Capas:**
  - Capa de Presentación (Frontend)
  - Capa Lógica (Backend + Motor IA)
  - Capa de Datos (Base de Conocimiento)

- **API REST:**
  - Endpoints documentados para comunicación frontend-backend
  - Preparado para integración futura con sistemas externos (RNF4)

**6. Monitoreo y Mantenibilidad (RM1-RM3):**

- **Logging y Trazabilidad:**
  - Logs de errores y excepciones (RM2)
  - Logs de rendimiento (tiempos de respuesta)
  - Logs de auditoría de seguridad

- **Documentación Técnica:**
  - Manual técnico del sistema (RM3)
  - Documentación de código
  - Diagramas UML (Casos de Uso, Componentes, E-R)
  - Guía de actualización del modelo de IA (RM1)

**Entregables del MVP (Alineados con Sprints):**

| Sprint | Fase | Entregables Principales |
|--------|------|------------------------|
| **Sprint 0** | Planificación y Levantamiento | Product Backlog, ERS (Especificación de Requerimientos), Matriz RACI, Cronograma |
| **Sprint 1** | Diseño Conceptual y Arquitectura | Diagramas UML (Casos de Uso, Componentes, E-R), Documentación de Casos de Uso, Arquitectura de 3 capas |
| **Sprint 2** | Desarrollo Motor IA | Backend funcional, Motor de IA operativo con LLM, Repositorio de conocimiento estructurado, API REST |
| **Sprint 3** | Interfaz y Pruebas Usabilidad | Frontend funcional, Integración frontend-backend completa, Reporte de Pruebas de Usabilidad |
| **Sprint 4** | Evaluación Prefactibilidad | Pruebas funcionales exhaustivas, Pruebas de seguridad, Informe de Prefactibilidad (técnica/operativa/económica), Documentación final |

**Funcionalidades Excluidas del MVP:**

✗ Implementación en producción en Isapre Banmédica
✗ Infraestructura de alta disponibilidad (servidores dedicados, cloud empresarial)
✗ Soporte multiidioma (solo español)
✗ Integración con sistemas legacy de Banmédica
✗ Análisis predictivo avanzado
✗ Módulo de reportería empresarial
✗ Despliegue masivo y escalamiento a miles de usuarios
✗ Mantenimiento y soporte post-proyecto

### Growth Features (Post-MVP / Futuras Versiones)

**Funcionalidades de Expansión (No incluidas en este proyecto):**

**1. Capacitación Avanzada:**
- Generación de cursos completos automáticos
- Gamificación del aprendizaje
- Certificaciones y tracking de progreso individual
- Recomendaciones personalizadas por perfil de usuario

**2. Analítica y Business Intelligence:**
- Dashboard de métricas de uso y adopción
- Análisis de gaps de conocimiento organizacional
- Identificación de áreas críticas de capacitación
- Reportes ejecutivos automatizados

**3. Integración Empresarial:**
- Conexión con sistemas HR (RRHH)
- Integración con plataformas LMS existentes
- SSO (Single Sign-On) corporativo
- API pública para terceros

**4. IA Multimodal:**
- Procesamiento de videos y audios (transcripción automática)
- Generación de contenido visual (infografías, diagramas)
- Asistente de voz para consultas

**5. Colaboración y Social Learning:**
- Comentarios y valoraciones comunitarias
- Foros de discusión integrados
- Expertos verificados y mentorías
- Compartir conocimiento entre equipos

### Vision (Largo Plazo)

**Transformación Digital Completa del Aprendizaje Organizacional:**

- **Plataforma SaaS Multiempresa:**
  - Solución cloud escalable para múltiples organizaciones
  - Multi-tenancy con aislamiento de datos
  - Marketplace de contenido formativo

- **IA Predictiva y Adaptativa:**
  - Predicción de necesidades de capacitación
  - Detección temprana de brechas de conocimiento
  - Adaptación automática de contenido según desempeño

- **Expansión Regional:**
  - Cumplimiento de regulaciones de múltiples países (GDPR, LGPD Brasil, etc.)
  - Soporte multiidioma para Latinoamérica
  - Alianzas con empresas regionales

---

## Domain-Specific Requirements

### Cumplimiento Normativo y Legal (Chile)

**1. Ley N.º 19.628 - Protección de Datos Personales:**

**Principio:** Solo se puede tratar datos personales con autorización legal o consentimiento del titular.

**Aplicación al Prototipo:**

- **Anonimización Obligatoria (RS5):**
  - Todo dato personal en documentos de prueba debe ser anonimizado
  - Técnicas: enmascaramiento, pseudonimización, datos sintéticos
  - Validación: Ningún dato real de empleados de Banmédica en el sistema de pruebas

- **Minimización de Datos:**
  - Solo recopilar información estrictamente necesaria
  - No almacenar datos personales innecesarios
  - Política de retención de datos clara

- **Control de Acceso y Confidencialidad (RS2):**
  - Roles y permisos estrictos
  - Logs de auditoría de acceso a información sensible (RS3)
  - Derecho de los titulares a acceder y eliminar sus datos

**Consecuencias del Incumplimiento:** Sanciones legales, pérdida de confianza, inviabilidad del proyecto

**2. Ley N.º 21.180 - Transformación Digital del Estado:**

**Principio:** Promover interoperabilidad, integridad y trazabilidad de datos.

**Aplicación al Prototipo:**

- **Interoperabilidad (RNF4):**
  - Diseño de API REST con estándares abiertos
  - Documentación OpenAPI/Swagger
  - Preparación para integración con sistemas externos

- **Trazabilidad:**
  - Logs de auditoría completos (RS3)
  - Versionado de documentos
  - Historial de cambios en base de conocimiento

**3. Ley N.º 17.336 - Propiedad Intelectual:**

**Principio:** Protección de derechos de autor sobre obras intelectuales (software, algoritmos, bases de datos).

**Aplicación al Prototipo:**

- **Respeto a Licencias:**
  - Todo software de terceros debe tener licencia válida (open source o comercial)
  - Bibliotecas Python: verificar licencias MIT, Apache, GPL
  - APIs de IA (OpenAI, HuggingFace): cumplir términos de uso

- **Propiedad del Desarrollo:**
  - El código fuente del prototipo es propiedad intelectual del equipo
  - Documentación técnica protegida por derechos de autor
  - Compromiso de no usar código propietario sin autorización

**4. ISO/IEC 27001:2022 - Seguridad de la Información:**

**Principio:** Gestión de riesgos para garantizar confidencialidad, integridad y disponibilidad.

**Aplicación al Prototipo:**

- **Controles de Seguridad:**
  - Gestión de accesos (RS1, RS2)
  - Cifrado en tránsito (HTTPS) y en reposo (base de datos)
  - Gestión de vulnerabilidades (actualizaciones de dependencias)
  - Backup y recuperación de datos

- **Gestión de Riesgos:**
  - Identificación de amenazas: acceso no autorizado, pérdida de datos, ataques de inyección
  - Medidas de mitigación documentadas
  - Plan de respuesta a incidentes básico

**5. GDPR (Unión Europea) - Buenas Prácticas Internacionales:**

Aunque no aplica directamente en Chile, GDPR establece estándares de oro para protección de datos:

**Principios Adoptados:**

- **Transparencia Algorítmica:**
  - Usuarios deben entender cómo la IA genera respuestas
  - Explicación de fuentes de conocimiento utilizadas
  - Feedback sobre calidad de respuestas

- **Derecho al Olvido:**
  - Capacidad de eliminar documentos del repositorio
  - Purga de datos de auditoría según política de retención

- **Responsabilidad y Ética:**
  - Uso ético de IA (no sesgos discriminatorios)
  - Verificación de respuestas generadas
  - Humano en el bucle para decisiones críticas

**6. UNESCO - Ética de la Inteligencia Artificial (2021):**

**Principios Aplicados:**

- **Transparencia:**
  - Documentación de cómo funciona el motor de IA
  - Claridad sobre limitaciones del sistema

- **Explicabilidad:**
  - Respuestas deben incluir referencias a fuentes
  - Usuarios pueden validar información

- **Responsabilidad Social:**
  - Uso educativo y ético de la IA
  - Beneficio para empleados y organización
  - No automatización de decisiones críticas sin supervisión humana

### Requerimientos de Dominio Específicos

**Gestión del Conocimiento Organizacional:**

1. **Conversión Conocimiento Tácito → Explícito (Modelo SECI - Nonaka & Takeuchi):**
   - Socialización: Captura de conocimiento de expertos mediante documentación
   - Externalización: Transformación de experiencias en manuales/guías
   - Combinación: Integración de múltiples fuentes de conocimiento
   - Internalización: Aprendizaje individual mediante IA personalizada

2. **Ciclo de Mejora Continua (PDCA - Deming):**
   - Plan: Definir qué conocimiento capturar
   - Do: Implementar carga y procesamiento de documentos
   - Check: Validar calidad de respuestas de IA
   - Act: Reentrenar modelo con feedback (RM1)

3. **Validación de Conocimiento:**
   - Versionado de documentos
   - Aprobación de contenido por expertos
   - Marcado de contenido obsoleto
   - Actualización periódica de base de conocimiento

---

## Innovation & Novel Patterns

### Patrones de Innovación del Prototipo

**1. RAG (Retrieval-Augmented Generation) con Cumplimiento Normativo:**

**Innovación:** Combinar IA generativa con recuperación de información garantizando privacidad.

**Cómo Funciona:**
1. Usuario hace consulta en lenguaje natural
2. Sistema busca documentos relevantes en base de conocimiento (Retrieval)
3. Contexto recuperado + consulta se envían a LLM
4. LLM genera respuesta fundamentada en documentos corporativos (Generation)
5. Respuesta incluye referencias a fuentes verificables

**Valor Diferencial:**
- **No alucinaciones:** IA responde solo con información del repositorio corporativo
- **Trazabilidad:** Cada respuesta referencia documentos fuente
- **Cumplimiento legal:** Datos nunca abandonan la infraestructura local, garantizando privacidad total

**2. Generación Automática de Contenido Formativo:**

**Innovación:** IA no solo responde, CREA material de capacitación personalizado.

**Capacidades:**
- **Resúmenes adaptativos:** Extrae puntos clave de documentos extensos
- **Quizzes automáticos:** Genera preguntas de evaluación basadas en contenido
- **Learning paths:** Sugiere secuencias de aprendizaje según necesidad del usuario

**Aplicación Práctica:**
- Empleado nuevo: IA genera "Guía de Inducción Personalizada" automáticamente
- Cambio de proceso: IA crea quiz de validación de nuevo conocimiento
- Capacitación continua: Ruta de aprendizaje progresiva adaptada al rol

**3. Arquitectura 100% Local con Modelo Open Source:**

**Innovación:** Implementación completamente on-premise que garantiza soberanía total de datos y cumplimiento normativo sin dependencias externas.

**Modelo Propuesto:**
- **Datos sensibles:** Permanecen en infraestructura local, nunca abandonan el sistema
- **Procesamiento IA:** Modelo Llama 3.1:8b-instruct cuantizado (q4_K_M) ejecutándose localmente vía Ollama
- **Control total:** Sin dependencia de terceros, sin costos recurrentes, sin conectividad requerida

**Ventajas:**
- Cumplimiento 100% de Ley 19.628 (datos nunca abandonan el sistema)
- Sin rate limits, sin costos por token, sin necesidad de internet
- Replicable para cualquier organización sin infraestructura cloud
- Modelo open source (Llama 3.1 bajo licencia Meta)
- Mayor control sobre respuestas y privacidad absoluta

**Especificaciones Técnicas:**
- **Modelo:** Meta Llama 3.1:8b-instruct cuantizado a 4-bit (q4_K_M)
- **Runtime:** Ollama (abstracción simple) o llama.cpp (control fino)
- **Requerimientos:** 8-16GB RAM, CPU moderna (AVX2) o GPU opcional (NVIDIA CUDA)
- **Rendimiento estimado:** 10-20 tokens/segundo en CPU, 40-60 tokens/s con GPU
- **Tamaño del modelo:** ~4.7GB en disco

**4. Modelo de Prefactibilidad Académica Rigurosa:**

**Innovación:** No es solo un "demo técnico", es evaluación integral de viabilidad.

**Componentes:**
- **Prefactibilidad Técnica:** ¿Funciona la tecnología? (Pruebas funcionales)
- **Prefactibilidad Operativa:** ¿Es usable y útil? (Pruebas de usabilidad)
- **Prefactibilidad Económica:** ¿Es sostenible? (Análisis costo-beneficio)

**Impacto:**
- Resultados académicos publicables
- Modelo replicable para otras empresas chilenas/latinoamericanas
- Base sólida para implementación futura real

### Validation Approach

**Validación de Innovaciones:**

**1. Validación Técnica:**
- **Pruebas de Precisión:** Evaluar % de respuestas correctas de IA (objetivo >80%)
- **Pruebas de Rendimiento:** Medir tiempos de respuesta (objetivo <2s)
- **Pruebas de Seguridad:** Intentar accesos no autorizados, inyección de código
- **Pruebas de Protección de Datos:** Verificar que datos de prueba no contengan PII real

**2. Validación de Usabilidad:**
- **Pruebas con usuarios reales:** Empleados simulados prueban consultas típicas
- **Métricas SUS (System Usability Scale):** Cuestionario estándar de usabilidad
- **Task Success Rate:** % de tareas completadas exitosamente
- **Time on Task:** Tiempo para resolver consultas

**3. Validación de Contenido Generado:**
- **Revisión humana:** Expertos validan calidad de resúmenes y quizzes
- **Comparación con material manual:** ¿IA genera contenido comparable?
- **Feedback de usuarios:** Calificación de utilidad de contenido generado

**4. Validación de Prefactibilidad:**
- **Análisis costo-beneficio:** Proyección de ROI de implementación real
- **Evaluación de escalabilidad:** ¿Puede manejar 100, 1000, 10000 usuarios?
- **Riesgos identificados:** Documentación de limitaciones y riesgos

**Fallback (Plan B si Innovaciones Fallan):**

- **Si RAG no alcanza precisión >80%:** Reducir alcance a búsqueda semántica + respuestas predefinidas
- **Si generación de contenido no es usable:** Enfocarse solo en Q&A conversacional
- **Si rendimiento <2s es inalcanzable:** Redefinir RNF2 a <5s con justificación técnica, considerar modelo más pequeño (Llama 3.1:3b)
- **Si hardware es insuficiente:** Usar modelo cuantizado más agresivo (q3 o q2) o cambiar a Phi-3 mini

---

## Web Application Specific Requirements

### Arquitectura Web de 3 Capas

**Separación de Responsabilidades:**

```
┌─────────────────────────────────────────┐
│   CAPA DE PRESENTACIÓN (Frontend)       │
│   - Interfaz web HTML/CSS/JS            │
│   - Framework: Flask templates o React  │
│   - Responsive design                   │
└──────────────┬──────────────────────────┘
               │ HTTP/HTTPS (API REST)
┌──────────────▼──────────────────────────┐
│   CAPA LÓGICA (Backend + Motor IA)      │
│   - API REST (Flask/FastAPI)            │
│   - Motor de IA Generativa (Python)     │
│   - Lógica de negocio                   │
│   - Gestión de sesiones y autenticación │
└──────────────┬──────────────────────────┘
               │ SQL Queries
┌──────────────▼──────────────────────────┐
│   CAPA DE DATOS (Base de Conocimiento)  │
│   - Base de datos: SQLite/PostgreSQL    │
│   - Almacenamiento de documentos        │
│   - Logs de auditoría                   │
└─────────────────────────────────────────┘
```

### Especificación de API REST

**Endpoints Principales:**

**Autenticación:**
```
POST /api/auth/login
- Body: { "username": "string", "password": "string" }
- Response: { "token": "JWT_TOKEN", "user_id": "int", "role": "string" }

POST /api/auth/logout
- Headers: Authorization: Bearer {token}
- Response: { "message": "Logout successful" }
```

**Gestión de Conocimiento:**
```
POST /api/knowledge/upload
- Headers: Authorization: Bearer {token}
- Body: multipart/form-data (archivo PDF/TXT + metadata)
- Response: { "document_id": "int", "status": "processed" }

GET /api/knowledge/documents
- Headers: Authorization: Bearer {token}
- Query params: ?category=string&limit=int&offset=int
- Response: { "documents": [ {id, title, category, upload_date} ] }

DELETE /api/knowledge/documents/{document_id}
- Headers: Authorization: Bearer {token}
- Response: { "message": "Document deleted" }
```

**Consultas IA:**
```
POST /api/ia/query
- Headers: Authorization: Bearer {token}
- Body: { "query": "string", "context_mode": "general|specific" }
- Response: {
    "answer": "string",
    "sources": [ {document_id, title, relevance_score} ],
    "response_time_ms": "int"
  }

POST /api/ia/generate/summary
- Headers: Authorization: Bearer {token}
- Body: { "document_id": "int" }
- Response: { "summary": "string" }

POST /api/ia/generate/quiz
- Headers: Authorization: Bearer {token}
- Body: { "document_id": "int", "num_questions": "int" }
- Response: { "quiz": [ {question, options, correct_answer} ] }
```

**Auditoría:**
```
GET /api/audit/logs
- Headers: Authorization: Bearer {token} (solo Admin)
- Query params: ?user_id=int&start_date=date&end_date=date
- Response: { "logs": [ {timestamp, user, action, resource} ] }
```

### Modelo de Autenticación y Autorización

**Autenticación:**

- **Método:** JWT (JSON Web Tokens)
- **Flujo:**
  1. Usuario envía credenciales a `/api/auth/login`
  2. Backend valida contra base de datos
  3. Si válido, genera JWT con payload: `{user_id, role, exp}`
  4. Cliente almacena token (sessionStorage o cookie HttpOnly)
  5. Todas las requests subsecuentes incluyen token en header `Authorization: Bearer {token}`

**Autorización (Roles):**

| Rol | Permisos |
|-----|----------|
| **Administrador** | - Gestionar usuarios<br>- Cargar/eliminar documentos<br>- Consultar IA<br>- Acceder logs de auditoría<br>- Configurar sistema |
| **Usuario** | - Consultar IA<br>- Ver documentos<br>- Generar contenido formativo<br>- Calificar respuestas |

**Control de Acceso:**

- Middleware de autenticación verifica token en cada request
- Middleware de autorización verifica rol según endpoint
- Respuestas de error: `401 Unauthorized` o `403 Forbidden`

### Gestión de Errores y Códigos HTTP

**Códigos de Respuesta:**

- `200 OK`: Operación exitosa
- `201 Created`: Recurso creado (ej. documento cargado)
- `400 Bad Request`: Error en parámetros de entrada
- `401 Unauthorized`: Token inválido o ausente
- `403 Forbidden`: Usuario no tiene permisos
- `404 Not Found`: Recurso no existe
- `500 Internal Server Error`: Error del servidor
- `503 Service Unavailable`: Servicio de IA local no disponible (ej. Ollama no iniciado)

**Formato de Errores:**
```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "El documento debe ser PDF o TXT",
    "details": { "field": "file_type", "received": "docx" }
  }
}
```

### Seguridad de la API

**Medidas de Seguridad:**

1. **HTTPS Obligatorio:** Todas las comunicaciones cifradas (RS4)
2. **Rate Limiting:** Límite de requests por minuto por usuario (prevenir abuso)
3. **CORS Configurado:** Solo orígenes permitidos
4. **Validación de Entrada:** Sanitización de inputs (prevenir inyección SQL/XSS)
5. **Tokens con Expiración:** JWT válido por 24 horas, requiere re-login
6. **Logging de Seguridad:** Intentos fallidos de login, accesos no autorizados (RS3)

---

## User Experience Principles

### Filosofía de Diseño

**Personalidad Visual del Producto:**

- **Profesional pero Accesible:** No intimidante, diseño limpio y moderno
- **Confiable:** Visual que transmite seguridad de datos
- **Intuitivo:** Minimiza fricción de aprendizaje

**Principios UX:**

1. **Claridad sobre Complejidad:**
   - Interfaces simples que ocultan complejidad técnica
   - Lenguaje claro, sin jerga técnica innecesaria
   - Feedback visual inmediato de acciones

2. **Eficiencia en la Tarea:**
   - Reducir clics para tareas comunes
   - Búsqueda/consulta accesible desde cualquier pantalla
   - Atajos de teclado para usuarios avanzados

3. **Tolerancia a Errores:**
   - Confirmaciones para acciones destructivas (eliminar documentos)
   - Mensajes de error constructivos (qué falló + cómo arreglarlo)
   - Recuperación fácil de errores (ej. deshacer)

4. **Consistencia:**
   - Patrones de diseño consistentes (botones, colores, tipografía)
   - Comportamiento predecible de elementos interactivos
   - Terminología uniforme en toda la interfaz

### Key Interactions (Interacciones Clave)

**1. Consulta Conversacional (Interacción Principal):**

**Flujo:**
```
Usuario escribe pregunta →
  Sistema muestra "Pensando..." (indicador de carga) →
    IA genera respuesta en <2s →
      Respuesta se renderiza con formato + fuentes →
        Usuario puede calificar respuesta (👍/👎)
```

**Diseño de Interfaz:**
- Estilo chat (mensajes alternados usuario/IA)
- Input text area con placeholder: "¿Qué necesitas saber?"
- Botón "Enviar" o Enter para consultar
- Historial de conversación visible (scroll infinito)
- Cada respuesta muestra: texto + fuentes + timestamp

**Elementos Mágicos:**
- Auto-sugerencias mientras escribe (búsquedas comunes)
- Animación suave de aparición de respuestas
- Resaltado de palabras clave en respuesta
- Links directos a documentos fuente

**2. Gestión Documental (Interacción Secundaria):**

**Flujo de Carga:**
```
Admin selecciona "Cargar documento" →
  Drag & drop archivo o selección manual →
    Sistema valida formato (PDF/TXT) →
      Extrae texto + solicita metadatos (categoría, descripción) →
        Confirma carga → Indexación en background →
          Notificación "Documento disponible"
```

**Diseño:**
- Zona drag & drop visual clara
- Validación en tiempo real de formato
- Barra de progreso de carga
- Vista de documentos en tabla/grid con filtros

**3. Generación de Contenido Formativo:**

**Flujo de Generación de Quiz:**
```
Usuario ve documento →
  Botón "Generar Quiz" →
    Modal: "¿Cuántas preguntas?" (5/10/15) →
      IA genera quiz en <5s →
        Visualización interactiva del quiz →
          Usuario puede responder en interfaz →
            Feedback inmediato correcto/incorrecto
```

**Diseño:**
- Botones de acción contextuales en cada documento
- Generación de contenido en modal/panel lateral
- Preview antes de guardar contenido generado
- Opciones de exportar (PDF, texto)

**4. Retroalimentación del Usuario:**

**Calificación de Respuestas:**
- Iconos 👍👎 en cada respuesta de IA
- Al calificar negativo: campo opcional "¿Qué falló?" (feedback cualitativo)
- Confirmación visual "Gracias por tu feedback"

**Mejora Continua:**
- Datos de calificación alimentan logs para análisis
- Dashboard admin muestra métricas de satisfacción
- Identificación de consultas problemáticas para mejorar modelo

### Flujos de Usuario Críticos

**Flujo 1: Empleado Nuevo - Primera Consulta**

**Objetivo:** Reducir tiempo hasta primera consulta exitosa a <5 minutos.

**Pasos:**
1. Login con credenciales proporcionadas por Admin
2. Landing page con tutorial interactivo rápido (30 segundos)
3. Prompt sugerido: "Haz tu primera pregunta, ej. ¿Cómo solicito vacaciones?"
4. Usuario escribe consulta → recibe respuesta útil
5. Sistema ofrece: "¿Quieres un resumen de políticas de RRHH?" (onboarding proactivo)

**Medición de Éxito:**
- Time to First Successful Query (TFSQ) < 5 min
- Tasa de abandono en primer login < 10%

**Flujo 2: Administrador - Carga de Documento Crítico**

**Objetivo:** Proceso de carga de documento completo en <2 minutos.

**Pasos:**
1. Login Admin → Dashboard
2. Botón "Cargar Documento" prominente
3. Drag & drop PDF → validación instantánea
4. Form metadatos pre-llenado con sugerencias (IA detecta categoría de contenido)
5. Click "Procesar" → barra progreso → confirmación
6. Documento indexado y consultable inmediatamente

**Medición de Éxito:**
- Time to Upload Complete < 2 min
- Tasa de error en carga < 5%

**Flujo 3: Usuario - Generación de Ruta de Aprendizaje**

**Objetivo:** Generar learning path personalizado en <3 clicks.

**Pasos:**
1. Usuario en interfaz de consulta
2. Pregunta: "¿Qué necesito aprender sobre [tema]?"
3. IA responde + botón "Crear ruta de aprendizaje"
4. Click → IA genera secuencia de documentos/temas
5. Usuario ve roadmap visual interactivo
6. Click en cada paso → acceso directo a contenido

**Medición de Éxito:**
- Clicks to Learning Path Generation = 3
- Tasa de adopción de learning paths generados > 40%

### Accesibilidad Básica

**Cumplimiento Mínimo:**

- **Contraste de colores:** WCAG 2.1 AA (mínimo 4.5:1 texto normal)
- **Navegación por teclado:** Todas las funciones accesibles vía teclado (Tab, Enter, Esc)
- **Labels semánticos:** Formularios con labels asociados
- **Mensajes de error accesibles:** Lectores de pantalla pueden leer errores
- **Responsive:** Funciona en desktop, tablet, mobile

*(Nota: Accesibilidad completa WCAG AAA es Growth Feature, no MVP)*

---

## Functional Requirements

Los requerimientos funcionales (RF) definen las capacidades específicas que el prototipo debe ejecutar. Se organizan por módulos y se alinean con los objetivos académicos del proyecto.

### Módulo 1: Gestión del Conocimiento

**RF1: Registro, Almacenamiento y Consulta de Conocimiento Organizacional**

**Descripción:**
El sistema debe permitir a los administradores registrar, almacenar y a los usuarios consultar información del repositorio de conocimiento corporativo de manera eficiente.

**Criterios de Aceptación:**
- El sistema acepta documentos en formatos PDF y TXT
- Los documentos se almacenan con metadatos: título, categoría, fecha de carga, autor, descripción
- Los usuarios pueden buscar documentos por título, categoría o palabras clave
- El sistema indexa el contenido de documentos para búsqueda de texto completo
- La base de conocimiento es persistente (sobrevive reinicios del sistema)

**Prioridad:** CRÍTICA (Sprint 2)

**Trazabilidad Académica:**
- Objetivo Específico 2: "Diseñar arquitectura funcional"
- Objetivo Específico 3: "Construir prototipo funcional con mecanismos de gestión de conocimiento"

---

**RF3: Gestión Documental (Carga, Clasificación e Indexación)**

**Descripción:**
El sistema debe gestionar el ciclo de vida de documentos: ingreso, procesamiento, clasificación automática, indexación y eliminación.

**Criterios de Aceptación:**

**Carga de Documentos:**
- Interfaz de carga soporta drag & drop y selección manual
- Validación de formato: solo PDF y TXT permitidos
- Validación de tamaño: límite de 10MB por archivo
- Extracción automática de texto de PDFs usando bibliotecas Python (PyPDF2, pdfplumber)
- Feedback visual de progreso de carga

**Clasificación:**
- Administrador asigna categoría manual (ej. "Políticas RRHH", "Procedimientos Operativos", "Manuales Técnicos")
- (Opcional Growth) IA sugiere categoría basada en contenido

**Indexación:**
- Sistema crea índice invertido de palabras clave para búsqueda rápida
- Indexación ocurre en background (no bloquea interfaz)
- Documentos indexados disponibles para consultas IA en <1 minuto

**Eliminación:**
- Administrador puede eliminar documentos
- Confirmación antes de eliminación permanente
- Logs de auditoría registran eliminaciones (RS3)

**Prioridad:** CRÍTICA (Sprint 2)

**Casos de Uso Asociados:**
- CU-002: Gestionar Documentos (ver sección UML)

---

### Módulo 2: Interacción con IA Generativa

**RF2: Consultas en Lenguaje Natural y Respuestas Contextualizadas**

**Descripción:**
Los usuarios deben poder ingresar consultas en lenguaje natural (español) y recibir respuestas precisas y contextualizadas generadas por IA, fundamentadas en la base de conocimiento corporativa.

**Criterios de Aceptación:**

**Interfaz de Consulta:**
- Campo de texto para escribir preguntas (mínimo 10 caracteres, máximo 500)
- Botón "Enviar" o tecla Enter para enviar consulta
- Indicador visual de "procesando" mientras IA genera respuesta

**Procesamiento de Consulta:**
- Sistema usa técnica RAG (Retrieval-Augmented Generation):
  1. **Retrieval:** Busca documentos relevantes en base de conocimiento (top 3-5 más relevantes)
  2. **Augmentation:** Construye contexto con fragmentos de documentos recuperados
  3. **Generation:** Envía contexto + consulta a Llama 3.1 local ejecutándose vía Ollama
  4. El modelo genera respuesta fundamentada en contexto proporcionado

**Respuesta:**
- Respuesta renderizada en formato legible (párrafos, listas si aplica)
- Incluye sección "Fuentes consultadas" con links a documentos fuente
- Tiempo de respuesta < 2 segundos (RNF2)
- Si no encuentra información relevante: mensaje claro "No encontré información sobre [tema]. ¿Podrías reformular tu pregunta?"

**Historial:**
- Las consultas y respuestas se muestran en formato conversacional (chat)
- Historial persiste durante sesión de usuario
- (Opcional Growth) Historial guardado entre sesiones

**Prioridad:** CRÍTICA (Sprint 2-3)

**Trazabilidad Académica:**
- Objetivo Específico 3: "Construir prototipo con asistencia en procesos de capacitación"
- Objetivo Específico 4: "Validar desempeño en automatización de gestión del conocimiento"

**Casos de Uso Asociados:**
- CU-001: Consultar Conocimiento a través de IA

---

**RF4: Generación de Contenido Formativo**

**Descripción:**
La IA debe ser capaz de generar nuevo material de capacitación automáticamente: resúmenes, quizzes de evaluación y learning paths (rutas de aprendizaje).

**Criterios de Aceptación:**

**Generación de Resúmenes:**
- Usuario selecciona documento → click "Generar Resumen"
- IA extrae puntos clave del documento (máximo 300 palabras)
- Resumen incluye: conceptos principales, pasos clave, información crítica
- Tiempo de generación < 5 segundos

**Generación de Quizzes:**
- Usuario selecciona documento → click "Generar Quiz"
- Usuario especifica número de preguntas (5, 10, 15)
- IA genera preguntas de opción múltiple (4 opciones, 1 correcta)
- Cada pregunta evalúa comprensión de conceptos del documento
- Tiempo de generación < 10 segundos
- Quiz se puede exportar a texto o responder interactivamente en interfaz

**Generación de Learning Paths (Opcional en MVP):**
- Usuario pregunta "¿Qué necesito aprender sobre [tema]?"
- IA analiza documentos disponibles sobre el tema
- Genera secuencia recomendada de aprendizaje (orden lógico de documentos/temas)
- Muestra roadmap visual

**Validación de Contenido Generado:**
- Contenido generado incluye disclaimer: "Generado por IA - validar con supervisor"
- Administrador puede revisar y aprobar contenido antes de publicar
- Logs de auditoría registran contenido generado (quién, cuándo, qué)

**Prioridad:** ALTA (Sprint 3)

**Trazabilidad Académica:**
- Objetivo Específico 3: "Construir prototipo con mecanismos de asistencia en capacitación"
- Diferenciador clave del proyecto: No solo Q&A, sino creación de contenido formativo

**Casos de Uso Asociados:**
- CU-003: Generar Contenido de Capacitación

---

**RF5: Retroalimentación de Usuarios**

**Descripción:**
El prototipo debe ofrecer retroalimentación textual clara al usuario y permitir la calificación de la calidad de las respuestas para mejora continua.

**Criterios de Aceptación:**

**Retroalimentación del Sistema al Usuario:**
- Mensajes de confirmación para acciones exitosas (ej. "Documento cargado correctamente")
- Mensajes de error constructivos (qué falló + sugerencia de solución)
- Indicadores de progreso para operaciones largas (carga, indexación)
- Tiempos de espera estimados ("Procesando... ~5 segundos")

**Calificación de Respuestas:**
- Cada respuesta de IA tiene botones 👍 (útil) / 👎 (no útil)
- Al calificar negativo: campo opcional de texto "¿Qué falló?" (máximo 200 caracteres)
- Calificaciones se almacenan en base de datos con timestamp, user_id, query_id
- Dashboard de administrador muestra métricas de satisfacción:
  - % respuestas positivas vs negativas
  - Consultas con peor calificación (para análisis)

**Mejora Continua:**
- Datos de retroalimentación alimentan logs de análisis
- Identificación de gaps de conocimiento (temas con muchas respuestas negativas)
- Base para reentrenamiento del modelo (RM1)

**Prioridad:** MEDIA (Sprint 3-4)

**Trazabilidad Académica:**
- Objetivo Específico 4: "Validar desempeño del prototipo"
- Sección 6.7 Metodología: "Validación de la metodología (retroalimentación)"

---

### Módulo 3: Administración y Seguridad

**RF6: Autenticación de Usuarios (RS1)**

**Descripción:**
El sistema debe requerir autenticación básica de usuario mediante credenciales únicas antes de acceder a funcionalidades.

**Criterios de Aceptación:**
- Pantalla de login con campos: username y password
- Validación de credenciales contra base de datos de usuarios
- Contraseñas almacenadas con hash seguro (bcrypt o similar)
- Generación de token JWT tras login exitoso
- Token incluye: user_id, role, fecha de expiración (24 horas)
- Sesión expira tras 24 horas de inactividad (requiere re-login)
- Logout manual invalida token

**Gestión de Usuarios (Solo Admin):**
- Admin puede crear nuevos usuarios
- Datos mínimos: username (único), password, role (Admin/Usuario), nombre completo
- Admin puede desactivar usuarios (no eliminar, para mantener trazabilidad)

**Prioridad:** CRÍTICA (Sprint 2)

**Cumplimiento Legal:** Ley 19.628 (protección de datos), ISO 27001 (control de acceso)

---

**RF7: Control de Acceso Basado en Roles (RS2)**

**Descripción:**
Debe existir un control de acceso basado en roles (RBAC) para la consulta y modificación de la base de conocimiento.

**Criterios de Aceptación:**

**Roles Definidos:**

| Rol | Permisos |
|-----|----------|
| **Administrador** | - Gestionar usuarios (crear, desactivar)<br>- Cargar/editar/eliminar documentos<br>- Consultar IA<br>- Generar contenido formativo<br>- Acceder logs de auditoría<br>- Ver dashboard de métricas |
| **Usuario** | - Consultar IA<br>- Ver lista de documentos (solo lectura)<br>- Generar contenido formativo (resúmenes, quizzes)<br>- Calificar respuestas |

**Implementación:**
- Middleware de autorización verifica rol antes de ejecutar acciones
- Endpoints sensibles protegidos por decorador `@require_role('admin')`
- Intentos de acceso no autorizado registrados en logs (RS3)
- UI adapta opciones según rol (ej. botón "Cargar Documento" solo visible para Admin)

**Prioridad:** CRÍTICA (Sprint 2)

**Cumplimiento Legal:** ISO 27001 (gestión de accesos)

---

**RF8: Trazabilidad y Auditoría (RS3)**

**Descripción:**
El sistema debe mantener un registro de auditoría de todas las interacciones clave con la base de conocimiento y el motor de IA.

**Criterios de Aceptación:**

**Eventos Auditados:**
- Login/logout de usuarios (timestamp, user_id, IP)
- Carga de documentos (quién, qué, cuándo)
- Eliminación de documentos (quién, qué, cuándo, documento eliminado)
- Consultas a IA (user_id, query, timestamp, response_time)
- Calificaciones de respuestas (user_id, query_id, rating, feedback_text)
- Intentos de acceso no autorizado (user_id, endpoint, timestamp)
- Errores del sistema (tipo, timestamp, stack trace)

**Almacenamiento:**
- Tabla `audit_logs` en base de datos
- Campos: id, timestamp, user_id, event_type, resource, action, details (JSON), ip_address
- Logs retenidos por mínimo 6 meses (política de retención)

**Acceso a Logs:**
- Solo Administradores acceden a logs de auditoría
- Interfaz de consulta con filtros: fecha, usuario, tipo de evento
- Exportación de logs a CSV para análisis externo

**Prioridad:** ALTA (Sprint 2-4)

**Cumplimiento Legal:** Ley 19.628 (trazabilidad), ISO 27001 (registros de seguridad)

---

### Resumen de Requerimientos Funcionales

| ID | Descripción | Prioridad | Sprint |
|----|-------------|-----------|--------|
| RF1 | Registro, almacenamiento y consulta de conocimiento | CRÍTICA | 2 |
| RF2 | Consultas en lenguaje natural con respuestas IA | CRÍTICA | 2-3 |
| RF3 | Gestión documental (carga, clasificación, indexación) | CRÍTICA | 2 |
| RF4 | Generación de contenido formativo (resúmenes, quizzes) | ALTA | 3 |
| RF5 | Retroalimentación de usuarios (calificación de respuestas) | MEDIA | 3-4 |
| RF6 | Autenticación de usuarios (RS1) | CRÍTICA | 2 |
| RF7 | Control de acceso basado en roles (RS2) | CRÍTICA | 2 |
| RF8 | Trazabilidad y auditoría (RS3) | ALTA | 2-4 |

**Trazabilidad con Objetivos Académicos:**

- **Objetivo Específico 2** (Diseñar arquitectura): RF1, RF3, RF6, RF7
- **Objetivo Específico 3** (Construir prototipo): RF2, RF4, RF5, RF8
- **Objetivo Específico 4** (Pruebas): Todos los RF (validación funcional)
- **Objetivo Específico 5** (Evaluar prefactibilidad): Todos los RF (demostración de viabilidad)

---

## Non-Functional Requirements

Los requerimientos no funcionales (RNF) definen características de calidad del sistema que no son funcionalidades específicas, pero son críticos para el éxito del prototipo.

### RNF1: Usabilidad

**Definición:**
La interfaz debe ser intuitiva, adaptable y diseñada bajo principios de experiencia de usuario (UX), minimizando la fricción de aprendizaje.

**Criterios Medibles:**

- **System Usability Scale (SUS):** Puntuación ≥70 (considerado "bueno" en escala SUS)
  - Aplicar cuestionario SUS de 10 preguntas a mínimo 5 usuarios de prueba

- **Task Success Rate:** ≥80% de tareas completadas exitosamente sin ayuda
  - Tareas típicas: login, consulta IA, carga documento, generación de quiz

- **Time to First Successful Query:** <5 minutos para usuario nuevo
  - Métrica clave: tiempo desde login inicial hasta primera consulta respondida satisfactoriamente

- **Error Recovery:** Usuarios recuperan de errores en ≤2 intentos
  - Mensajes de error deben ser lo suficientemente claros para auto-corrección

**Técnicas de Diseño UX Aplicadas:**

- Navegación simple con máximo 3 niveles de profundidad
- Consistencia visual: paleta de colores, tipografía, iconografía coherentes
- Feedback inmediato de acciones (ej. confirmaciones, indicadores de carga)
- Diseño responsive: adaptable a desktop (1920x1080) y tablet (1024x768)
- Lenguaje claro y directo (sin jerga técnica innecesaria)

**Validación:**
- **Pruebas de Usabilidad (Sprint 3):** 5-10 usuarios de prueba ejecutan tareas guiadas
- **Análisis de métricas:** Task completion rate, time on task, error rate
- **Feedback cualitativo:** Entrevistas post-prueba sobre experiencia

**Prioridad:** ALTA

**Trazabilidad Académica:**
- Objetivo Específico 4: "Realizar pruebas de usabilidad del prototipo"
- Capítulo VII: "7.3 Pruebas del prototipo (usabilidad)"

---

### RNF2: Rendimiento

**Definición:**
El tiempo de respuesta del motor de IA por consulta debe ser inferior a 2 segundos para garantizar una experiencia fluida.

**Criterios Medibles:**

**Tiempos de Respuesta:**

| Operación | Tiempo Objetivo | Tiempo Crítico (No Exceder) |
|-----------|-----------------|------------------------------|
| Consulta IA (prompt → respuesta) | < 2 segundos | < 5 segundos |
| Carga de documento (upload + procesamiento) | < 30 segundos | < 60 segundos |
| Generación de resumen | < 5 segundos | < 10 segundos |
| Generación de quiz (5 preguntas) | < 10 segundos | < 20 segundos |
| Login | < 1 segundo | < 3 segundos |
| Búsqueda de documentos | < 1 segundo | < 3 segundos |

**Medición:**
- Logs de rendimiento registran tiempo de cada operación
- Dashboard de admin muestra métricas de rendimiento:
  - Tiempo promedio de respuesta IA (últimas 100 consultas)
  - Consultas que excedieron objetivo de 2s (% del total)
  - P95 y P99 (percentil 95 y 99 de tiempos de respuesta)

**Optimizaciones Técnicas:**

- **Caché de Resultados:** Consultas idénticas recientes se sirven de caché (ej. últimos 5 minutos)
- **Indexación Eficiente:** Índice invertido para búsqueda rápida de documentos relevantes
- **Modelo Pre-cargado:** Mantener Llama 3.1 cargado en memoria para evitar latencia de inicialización
- **Paginación:** Resultados de búsqueda paginados (máximo 20 documentos por página)
- **Procesamiento Asíncrono:** Indexación de documentos en background (no bloquea UI)
- **Context Pruning:** Limitar contexto a tokens más relevantes para reducir tiempo de inferencia

**Contingencia:**
- Si rendimiento consistente <2s no es alcanzable con recursos disponibles:
  - Documentar limitación técnica en Informe de Prefactibilidad
  - Redefinir objetivo a <5s con justificación (limitaciones de CPU, memoria RAM disponible)
  - Proponer soluciones: GPU dedicada, modelo más pequeño (3b), cuantización más agresiva

**Prioridad:** ALTA

**Trazabilidad Académica:**
- Objetivo Específico 4: "Validar desempeño del prototipo"
- Capítulo VII: "7.3 Pruebas del prototipo (funcionales)"
- Informe de Prefactibilidad: Evaluación de rendimiento técnico

---

### RNF3: Escalabilidad

**Definición:**
El diseño de la arquitectura debe permitir la futura integración de nuevos módulos y el escalamiento del volumen de usuarios y documentos.

**Criterios de Diseño Escalable:**

**Arquitectura:**
- **Separación de capas:** Frontend, Backend, Datos independientes (permite escalar cada capa por separado)
- **API RESTful:** Comunicación stateless entre capas (facilita balanceo de carga)
- **Base de datos relacional normalizada:** Evita redundancia, facilita crecimiento

**Capacidad Proyectada:**

| Métrica | MVP (Laboratorio) | Proyección Producción |
|---------|-------------------|-----------------------|
| Usuarios concurrentes | 5-10 | 100-500 |
| Documentos en repositorio | 50-100 | 1,000-10,000 |
| Consultas IA por día | 100-500 | 10,000-50,000 |
| Tamaño de base de datos | <1 GB | 10-100 GB |

**Pruebas de Escalabilidad (Sprint 4):**

- **Carga de volumen de documentos:** Cargar 100 documentos y medir:
  - Tiempo de indexación total
  - Degradación de tiempo de búsqueda (debe ser <10% vs 10 documentos)

- **Simulación de usuarios concurrentes:** Usar herramienta (ej. Locust, JMeter) para simular 10 usuarios concurrentes:
  - Medir tiempos de respuesta bajo carga
  - Identificar cuellos de botella (CPU, RAM, I/O, cola de inferencia)

**Limitaciones Conocidas:**

- **Hardware de laboratorio:** Recursos limitados (CPU, RAM, almacenamiento)
- **Inferencia local:** Velocidad limitada por capacidad computacional disponible (CPU vs GPU)
- **Sin infraestructura cloud:** No auto-scaling, no balanceadores de carga

**Recomendaciones para Escalamiento Futuro:**

- Migrar a cloud (AWS, Azure, GCP) con auto-scaling
- Implementar caché distribuido (Redis) para reducir carga en base de datos
- Usar colas de mensajes (RabbitMQ, Kafka) para procesamiento asíncrono
- Considerar base de datos vectorial (Pinecone, Weaviate) para búsqueda semántica escalable

**Prioridad:** MEDIA

**Trazabilidad Académica:**
- Objetivo Específico 5: "Evaluar prefactibilidad técnica y potencial de integración en entornos empresariales reales"
- Informe de Prefactibilidad: Análisis de escalabilidad

---

### RNF4: Interoperabilidad

**Definición:**
El sistema debe diseñarse para ser integrable con sistemas externos a través de una API REST bien documentada.

**Criterios de Interoperabilidad:**

**Estándares Abiertos:**
- API RESTful siguiendo convenciones HTTP (GET, POST, PUT, DELETE)
- Formato de datos: JSON (estándar web)
- Autenticación: JWT (JSON Web Tokens) - estándar OAuth 2.0 compatible
- Versionado de API: `/api/v1/...` (facilita cambios futuros sin romper clientes)

**Documentación de API:**
- Especificación OpenAPI 3.0 (Swagger)
- Documentación generada automáticamente (ej. con Flask-RESTX, FastAPI auto-docs)
- Incluye: endpoints, métodos, parámetros, ejemplos de request/response, códigos de error

**Ejemplos de Integración Futura:**

- **Sistema RRHH:** Importar automáticamente nuevos empleados como usuarios
- **Plataforma LMS:** Exportar quizzes generados a Moodle/Canvas
- **Dashboard BI:** Conectar métricas de uso a herramientas de analítica (Tableau, Power BI)
- **Chatbot corporativo:** Integrar motor de IA como backend de chatbot en Slack/Teams

**Prueba de Interoperabilidad (Sprint 4):**

- Crear cliente de prueba externo (script Python o Postman collection)
- Demostrar llamadas a API desde fuera del frontend:
  - Autenticación vía API
  - Consulta a motor de IA vía API
  - Recuperación de documentos vía API

**Prioridad:** MEDIA

**Trazabilidad Académica:**
- Objetivo Específico 5: "Potencial de integración en entornos empresariales reales"
- Arquitectura de 3 capas con API REST (Diseño Conceptual)

---

### Seguridad (RS1-RS5)

Los requerimientos de seguridad son no-funcionales pero críticos. Se detallan aquí para completitud.

**RS1: Autenticación** (ver RF6)

**RS2: Control de Acceso Basado en Roles** (ver RF7)

**RS3: Trazabilidad** (ver RF8)

**RS4: Cifrado**

**Definición:**
La base de conocimiento debe estar cifrada en reposo, y las comunicaciones cifradas mediante HTTPS.

**Criterios:**

- **Cifrado en Tránsito:**
  - Todas las comunicaciones HTTP usan HTTPS (TLS 1.2+)
  - Certificado SSL/TLS válido (puede ser auto-firmado para laboratorio, pero debe estar configurado)
  - Headers de seguridad: `Strict-Transport-Security`, `X-Content-Type-Options`

- **Cifrado en Reposo:**
  - Base de datos cifrada a nivel de archivo (ej. SQLite con SQLCipher, PostgreSQL con pgcrypto)
  - Contraseñas de usuarios hasheadas con bcrypt (salt único por usuario)
  - Tokens JWT firmados con clave secreta (HS256 o RS256)

**Prioridad:** CRÍTICA

**Cumplimiento Legal:** Ley 19.628, ISO 27001

---

**RS5: Confidencialidad y Anonimización**

**Definición:**
Se deben aplicar técnicas de anonimización y minimización de datos para cumplir con la ley chilena de protección de datos (Ley 19.628).

**Criterios:**

- **Anonimización de Datos de Prueba:**
  - Ningún dato personal real de empleados de Banmédica en el sistema
  - Datos de prueba: nombres ficticios, RUTs sintéticos, correos de ejemplo
  - Documentos de prueba: versiones anonimizadas de manuales reales (o completamente ficticios)

- **Minimización de Datos:**
  - Solo se recopilan datos estrictamente necesarios (username, password hash, role)
  - No se solicita información personal sensible innecesaria (edad, género, dirección, etc.)

- **Técnicas de Anonimización:**
  - Enmascaramiento: reemplazar nombres reales con ficticios
  - Generalización: "Área Metropolitana" en vez de dirección exacta
  - Datos sintéticos: generados algorítmicamente (ej. con Faker library)

**Validación:**
- Revisión manual de documentos de prueba antes de carga
- Escaneo automatizado de datos personales (ej. regex para RUT chileno) con advertencia

**Prioridad:** CRÍTICA

**Cumplimiento Legal:** Ley 19.628 (artículo 4: consentimiento y minimización)

---

### Resumen de Requerimientos No Funcionales

| ID | Categoría | Descripción | Métrica Objetivo | Prioridad |
|----|-----------|-------------|------------------|-----------|
| RNF1 | Usabilidad | Interfaz intuitiva | SUS ≥70, Task Success ≥80% | ALTA |
| RNF2 | Rendimiento | Tiempo de respuesta IA | < 2 segundos | ALTA |
| RNF3 | Escalabilidad | Arquitectura escalable | Soportar 100 docs sin degradación >10% | MEDIA |
| RNF4 | Interoperabilidad | API REST documentada | OpenAPI 3.0, integración vía API demostrada | MEDIA |
| RS4 | Seguridad | Cifrado | HTTPS + DB cifrada | CRÍTICA |
| RS5 | Seguridad | Confidencialidad | Anonimización completa de datos de prueba | CRÍTICA |

---

## Implementation Planning

### Metodología de Desarrollo: Scrum + Prefactibilidad

**Justificación de la Metodología:**

La metodología Scrum fue seleccionada por su:

- **Adaptabilidad:** IA generativa requiere ajustes iterativos de modelos y prompts
- **Validación Temprana:** Sprints permiten validar funcionalidad en fases tempranas
- **Trazabilidad:** Cada sprint genera entregables medibles
- **Gestión de Riesgos:** Retrospectivas identifican problemas y ajustan curso

**Integración con Prefactibilidad Tecnológica:**

- Scrum maneja el **desarrollo** del prototipo
- Prefactibilidad maneja la **evaluación** de viabilidad técnica/operativa/económica
- Sprint 4 se dedica completamente a análisis de prefactibilidad

### Estructura de Sprints (5 Sprints)

**Duración de Sprints:** 2-3 semanas cada uno (ajustable según calendario académico)

**Roles Scrum:**

- **Product Owner:** Profesor Guía (Cristian Rojas Catalan) - define prioridades, valida entregables
- **Scrum Master:** Andres Amaya Garces - facilita proceso, elimina impedimentos
- **Equipo de Desarrollo:** Andres Amaya, Marco Ortiz, Jorge Santander

**Ceremonias Scrum:**

- **Sprint Planning:** Inicio de cada sprint - definir objetivos y tareas (Product Backlog → Sprint Backlog)
- **Daily Scrum:** Reuniones cortas (15 min) - sincronización del equipo (qué hice, qué haré, impedimentos)
- **Sprint Review:** Final de sprint - demostración de entregables al Product Owner
- **Sprint Retrospective:** Lecciones aprendidas - qué mejorar en próximo sprint

### Desglose de Sprints

**Sprint 0: Planificación Inicial y Levantamiento de Requerimientos**

**Duración:** 2 semanas

**Objetivo:** Establecer fundamentos del proyecto, definir requerimientos completos y preparar entorno de desarrollo.

**Actividades:**

1. **Análisis de Contexto:**
   - Revisar documentación de Isapre Banmédica (contexto organizacional)
   - Identificar stakeholders y fuentes de información
   - Análisis de problema (Diagrama de Ishikawa completado)

2. **Levantamiento de Requerimientos:**
   - Técnicas: análisis documental, benchmarking de soluciones existentes
   - Especificación de RF, RNF, RS, RM (ver secciones anteriores de este PRD)
   - Documentar Especificación de Requerimientos del Sistema (ERS)

3. **Product Backlog Inicial:**
   - Crear backlog priorizado de user stories
   - Estimación de esfuerzo (story points)
   - Definir Definition of Done (DoD) para cada tipo de entregable

4. **Setup de Entorno:**
   - Configurar repositorio Git
   - Setup de entorno de desarrollo (Python, librerías, IDE)
   - Configurar herramienta de gestión (Trello/GitHub Projects)

5. **Planificación de Sprints:**
   - Cronograma detallado de 5 sprints
   - Matriz RACI (quién hace qué)
   - Plan de riesgos inicial

**Entregables:**

- Product Backlog completo y priorizado
- Especificación de Requerimientos (ERS) - documento académico formal
- Matriz RACI
- Cronograma de sprints
- Entorno de desarrollo configurado

**Criterios de Éxito:**

- Product Backlog tiene ≥90% de requerimientos identificados
- ERS aprobada por Product Owner
- Equipo tiene claridad de alcance y objetivos

---

**Sprint 1: Diseño Conceptual y Arquitectura**

**Duración:** 2-3 semanas

**Objetivo:** Diseñar la arquitectura completa del sistema y modelar con UML según estándares académicos.

**Actividades:**

1. **Arquitectura de Sistema:**
   - Diseñar modelo de 3 capas (Frontend, Backend, Datos)
   - Definir tecnologías por capa (Python, Flask/FastAPI, SQLite/PostgreSQL)
   - Diseñar API REST (endpoints, métodos, autenticación)
   - Documentar decisiones arquitectónicas (ADRs - Architecture Decision Records)

2. **Modelamiento UML:**
   - **Diagrama de Casos de Uso:** Identificar actores (Admin, Usuario), casos de uso principales (CU-001 a CU-005)
   - **Documentación de Casos de Uso:** Plantilla completa por cada CU (objetivo, actores, precondiciones, flujo normal, flujos alternos, excepciones)
   - **Diagrama de Componentes:** Mostrar despliegue lógico de Frontend, API Gateway, Motor de IA, Base de Datos
   - **Modelo Entidad-Relación (E-R):** Diseñar esquema de base de datos (entidades: Usuario, Documento, Consulta, AuditLog, Feedback)

3. **Diseño de Seguridad:**
   - Modelo de autenticación (JWT)
   - Modelo de autorización (RBAC)
   - Plan de cifrado (HTTPS, DB encryption)
   - Estrategia de anonimización de datos

4. **Prototipo de Interfaz (Wireframes):**
   - Sketches de pantallas principales: Login, Dashboard, Consulta IA, Gestión Docs
   - Flujos de usuario (user journeys)

**Entregables:**

- Documento de Arquitectura del Sistema (formal académico)
- Diagramas UML completos:
  - Casos de Uso (con documentación exhaustiva de cada CU)
  - Componentes
  - Entidad-Relación (E-R)
- Especificación de API REST (OpenAPI/Swagger)
- Wireframes de interfaz

**Criterios de Éxito:**

- Diagramas UML completos y validados por Product Owner
- Arquitectura técnicamente sólida (revisión de pares)
- Documentación de casos de uso cubre ≥95% de funcionalidades

**Trazabilidad Académica:**
- Objetivo Específico 2: "Diseñar la arquitectura conceptual y funcional"
- Capítulo VI: "6.5 Modelamiento UML / arquitectura del sistema"

---

**Sprint 2: Desarrollo del Motor de IA Generativa (Backend)**

**Duración:** 3 semanas

**Objetivo:** Construir el núcleo del sistema - backend funcional con motor de IA, base de datos y API REST operativa.

**Actividades:**

1. **Base de Datos:**
   - Implementar esquema de base de datos (SQLite para desarrollo, PostgreSQL para producción)
   - Crear tablas: usuarios, documentos, consultas, audit_logs, feedback
   - Scripts de migración y seed data (datos de prueba anonimizados)

2. **Motor de IA Generativa:**
   - Configurar e integrar Llama 3.1:8b local vía Ollama
   - Implementar pipeline RAG:
     - Módulo de retrieval: búsqueda semántica de documentos relevantes
     - Módulo de augmentation: construcción de contexto para el modelo
     - Módulo de generation: envío de prompt + contexto a LLM, recepción de respuesta
   - Procesamiento de documentos:
     - Extracción de texto de PDFs (PyPDF2, pdfplumber)
     - Chunking de documentos largos
     - Generación de embeddings para búsqueda semántica (opcional: usar FAISS, Chroma)

3. **API REST:**
   - Implementar endpoints definidos en diseño (Sprint 1)
   - Autenticación JWT
   - Middleware de autorización RBAC
   - Validación de inputs (esquemas Pydantic)
   - Manejo de errores (excepciones, códigos HTTP)

4. **Funcionalidades Core:**
   - RF1: Gestión de conocimiento (CRUD documentos)
   - RF2: Consultas en lenguaje natural
   - RF3: Indexación de documentos
   - RF6: Autenticación
   - RF7: Control de acceso
   - RF8: Logging de auditoría

5. **Pruebas Unitarias:**
   - Test coverage ≥70% de código backend
   - Tests de API (pytest, requests)

**Entregables:**

- Backend funcional (código Python)
- Base de datos operativa con datos de prueba
- Motor de IA respondiendo consultas
- API REST documentada y testeada
- Repositorio de conocimiento con 20-50 documentos de prueba indexados

**Criterios de Éxito:**

- Consulta de prueba a IA responde en <2 segundos
- API REST pasa todas las pruebas unitarias
- Autenticación y roles funcionan correctamente
- Logs de auditoría registran eventos clave

**Trazabilidad Académica:**
- Objetivo Específico 3: "Construir y poner en marcha prototipo funcional"
- Capítulo VII: "7.2 Implementación del prototipo"

---

**Sprint 3: Interfaz de Usuario y Pruebas de Usabilidad**

**Duración:** 2-3 semanas

**Objetivo:** Desarrollar frontend completo, integrar con backend y validar usabilidad con usuarios de prueba.

**Actividades:**

1. **Desarrollo de Frontend:**
   - Implementar pantallas diseñadas en wireframes (Sprint 1)
   - Tecnologías: HTML5, CSS3, JavaScript (o framework: Flask templates, React)
   - Pantallas principales:
     - Login/Logout
     - Dashboard (Admin vs Usuario)
     - Interfaz de consulta conversacional (chat)
     - Panel de gestión de documentos (Admin)
     - Visualización de respuestas con fuentes
     - Generación de contenido formativo (botones de resumen/quiz)
   - Diseño responsive (desktop + tablet)

2. **Integración Frontend-Backend:**
   - Consumo de API REST desde frontend (fetch/axios)
   - Manejo de tokens JWT (almacenamiento, inclusión en headers)
   - Manejo de estados de carga (spinners, progress bars)
   - Manejo de errores (mensajes user-friendly)

3. **Funcionalidades de Interfaz:**
   - RF4: Generación de resúmenes y quizzes (botones en UI)
   - RF5: Calificación de respuestas (botones 👍👎)
   - Historial de conversación
   - Feedback visual de acciones

4. **Pruebas de Usabilidad:**
   - Reclutar 5-10 usuarios de prueba (compañeros, profesores, externos)
   - Definir tareas de prueba:
     - Tarea 1: Login y hacer primera consulta
     - Tarea 2: Cargar un documento (Admin)
     - Tarea 3: Generar un quiz de un documento
     - Tarea 4: Calificar una respuesta
   - Métricas: task success rate, time on task, errores cometidos
   - Cuestionario SUS (System Usability Scale)
   - Entrevistas post-prueba: feedback cualitativo

5. **Iteraciones de Mejora:**
   - Analizar resultados de pruebas de usabilidad
   - Identificar pain points
   - Implementar mejoras críticas (ajustes de UI/UX)

**Entregables:**

- Frontend funcional completo
- Integración frontend-backend operativa (sistema end-to-end)
- Reporte de Pruebas de Usabilidad (documento académico formal)
  - Metodología de pruebas
  - Métricas obtenidas (SUS score, task success rate, etc.)
  - Hallazgos y recomendaciones
  - Evidencias (screenshots, videos de sesiones, cuestionarios)

**Criterios de Éxito:**

- Sistema completo funciona end-to-end (login → consulta → respuesta → feedback)
- Puntuación SUS ≥70
- Task success rate ≥80%
- Feedback cualitativo mayormente positivo

**Trazabilidad Académica:**
- Objetivo Específico 4: "Realizar pruebas de usabilidad"
- Capítulo VII: "7.3 Pruebas del prototipo (usabilidad)"

---

**Sprint 4: Evaluación de Prefactibilidad**

**Duración:** 2-3 semanas

**Objetivo:** Realizar pruebas exhaustivas (funcionales, seguridad, rendimiento) y elaborar el Informe de Prefactibilidad completo.

**Actividades:**

1. **Pruebas Funcionales Exhaustivas:**
   - Validar todos los RF (RF1-RF8) funcionan según criterios de aceptación
   - Pruebas de caja negra: inputs válidos, inválidos, casos borde
   - Verificar flujos normales y alternativos de casos de uso
   - Documentar resultados: casos de prueba ejecutados, resultados (pass/fail), bugs encontrados

2. **Pruebas de Seguridad:**
   - Verificar RS1-RS5 cumplidos
   - Intentos de acceso no autorizado (verificar logs de auditoría)
   - Pruebas de inyección SQL (inputs maliciosos)
   - Verificar cifrado HTTPS activo
   - Verificar anonimización de datos de prueba

3. **Pruebas de Rendimiento:**
   - Medir tiempos de respuesta de operaciones críticas (ver RNF2)
   - Generar 100 consultas de prueba, calcular promedio, P95, P99
   - Identificar consultas que exceden 2 segundos, analizar causas
   - Pruebas de carga: simular 10 usuarios concurrentes (herramienta: Locust/JMeter)

4. **Pruebas de Escalabilidad:**
   - Cargar 100 documentos, medir degradación de rendimiento
   - Documentar limitaciones de hardware de laboratorio
   - Proyecciones para escalamiento a producción

5. **Análisis de Prefactibilidad:**

   **Prefactibilidad Técnica:**
   - ¿La tecnología funciona? → Sí/No/Parcialmente + evidencia
   - Métricas de rendimiento alcanzadas vs objetivos
   - Limitaciones técnicas identificadas
   - Tecnologías requeridas para producción

   **Prefactibilidad Operativa:**
   - ¿Es usable? → Resultados de pruebas de usabilidad
   - ¿Resuelve el problema? → Feedback de usuarios de prueba
   - ¿Es adoptable por organización? → Análisis de cambio organizacional

   **Prefactibilidad Económica:**
   - Estimación de costos de desarrollo completo (horas-persona)
   - Costos de infraestructura (cloud, APIs de IA, almacenamiento)
   - Proyección de ROI: ahorro en capacitación vs costo de operación
   - Análisis costo-beneficio simplificado

6. **Documentación Final:**
   - Manual Técnico del Sistema (arquitectura, código, instalación, configuración)
   - Manual de Usuario (cómo usar el sistema)
   - Documentación de código (docstrings, comentarios)
   - Guía de actualización del modelo de IA (RM1)

**Entregables:**

- **Informe de Prefactibilidad** (documento académico formal, ~20-30 páginas):
  - Resumen ejecutivo
  - Prefactibilidad técnica (con evidencia de pruebas)
  - Prefactibilidad operativa (con resultados de usabilidad)
  - Prefactibilidad económica (análisis costo-beneficio)
  - Conclusiones y recomendaciones
  - Anexos: resultados de pruebas, logs, screenshots

- **Documentación Técnica del Prototipo:**
  - Manual técnico
  - Manual de usuario
  - Código documentado

- **Reporte de Pruebas Exhaustivas:**
  - Pruebas funcionales
  - Pruebas de seguridad
  - Pruebas de rendimiento
  - Pruebas de escalabilidad

**Criterios de Éxito:**

- ≥90% de requerimientos funcionales validados exitosamente
- Todos los requerimientos de seguridad cumplidos
- Informe de Prefactibilidad completo y aprobado por Product Owner
- Conclusión clara: Prototipo ES/NO ES prefactible técnica y operativamente

**Trazabilidad Académica:**
- Objetivo Específico 4: "Realizar pruebas de funcionalidad"
- Objetivo Específico 5: "Evaluar prefactibilidad técnica y operativa"
- Capítulo VII: "7.3 Pruebas del prototipo (funcionales, unitarias)"
- Capítulo VII: "7.4 Documentación técnica del sistema"
- Capítulo VII: "7.5 Funcionalidad demostrada y resultados obtenidos"
- Capítulo VII: "7.6 Evaluación de prefactibilidad"

---

### Gestión de Riesgos

**Riesgos Identificados y Mitigaciones:**

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| API de IA externa no disponible/lenta | Media | Alto | - Tener API alternativa configurada (HuggingFace, modelo local)<br>- Cache de respuestas comunes |
| Requerimientos cambian durante desarrollo | Media | Medio | - Scrum permite adaptación iterativa<br>- Validación continua con Product Owner |
| Pruebas de usabilidad revelan problemas críticos | Media | Alto | - Reservar tiempo en Sprint 3 para iteraciones<br>- Validar wireframes antes de implementar |
| Rendimiento <2s no alcanzable | Media | Alto | - Optimizaciones tempranas (caché, indexación)<br>- Plan B: redefinir RNF2 a <5s con justificación |
| Datos de prueba no suficientemente anónimos | Baja | Crítico | - Revisión manual de documentos<br>- Usar solo datos 100% sintéticos si hay duda |
| Equipo no completa sprints a tiempo | Media | Medio | - Buffer de tiempo en cronograma<br>- Priorización clara de must-have vs nice-to-have |

---

## References

### Documentos Académicos del Proyecto

- **Contexto del Proyecto:** `docs/contexto/contexto.txt`
  - Capítulos I-II: Problema, Objetivos, Justificación, Marco Conceptual
  - Capítulo VI: Metodología Aplicada (Scrum + Prefactibilidad)
  - Bases Legales (Leyes 19.628, 21.180, 17.336, ISO 27001, GDPR, UNESCO)

- **Workflow Status:** `docs/bmm-workflow-status.yaml`
  - Estado de avance de workflows BMad Method

### Bibliografía Técnica y Académica

**Gestión del Conocimiento:**
- Nonaka, I., & Takeuchi, H. (1995). *The Knowledge-Creating Company.* Oxford University Press.
- Davenport, T. H. (2018). *Working Knowledge: How Organizations Manage What They Know.* Harvard Business Press.
- Argyris, C., & Schön, D. (1996). *Organizational Learning II.* Addison-Wesley.

**Inteligencia Artificial:**
- Russell, S., & Norvig, P. (2021). *Artificial Intelligence: A Modern Approach* (4th ed.). Pearson.
- Goodfellow, I., Bengio, Y., & Courville, A. (2016). *Deep Learning.* MIT Press.

**Transformación Digital:**
- Brynjolfsson, E., & McAfee, A. (2017). *The Second Machine Age.* W. W. Norton & Company.
- Schwab, K. (2017). *The Fourth Industrial Revolution.* Crown Business.
- Porter, M. E., & Heppelmann, J. E. (2019). "Why Every Organization Needs an Augmented Reality Strategy." *Harvard Business Review*.

**Metodologías de Desarrollo:**
- Schwaber, K., & Sutherland, J. (2020). *The Scrum Guide.* Scrum.org.
- Pressman, R. S. (2021). *Software Engineering: A Practitioner's Approach* (9th ed.). McGraw-Hill.
- Sommerville, I. (2016). *Software Engineering* (10th ed.). Pearson.

**Calidad y Mejora Continua:**
- Deming, W. E. (1986). *Out of the Crisis.* MIT Press.
- Ishikawa, K. (1985). *What Is Total Quality Control?* Prentice Hall.

**Mercado y Tendencias:**
- MarketsandMarkets. (2024). *AI in Knowledge Management Market - Global Forecast to 2030.*
- Banco Interamericano de Desarrollo (BID). (2023). *El futuro del trabajo en América Latina.*

**Normativas y Estándares:**
- Ley N.º 19.628 (1999). *Protección de la Vida Privada.* República de Chile.
- Ley N.º 21.180 (2019). *Transformación Digital del Estado.* República de Chile.
- Ley N.º 17.336 (1970). *Propiedad Intelectual.* República de Chile.
- ISO/IEC 27001:2022. *Information Security Management Systems.*
- European Parliament. (2018). *General Data Protection Regulation (GDPR).*
- UNESCO. (2021). *Recommendation on the Ethics of Artificial Intelligence.*

---

## Next Steps

### Inmediatos (Post-PRD)

**1. Epic & Story Breakdown (REQUERIDO)**

Este PRD debe descomponerse en épicas e historias de usuario implementables:

**Comando:** `/bmad:bmm:workflows:create-epics-and-stories`

**Qué Generará:**
- Épicas organizadas por módulos (Gestión Conocimiento, Motor IA, Interfaz, Seguridad)
- Historias de usuario (<200 líneas de código cada una) con:
  - Formato: "Como [rol], quiero [funcionalidad], para [beneficio]"
  - Criterios de aceptación derivados de RF/RNF
  - Prioridad y sprint asignado
  - Estimación de esfuerzo (story points)

**Por Qué Es Crítico:**
- Los agentes de desarrollo (SM agent) necesitan historias atómicas para implementar
- Trazabilidad académica: cada RF se mapea a épica/story
- Base para Sprint Planning de Scrum

---

**2. UX Design (OPCIONAL pero RECOMENDADO)**

**Comando:** `/bmad:bmm:workflows:ux-design` (ejecutar con ux-designer agent)

**Qué Generará:**
- Wireframes detallados de pantallas principales
- Prototipos interactivos (Figma, Sketch)
- Guía de estilos (colores, tipografía, componentes)
- Flujos de usuario refinados

**Por Qué Es Recomendado:**
- RNF1 (Usabilidad) requiere diseño UX sólido
- Validar diseño ANTES de implementar frontend (Sprint 3) ahorra tiempo
- Resultados de usabilidad mejoran si diseño está validado previamente

---

**3. Architecture (REQUERIDO)**

**Comando:** `/bmad:bmm:workflows:architecture` (ejecutar con architect agent)

**Qué Generará:**
- Documento de Arquitectura Técnica detallado
- Decisiones arquitectónicas (ADRs)
- Diagramas de despliegue, secuencia, clases
- Especificación de tecnologías y dependencias
- Plan de integración con APIs externas (OpenAI, HuggingFace)

**Por Qué Es Crítico:**
- Objetivo Específico 2: "Diseñar arquitectura conceptual y funcional"
- Capítulo VI (6.5): "Modelamiento UML / arquitectura del sistema"
- Base técnica para Sprint 1 y Sprint 2

---

### Secuencia Recomendada de Workflows

```
PRD (COMPLETADO) ✅
    ↓
Epic Breakdown (*create-epics-and-stories) 🔄 SIGUIENTE
    ↓
UX Design (*ux-design) [OPCIONAL]
    ↓
Architecture (*create-architecture) 🔄 REQUERIDO
    ↓
Solutioning Gate Check (*solutioning-gate-check) [Validación pre-implementación]
    ↓
Sprint Planning (*sprint-planning con SM agent)
    ↓
Story Development (*dev-story con SM agent) [Sprint por Sprint]
```

---

### Para Iniciar Epic Breakdown AHORA

**Opciones:**

**A) Continuar en esta sesión:**
- Responde "continuar" y ejecutaré el workflow de épicas/stories inmediatamente
- Ventaja: Flujo continuo, contexto fresco
- Desventaja: Sesión larga (puede tomar 30-60 minutos)

**B) Nueva sesión (RECOMENDADO para proyectos complejos):**
1. Guarda esta sesión
2. Abre nueva sesión de Claude Code
3. Ejecuta: `/bmad:bmm:agents:pm` (cargar PM agent)
4. Ejecuta: `*create-epics-and-stories`
5. El workflow cargará automáticamente este PRD y generará épicas/stories

**¿Qué prefieres, Andres?**

---

## Product Magic Summary

**La Magia de Asistente-Conocimiento:**

Este prototipo transforma el conocimiento organizacional invisible en un activo estratégico accesible. No es solo un "chatbot corporativo" - es un **sistema de aprendizaje organizacional inteligente** que:

✨ **Captura** conocimiento disperso y tácito de expertos (documentos, manuales, experiencia)

✨ **Transforma** información fragmentada en conocimiento estructurado y consultable

✨ **Genera** contenido formativo personalizado automáticamente (resúmenes, quizzes, learning paths)

✨ **Entrega** respuestas instantáneas (<2s) fundamentadas en fuentes verificables

✨ **Cumple** con regulaciones chilenas de privacidad (Ley 19.628) mediante anonimización rigurosa

✨ **Demuestra** viabilidad técnica, operativa y económica para empresas latinoamericanas mediante estudio académico riguroso

**El Impacto:**

- Empleados nuevos productivos en **semanas, no meses**
- Conocimiento crítico **preservado y democratizado** (no depende de individuos)
- Capacitación **continua y adaptativa** sin costos de instructores
- Decisiones **mejor informadas** con acceso instantáneo a conocimiento corporativo
- Base sólida para **transformación digital sostenible** en organizaciones chilenas

---

*Este PRD captura la visión completa de Asistente-Conocimiento. Cada requerimiento, cada decisión arquitectónica, cada criterio de éxito está diseñado para demostrar que la IA generativa puede transformar cómo las organizaciones aprenden, comparten y preservan su conocimiento más valioso.*

*Creado mediante descubrimiento colaborativo entre Andres Amaya Garces y PM Agent (BMad Method).*

**Versión:** 1.0
**Fecha:** 2025-11-10
**Estado:** ✅ COMPLETO - Listo para Epic Breakdown
