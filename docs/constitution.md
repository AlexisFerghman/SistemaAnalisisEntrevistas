# Constitución del Sistema

## 1. Declaración de Propósito
La plataforma es un entorno de software de apoyo a la investigación y práctica profesional enfocado en la transcripción, organización de observaciones y análisis de contenido afectivo/lingüístico sobre entrevistas (clínicas o laborales). El sistema actúa estrictamente como una herramienta auxiliar de organización y análisis computacional.

## 2. Principios Fundamentales

### P1. Supervisión Humana Obligatoria (Human-in-the-Loop)
- **Límite de Autonomía:** El sistema **bajo ninguna circunstancia** emitirá diagnósticos médicos, evaluaciones psiquiátricas ni conclusiones automatizadas sobre la idoneidad de un usuario o paciente.
- **Responsabilidad Profesional:** La precisión de la transcripción, la interpretación de las emociones detectadas y el registro de observaciones o diagnósticos son de responsabilidad exclusiva del profesional usuario.

### P2. Privacidad y Soberanía de Datos por Diseño
- **Consentimiento:** La obtención y custodia del consentimiento informado del entrevistado es responsabilidad directa del profesional tratante/reclutador.
- **Modalidad Aislada (Modo Invitado/Público):** Cuando el sistema opere en entornos de servicio público o con alta restricción de datos, todo el procesamiento (ASR, post-procesamiento y análisis afectivo) se ejecutará **localmente en el equipo del usuario**, garantizando que ningún dato salga del dispositivo local.
- **Modo Registrado:** Los audios, transcripciones, etiquetas, observaciones y matrices afectivas se almacenarán únicamente para dar continuidad a la sesión del usuario autenticado, pudiendo definirse políticas de purga periódica para archivos multimedia pesados.

### P3. Transparencia Algorítmica y Explicabilidad (XAI)
- **Claridad de Inferencia:** El análisis afectivo debe entregar una distribución de probabilidades emocionales explícita sobre el texto evaluado.
- **Trazabilidad:** Toda predicción analítica soportada por el modelo avanzado de investigación (modelo de doctorado) debe incluir una capa de explicabilidad que justifique las decisiones del algoritmo mediante la atribución de importancia a nivel de tokens/palabras.

### P4. Calidad del Procesamiento en Cascada
- **Post-Procesamiento Supervisado:** El uso de modelos LLM/MLM para la corrección de errores básicos de transcripción debe conservar las marcas de tiempo (`timestamps`) originales del ASR.
- **Inmutabilidad del Ground Truth:** El usuario mantendrá la capacidad de revisar, editar y validar el texto post-procesado antes de consolidar el análisis afectivo final.