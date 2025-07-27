---
title: "Detección de Emociones en Audio"
tags: [emociones, audio, ai, machine-learning, tensorflow]
created: 2025-07-26
---

# Detección de Emociones en Audio

## Descripción General
Sistema para identificar estados emocionales a partir de características acústicas de la voz humana. Utiliza técnicas de machine learning para clasificar emociones en tiempo real.

## Emociones Detectadas
1. **Alegría** - Tono elevado, ritmo rápido
2. **Tristeza** - Tono bajo, ritmo lento
3. **Ira** - Intensidad alta, fluctuaciones bruscas
4. **Miedo** - Temblor vocal, pitch elevado
5. **Sorpresa** - Cambios súbitos de tono
6. **Disgusto** - Tono ronco, articulación tensa
7. **Neutral** - Baseline emocional estable

## Arquitectura Técnica

### Extracción de Características
```python
import librosa
import numpy as np

def extract_features(audio_file):
    # Cargar audio
    y, sr = librosa.load(audio_file)
    
    # MFCCs (Mel-frequency cepstral coefficients)
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    
    # Características espectrales
    spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
    spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
    
    # Zero crossing rate
    zcr = librosa.feature.zero_crossing_rate(y)
    
    # Chroma features
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    
    return np.concatenate([
        mfccs.mean(axis=1),
        spectral_centroids.mean(),
        spectral_rolloff.mean(),
        zcr.mean(),
        chroma.mean(axis=1)
    ])
```

### Modelo de Clasificación
- **Arquitectura**: Red neuronal densa con dropout
- **Capas**: 128 → 64 → 32 → 7 (emociones)
- **Activación**: ReLU (capas ocultas), Softmax (salida)
- **Optimizador**: Adam con learning rate 0.001
- **Loss function**: Categorical crossentropy

### Dataset de Entrenamiento
- **RAVDESS**: 7,356 archivos de audio con emociones etiquetadas
- **CREMA-D**: 7,442 clips de audio emocional
- **SAVEE**: 480 utterances de 4 actores masculinos
- **EMO-DB**: Base de datos alemana de emociones

## Métricas de Performance

### Precisión por Emoción
| Emoción   | Precisión | Recall | F1-Score |
|-----------|-----------|--------|----------|
| Alegría   | 87%       | 85%    | 86%      |
| Tristeza  | 82%       | 88%    | 85%      |
| Ira       | 91%       | 89%    | 90%      |
| Miedo     | 78%       | 82%    | 80%      |
| Sorpresa  | 74%       | 76%    | 75%      |
| Disgusto  | 79%       | 77%    | 78%      |
| Neutral   | 93%       | 91%    | 92%      |

### Performance General
- **Accuracy**: 85.3%
- **Tiempo de inferencia**: ~50ms por clip de 3 segundos
- **Tamaño del modelo**: 2.4MB
- **Consumo de memoria**: ~300MB durante inferencia

## Integración con el Sistema Principal

### Pipeline de Procesamiento
1. **Segmentación**: Dividir audio en chunks de 3 segundos
2. **Preprocessing**: Normalización y filtrado de ruido
3. **Feature Extraction**: Extracción de características acústicas
4. **Predicción**: Clasificación emocional usando modelo entrenado
5. **Post-processing**: Suavizado temporal y agregación

### API Integration
```python
from emotion_detector import EmotionDetector

detector = EmotionDetector(model_path="emotion_model.h5")

# Analizar audio
emotion_scores = detector.predict(audio_data)
dominant_emotion = max(emotion_scores, key=emotion_scores.get)

# Resultado
{
    "emotion": "alegria",
    "confidence": 0.87,
    "scores": {
        "alegria": 0.87,
        "neutral": 0.08,
        "sorpresa": 0.03,
        "tristeza": 0.02
    }
}
```

## Aplicaciones en el Proyecto
1. **Análisis de Calls**: Evaluación emocional en [[proyecto_ia_demo]]
2. **Feedback Emocional**: Respuestas adaptativas del sistema
3. **Quality Assurance**: Monitoreo de satisfacción del usuario
4. **Research**: Estudios de comportamiento emocional

## Desafíos y Limitaciones
- **Variabilidad individual**: Diferentes formas de expresar emociones
- **Contexto cultural**: Variaciones culturales en expresión emocional
- **Calidad del audio**: Sensibilidad al ruido y compresión
- **Emociones mixtas**: Dificultad para detectar estados emocionales complejos

## Próximas Mejoras
- **Transfer Learning**: Adaptar a nuevos dialectos y acentos
- **Multi-modal**: Combinar con análisis facial y texto
- **Real-time**: Optimización para procesamiento en streaming
- **Personalization**: Modelos adaptados a usuarios específicos

## Referencias
- [[emotion_detection_research]] - Investigación detallada y experimentos
- [[audio_samples_analysis]] - Análisis de muestras de entrenamiento
- [[tensorflow_optimization]] - Optimizaciones específicas del modelo 