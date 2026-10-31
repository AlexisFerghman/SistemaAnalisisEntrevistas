# Inicio del proyecto: análisis de entrevistas clínicas

Esta guía adapta el flujo de Spec-Driven Development (SDD) del repositorio a un
sistema de análisis de entrevistas clínicas asistido por IA. La IA ayuda a
organizar y analizar información; no sustituye el juicio clínico ni establece
diagnósticos.

## 1. Define primero los límites

Antes de procesar entrevistas, documenta:

- quiénes serán los usuarios y qué decisiones podrán tomar con el sistema;
- qué datos se usarán, con qué consentimiento y durante cuánto tiempo;
- cómo se anonimizarán los textos y quién podrá acceder a ellos;
- qué tareas quedan explícitamente fuera del sistema, por ejemplo diagnosticar,
  indicar tratamientos o decidir por el profesional;
- cómo se revisarán las salidas de la IA y cómo se registrarán sus errores.

No uses entrevistas identificables como datos de prueba. Empieza con ejemplos
ficticios o anonimizados.

## 2. Crea los primeros documentos

Adapta la estructura de `habits-cli/` y crea, como mínimo:

```text
docs/constitution.md
AGENTS.md
specs/001-analisis-inicial/spec.md
specs/001-analisis-inicial/plan.md
specs/001-analisis-inicial/tasks.md
```

Orden recomendado:

1. **Constitución:** principios verificables sobre privacidad, supervisión
   clínica, trazabilidad, seguridad, calidad y límites de la IA.
2. **Spec:** problema, usuarios, flujo principal, requisitos en EARS, casos
   límite, fuera de alcance y criterios de finalización. Describe qué y por
   qué, no la arquitectura.
3. **Clarificación:** revisa ambigüedades, riesgos y requisitos ausentes como
   si fueras QA y responsable de protección de datos.
4. **Plan:** decide arquitectura, modelo de datos, estrategia de anonimización,
   uso de modelos y estrategia de pruebas. Relaciona cada decisión con los RF.
5. **Tareas:** divide el plan en tareas pequeñas, ordenadas por dependencia.

## 3. Primer prompt para trabajar con IA

```text
Quiero iniciar un proyecto SDD para analizar entrevistas clínicas con ayuda de
IA. NO escribas código. Hazme preguntas de una en una, como máximo 8, para
definir usuarios, objetivo, tipo de análisis, consentimiento, anonimización,
retención de datos, revisión humana, errores y fuera de alcance.

Después de mis respuestas, propón una docs/constitution.md de principios
cortos y verificables. Incluye privacidad, seguridad, supervisión clínica,
trazabilidad, calidad y límites: el sistema no diagnostica ni reemplaza al
profesional. Espera mi aprobación antes de generar más documentos.
```

Cuando apruebes la constitución, continúa con el prompt de **Spec** de
`samples/prompts.md`, indicando que el primer alcance es `001-analisis-inicial`.
No implementes nada hasta que la spec, su clarificación, el plan y las tareas
estén aprobados.

## 4. Criterio para el primer MVP

El primer MVP debe ser pequeño y revisable: por ejemplo, cargar una entrevista
anonimizada, extraer temas definidos por el profesional, mostrar evidencias
textuales y permitir aceptar, corregir o rechazar cada resultado. Toda salida
generada por IA debe quedar marcada como sugerencia y conservar su trazabilidad.