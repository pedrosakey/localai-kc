---
title: "Análisis de Muestras de Audio para Entrenamiento"
tags: [audio, samples, training, machine-learning]
created: 2025-07-25
---

# Análisis de Muestras de Audio para Entrenamiento

## Resumen Ejecutivo
Análisis exhaustivo de las muestras de audio recopiladas para entrenar los modelos de [[whisper_ai]] y [[emotion_detection]]. Este documento detalla la calidad, distribución y características de nuestro dataset personalizado.

## Dataset Overview

### Estadísticas Generales
- **Total de muestras**: 12,847 archivos de audio
- **Duración total**: 847 horas
- **Idiomas**: Español (60%), Inglés (30%), Francés (10%)
- **Calidad promedio**: 44.1 kHz, 16-bit
- **Formato**: WAV sin compresión

### Distribución por Categorías

#### Por Género del Hablante
- **Masculino**: 5,890 muestras (45.8%)
- **Femenino**: 6,720 muestras (52.3%)
- **No identificado**: 237 muestras (1.9%)

#### Por Grupo Etario
- **18-25 años**: 3,240 muestras (25.2%)
- **26-40 años**: 4,890 muestras (38.1%)
- **41-60 años**: 3,120 muestras (24.3%)
- **60+ años**: 1,597 muestras (12.4%)

#### Por Acentos/Dialectos (Español)
- **Mexicano**: 2,890 muestras
- **Argentino**: 1,560 muestras  
- **Colombiano**: 1,230 muestras
- **Español**: 980 muestras
- **Otros**: 880 muestras

## Análisis de Calidad de Audio

### Métricas Técnicas
- **SNR promedio**: 28.4 dB
- **Ruido de fondo**: <-45 dB en 94% de las muestras
- **Clipping**: Detectado en <0.1% de muestras
- **Frecuencia fundamental**: 85-350 Hz (rango normal)

### Condiciones de Grabación
1. **Estudio controlado**: 45% de muestras
   - SNR: >35 dB
   - Ambiente: Cabina insonorizada
   - Micrófono: Audio-Technica AT4040

2. **Oficina silenciosa**: 35% de muestras
   - SNR: 25-35 dB
   - Ambiente: Oficina sin ruido externo
   - Micrófono: Blue Yeti USB

3. **Ambiente doméstico**: 20% de muestras
   - SNR: 15-25 dB
   - Ambiente: Casa con ruido ambiental mínimo
   - Micrófono: Headset gaming/laptop integrado

### Distribución Emocional

#### Muestras para [[emotion_detection]]
| Emoción   | Cantidad | Porcentaje | Duración Promedio |
|-----------|----------|------------|-------------------|
| Neutral   | 3,890    | 30.3%      | 4.2 segundos      |
| Alegría   | 2,340    | 18.2%      | 3.8 segundos      |
| Tristeza  | 1,890    | 14.7%      | 5.1 segundos      |
| Ira       | 1,560    | 12.1%      | 3.2 segundos      |
| Miedo     | 1,234    | 9.6%       | 4.5 segundos      |
| Sorpresa  | 1,098    | 8.5%       | 2.9 segundos      |
| Disgusto  | 835      | 6.5%       | 3.7 segundos      |

## Problemas Identificados y Soluciones

### 1. Desbalance de Datos
**Problema**: Sobrerrepresentación de emociones neutrales
**Solución**: Técnicas de augmentación para emociones minoritarias
- Cambio de pitch: ±2 semitonos
- Adición de ruido controlado: SNR 20-30 dB
- Time stretching: ±10% velocidad

### 2. Variabilidad en Calidad
**Problema**: Diferentes condiciones de grabación
**Solución**: Normalización y preprocessing
```python
def normalize_audio(audio_path):
    y, sr = librosa.load(audio_path, sr=16000)
    # Normalización de volumen
    y = librosa.util.normalize(y)
    # Filtro pasa-altos para eliminar ruido de baja frecuencia
    y = librosa.effects.preemphasis(y)
    # Reducción de ruido usando spectral gating
    y = nr.reduce_noise(y=y, sr=sr, stationary=False)
    return y, sr
```

### 3. Inconsistencia en Etiquetado
**Problema**: Anotaciones subjetivas de emociones
**Solución**: 
- Triple anotación por evaluadores independientes
- Algoritmo de consenso con umbral de 70%
- Re-evaluación de muestras conflictivas

## Métricas de Validación

### Conjunto de Entrenamiento (70%)
- **Muestras**: 8,993
- **Distribución**: Estratificada por emoción y género
- **Validación cruzada**: 5-fold

### Conjunto de Validación (15%)
- **Muestras**: 1,927
- **Uso**: Ajuste de hiperparámetros
- **Evaluación**: Cada época de entrenamiento

### Conjunto de Prueba (15%)
- **Muestras**: 1,927
- **Uso**: Evaluación final del modelo
- **Características**: No visto durante entrenamiento

## Resultados de Entrenamiento

### Performance de [[whisper_ai]]
- **WER en español**: 3.1%
- **WER en inglés**: 2.8%
- **Tiempo de convergencia**: 45 épocas
- **Mejora vs modelo base**: +12% en español mexicano

### Performance de [[emotion_detection]]
- **Accuracy general**: 87.3%
- **F1-score promedio**: 0.84
- **Mejor emoción detectada**: Ira (93% accuracy)
- **Mayor desafío**: Sorpresa vs Miedo (confusión 18%)

## Recomendaciones para Futuras Recolecciones

### Prioridades
1. **Más datos de sorpresa y miedo**: Aumentar 50%
2. **Dialectos faltantes**: Peruano, venezolano, chileno
3. **Ambientes ruidosos**: Call centers, cafeterías, automóviles
4. **Edad avanzada**: >65 años (solo 3% del dataset actual)

### Protocolo de Grabación Optimizado
- **Duración mínima**: 3 segundos por clip
- **Duración máxima**: 8 segundos por clip
- **Muestreo**: 16 kHz (suficiente para voz humana)
- **Formato**: WAV o FLAC sin compresión
- **Metadatos**: Edad, género, dialecto, emoción, SNR

## Referencias
- [[proyecto_ia_demo]] - Proyecto principal
- [[data_collection_protocol]] - Protocolo de recolección
- [[preprocessing_pipeline]] - Pipeline de preprocesamiento 