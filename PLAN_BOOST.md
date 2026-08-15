# PLAN DE BOOST — Smart Classroom AI para la feria

**Objetivo:** convertir la demo de un sistema *simulado* en una experiencia donde
el público es el sensor, y respaldar las proyecciones con estadística dura.

**Restricciones confirmadas:**
- ⏱️ Menos de 1 semana de desarrollo
- 📶 WiFi inestable en la feria → **todo debe correr 100% local**
- 💻 Hardware: laptop + TV/proyector + webcam externa + tablet de respaldo
- 👥 Público: 1–3 personas a la vez, principalmente jueces
- 🎯 Meta: rigor científico **y** recordación

**Frontend objetivo:** `backend/static/index.html` (el app mantenido y desplegado).
El app Vite de `frontend/` queda congelado (no se toca).

---

## BOOST 1 ⭐ — "El salón que te ve"

**La cámara real del stand reemplaza al VisionAgent simulado.** Los jueces se paran
frente a la webcam, el sistema los detecta con visión artificial (TensorFlow.js en
el navegador, sin nube), los mapea a las zonas del aula y el gemelo digital reacciona
en vivo. El momento del guion *"nuestro agente de visión no ve con una cámara: simula"*
se transforma en *"hasta hoy"*.

### 1.1 Arquitectura

```
┌────────────────────────────────────────────────────────────┐
│ NAVEGADOR (laptop conectada al TV)                          │
│                                                             │
│  getUserMedia(webcam)                                       │
│       │                                                     │
│       ▼                                                     │
│  TensorFlow.js + COCO-SSD (vendidos en /vendor, offline)    │
│       │  detecciones "person" ~8 fps                        │
│       ▼                                                     │
│  LiveCameraPanel:                                           │
│   · dibuja cajas + líneas guía de zonas sobre el video      │
│   · normaliza centros de cajas a (0..1, 0..1)               │
│   · POST /api/vision/live  (throttle 500 ms)                │
└────────────────────────────┬───────────────────────────────┘
                             │ HTTP local
┌────────────────────────────▼───────────────────────────────┐
│ BACKEND (FastAPI local)                                     │
│                                                             │
│  VisionAgent                                                │
│   · source = "live_camera" | "simulated"                    │
│   · recibe personas reales, las mapea a coordenadas del aula│
│   · si los datos se ponen viejos (>8 s) → vuelve a simulado │
│       │                                                     │
│       ▼  (nada cambia de aquí en abajo)                     │
│  OrchestratorAgent → DecisionEngine → DigitalTwin → WS      │
└─────────────────────────────────────────────────────────────┘
```

**El punto arquitectónico del pitch se vuelve demostrable:** solo cambia la capa
del sensor; orquestador, motor de decisiones y gemelo no se modifican.

### 1.2 Cambios en el backend

#### `backend/agents/vision.py`
- Agregar `self.source: "simulated" | "live_camera"` (default `"simulated"`).
- Agregar `self._live_people: list[dict]` y `self._live_updated_at: float`.
- Nuevo método `set_live_detections(people: list[dict])`:
  - Recibe personas ya en coordenadas del aula `{"id", "x", "y"}`.
  - Asigna zona con `get_zone()` existente, guarda timestamp.
  - Cambia `self.source = "live_camera"` si estaba en simulado.
- Nuevo método `set_source(mode: str)`:
  - `"simulated"` → regenera el escenario actual y vuelve al modo simulado.
  - `"live_camera"` → marca el modo; si no llegan detecciones en 8 s, el modo
    se revierte solo (ver `get_occupancy`).
- Modificar `get_occupancy()`:
  - Si `source == "live_camera"`:
    - Si `now - _live_updated_at > LIVE_STALE_SECONDS (8)` → log de advertencia,
      `set_source("simulated")` y continúa con el escenario simulado (fallback
      automático, sin intervención humana).
    - Si no, devuelve conteos a partir de `_live_people` **sin** `nudge_positions`
      (las personas reales ya se mueven solas).
  - El campo `"scenario"` del retorno pasa a ser `"live_camera"` en modo live
    (esto alimenta `classroom_state.scenario` → la UI puede mostrar la insignia LIVE).
- Modificar `get_people_positions()`: devuelve `_live_people` en modo live.
- Constante `LIVE_STALE_SECONDS = 8` en `shared/thresholds.py`.

#### `backend/routes/vision_routes.py`
- `POST /api/vision/live` — cuerpo:
  ```json
  { "people": [ {"x": 0.23, "y": 0.61}, ... ] }
  ```
  coordenadas **normalizadas de cámara** (0..1). La ruta hace el mapeo a
  coordenadas del aula (ver 1.4) y llama `vision_agent.set_live_detections()`.
  Respuesta: `{"received": N, "source": "live_camera"}`.
- `POST /api/vision/mode` — cuerpo `{"mode": "live_camera" | "simulated"}`.
  Cambia el modo explícitamente (lo usa el botón del panel y el fallback manual).
- `GET /api/vision/mode` — devuelve `{"source": ..., "stale_seconds": ...}` para
  que la UI pinte el estado.
- Actualizar la descripción de `half_class` en `list_scenarios()`: dice 18 y son 12.

#### Sin cambios
`orchestrator.py`, `decision_engine.py`, `digital_twin.py`, `broadcaster.py`,
`main.py` — **cero modificaciones**. Esa es la prueba arquitectónica.

### 1.3 Detección en el navegador (offline)

**Modelo:** COCO-SSD con base MobileNetV2 (quantized). Detecta la clase `person`,
corre a ~8–15 fps en CPU de laptop sin GPU. Alternativa de respaldo si el
rendimiento es malo: MediaPipe Tasks Vision (person detector). Se decide en la
fase de prueba; la interfaz con el resto del sistema es idéntica.

**Archivos a descargar y vender en `backend/static/vendor/`:**

| Archivo | Origen | Tamaño aprox. |
|---|---|---|
| `tf.min.js` | jsdelivr `@tensorflow/tfjs@4.20.0/dist/tf.min.js` | ~1.5 MB |
| `coco-ssd.min.js` | jsdelivr `@tensorflow-models/coco-ssd@2.2.3/dist/coco-ssd.min.js` | ~30 KB |
| `models/coco-ssd/model.json` + shards de pesos | TF Hub / storage.googleapis.com (modelo mobilenet_v2) | ~5 MB |

Carga en el navegador:
```js
const model = await cocoSsd.load({ base: "mobilenet_v2", modelUrl: "/vendor/models/coco-ssd/model.json" });
```
> ⚠️ Verificar en la fase de implementación que `modelUrl` apunte a un
> `model.json` cuyas referencias de pesos sean relativas (si son absolutas,
> se descargan los shards y se reescriben las rutas). Si COCO-SSD no carga
> offline, plan B: MediaPipe con WASM + `.task` vendidos igualmente.

### 1.4 Mapeo cámara → aula

El video se muestra **espejado** (como un espejo: si te mueves a tu derecha,
tu avatar se mueve a la derecha en pantalla). Para cada detección con centro
normalizado `(bx, by)` en el video espejado:

```
x_aula = bx * 10        (0 = pared izquierda/ventanas, 10 = pared derecha)
y_aula = by * 8         (0 = frente/tablero, 8 = fondo/puerta)
```

- Arriba del cuadro = frente del salón; abajo = fondo.
- Izquierda/derecha del cuadro = zonas A–C / B–D.
- La zona se deriva con `get_zone(x_aula, y_aula)` (ya existe).
- Caminar hacia la cámara = caminar hacia el fondo del salón.

**Overlay pedagógico sobre el video:** cruz al 50%/50% con etiquetas A, B, C, D
en cada cuadrante (mismos colores de las zonas del 3D), para que el juez entienda
el mapeo sin explicación. Caja verde alrededor de cada persona con su zona.

### 1.5 Nuevo componente `LiveCameraPanel` (en `index.html`)

Ubicación: columna derecha, **primer panel** (arriba de Voice), porque es la
estrella de la demo.

Estructura:
- Botón grande `🎥 ACTIVAR CÁMARA REAL` / `⏹ VOLVER A SIMULACIÓN`.
- Al activar:
  1. `getUserMedia({video: {width: 640, height: 480}})` — Chrome en localhost
     tiene permiso automático de cámara (origen seguro). Si el usuario niega
     el permiso → mensaje claro con instrucciones.
  2. Carga del modelo (spinner "Cargando modelo de IA… ~5 MB", solo primera vez).
  3. `<video>` espejado + `<canvas>` encima para cajas/líneas guía.
  4. Loop de detección: `model.detect(video)` cada ~150 ms; filtro de clase
     `person` con `score >= 0.5`.
  5. Envío: `POST /api/vision/live` cada 500 ms con las detecciones normalizadas.
  6. Barra de estado: `● LIVE · N personas · X fps`.
- Al desactivar: detiene el stream (`track.stop()`), `POST /api/vision/mode
  {"mode":"simulated"}`.
- Insignia `🔴 LIVE` flotante sobre la vista 3D cuando
  `state.scenario === "live_camera"` (el 3D ya pinta las personas a partir de
  `state.people` — las personas reales aparecen como avatares en el aula 3D
  sin cambios adicionales).
- Traducciones ES/EN nuevas en `TR` (`cam.*`).

### 1.6 Interacción con DemoControls

- Mientras `source == "live_camera"`, los chips de OCUPACIÓN se deshabilitan
  visualmente (un clic ahí fuerza `POST /api/vision/scenario`, que a su vez
  devuelve el modo a simulado — comportamiento correcto y sin código extra:
  `set_scenario()` pone `source = "simulated"`).
- Clima y hora siguen activos en modo live (la IA decide con personas reales +
  sol simulado → perfecto para la demo "mismo público, cambiamos el clima").

### 1.7 Criterios de aceptación (Boost 1)

- [ ] Con el servidor sin internet (cortar WiFi), el modelo carga y detecta.
- [ ] 1 persona frente a la cámara → su avatar aparece en la zona correcta del
      3D en ≤ 2 ciclos (≤ 10 s, idealmente al siguiente ciclo de 5 s).
- [ ] Persona sale de cuadro → tras el ciclo, luces de esa zona se apagan
      (si la luz natural no exige otra cosa).
- [ ] Cerrar la pestaña de la cámara → en ≤ 8 s el sistema vuelve solo a simulado
      y queda registrado en `logs/system.log`.
- [ ] Botón de volver a simulación restaura el escenario previo al instante.
- [ ] Nada de lo existente (voz, clima, hora, energía) se rompe.

---

## BOOST 2 — "Un año escolar en 60 segundos" (Monte Carlo)

**Convertir la proyección en estadística.** Un botón simula un año lectivo completo
(200 días, clima y ocupación aleatorios) y otro repite la simulación 1000 veces
para producir un **intervalo de confianza** del ahorro. Respuesta directa a la
sección "La debilidad" del guion: los supuestos quedan a la vista y el resultado
es una distribución, no una promesa.

### 2.1 Modelo estadístico (supuestos públicos en la UI)

- **Jornada:** 8 h de clase/día (7:00–15:00), 200 días → coincide con los números
  del pitch (baseline 2.56 kWh/día = 320 W × 8 h).
- **Ocupación por franja horaria** (estocástica):
  | Franja | Personas (distribución) |
  |---|---|
  | 7–8 | uniforme 15–28 (llegada) |
  | 8–12 | uniforme 24–30 (clase plena) |
  | 12–13 | 50% vacío (descanso) / 50% quedan 2–6 |
  | 13–15 | uniforme 20–30 (clase de la tarde) |
- **Distribución por zonas:** pesos `[A:0.30, B:0.28, C:0.22, D:0.20]` + ruido,
  redondeo a enteros (la gente tiende a sentarse adelante).
- **Clima por día** (una muestra por día, persiste todo el día):
  `clear 0.35 / cloudy 0.35 / overcast 0.20 / rainy 0.10` — perfil de clima
  andino colombiano, constantes editables al inicio del módulo.
- **Luz natural:** `calculate_light_levels(hora, clima)` existente — sin cambios.
- **Decisión:** `run_decision_engine(ocupación, luz)` existente — sin cambios.
  (Garantiza que la simulación usa *exactamente* la IA que se muestra en vivo.)
- **Energía:** vatios decididos × 1 h por franja. Baseline = 320 W × 8 h.
- **Traducción económica/ambiental:** 800 COP/kWh, 0.126 kg CO₂/kWh (UPME),
  mismas constantes que los paneles existentes.

### 2.2 Backend

#### Nuevo `backend/skills/year_simulator.py`
- `simulate_school_year(rng) -> dict` — un año: recorre 200 días × 8 franjas,
  acumula kWh IA y baseline, devuelve:
  `{ai_kwh, baseline_kwh, savings_pct, savings_cop, co2_avoided_kg, weather_mix, days_empty, ...}`
- `run_monte_carlo(n_years, on_progress=None) -> dict` — repite N años, devuelve:
  - `mean/median/stdev` de `savings_pct`
  - percentiles `p10, p50, p90`
  - `min, max`
  - histograma de `savings_pct` (10 bins) para gráfica
  - agregados: COP y CO₂ totales ahorrados en los N años
  - `elapsed_seconds`, `n_years`
- **Optimización de rendimiento:** el camino caliente evita dicts por zona
  (tuplas + comparaciones directas), luz natural precalculada por
  `(hora, clima)` (tabla 8×4). Objetivo: 1000 años < 15 s en la laptop.

#### Nuevo `backend/routes/simulation_routes.py` (router nuevo en `main.py`)
- `POST /api/sim/year` — simula **1 año** (rápido, <50 ms), devuelve el detalle
  completo (para el contador animado).
- `POST /api/sim/monte-carlo` — cuerpo `{"n_years": 1000}`. Lanza la simulación
  en un hilo (`concurrent.futures` / `run_in_executor`) y devuelve
  `{"task_id": ...}` de inmediato.
- `GET /api/sim/status` — progreso `{running, progress_pct, result?}`.
  El frontend hace polling cada 500 ms y muestra barra de progreso.
  (Evita timeouts de HTTP y funciona igual en Render.)

### 2.3 Frontend — panel "🔮 Máquina del tiempo"

Ubicación: columna izquierda, entre la vista 3D y ComparisonPanel.

- Botón **▶ Simular 1 año lectivo**: ejecuta `POST /api/sim/year` y anima
  contadores (kWh, COP, kg CO₂) con `requestAnimationFrame` durante ~3 s.
  Muestra el mix de clima del año simulado (☀️35% ⛅35% ☁️20% 🌧️10%).
- Botón **🎲 Monte Carlo ×1000**: barra de progreso (polling a `/api/sim/status`)
  y al terminar:
  - Número grande: **ahorro mediano P50 = XX%** con rango P10–P90.
  - Histograma CSS (barras como `EnergyBars`) de la distribución de ahorros.
  - Frase de cierre calculada: *"En el 90% de los años simulados el ahorro está
    entre X% y Y%"* — el intervalo de confianza dicho en lenguaje simple.
  - Totales: COP y CO₂ evitados en 1000 años (cifra de impacto).
- Nota de supuestos (colapsable `<details>`): jornada, clima, ocupación —
  *"todos los supuestos a la vista"*, como promete el guion.
- Traducciones ES/EN nuevas (`sim.*`).

### 2.4 Criterios de aceptación (Boost 2)

- [ ] `POST /api/sim/year` responde en < 200 ms.
- [ ] Monte Carlo ×1000 termina en < 20 s con barra de progreso visible.
- [ ] El ahorro mediano cae en el rango prometido del sistema (40–60%);
      si no, revisar supuestos del horario (no maquillar).
- [ ] Los números del panel siguen usando 8 h × 200 días × 320 W = 2.56 kWh/día
      de baseline (coherencia con el pitch).
- [ ] Funciona offline.

---

## BOOST 3 — Aula 3D de alta definición

**De esquema vectorial a escena realista.** El aula es lo primero que ve el juez
en el TV; hoy parece maqueta plana. Meta: materiales PBR, iluminación
cinematográfica y detalle de mobiliario — sin dependencias nuevas y offline.

**Limitación técnica:** el Three.js vendido es r160 UMD (sin addons). Todo se
hace con el núcleo: nada de OrbitControls/RectAreaLightUniformsLib/EffectComposer.

### 3.1 Renderer y color (cambio global, máximo impacto por línea de código)
- `renderer.outputColorSpace = THREE.SRGBColorSpace`
- `renderer.toneMapping = THREE.ACESFilmicToneMapping`, exposición ~1.15
- Sombras: mapa 2048×2048 en la luz direccional, `bias` ajustado
- `scene.environment`: mapa PMREM generado con `PMREMGenerator.fromScene()` de
  una mini-escena procedural (cielo degradado + planos brillantes donde están
  las ventanas) → reflejos reales en todos los materiales PBR

### 3.2 Materiales (Lambert → Standard/Physical)
| Superficie | Material |
|---|---|
| Paredes / techo | `MeshStandardMaterial` rugosidad 0.95, textura con ruido fino |
| Piso de madera | `MeshStandardMaterial` + textura 1024² (vetas, juntas) + roughnessMap procedural |
| Patas de mesas/sillas | metalness 0.8, rugosidad 0.35 (metal pintado) |
| Tablero | `MeshPhysicalMaterial` clearcoat 1.0, rugosidad 0.15 (refleja el ambiente) |
| Vidrio ventanas | `MeshPhysicalMaterial` con reflejos del environment + tinte por clima |
| Pantalla monitor | emisiva con brillo de "contenido" |

### 3.3 Texturas procedurales de alta resolución (canvas, sin archivos externos)
- Piso 1024²: variación por tabla, veta, brillo irregular; **AO horneada**
  (degradado que oscurece esquinas y bajo-muebles) multiplicada sobre el color
- Pared 1024²: ruido sutil + zócalo con sombra de contacto
- **Decoración nueva:** pósters educativos en paredes (canvas dibujados:
  sistema solar, tabla periódica, póster "APAGA LA LUZ"), reloj de pared con
  manecillas, libros/cuadernos de colores sobre algunos pupitres, papelera
- Sombras de contacto baratas: planos circulares semitransparentes bajo
  pupitres y personas (ancla los objetos al piso visualmente)

### 3.4 Personas y luces
- Figuras con `CapsuleGeometry` (núcleo r160 ✓): extremidades y torso suaves,
  variación de altura ±8% por persona
- Lámparas: paneles emisivos con `emissiveIntensity` alta en ON + sprite de
  halo existente; intensidad de la luz direccional (sol) ligada al nivel de
  luz natural del LightSensorAgent (el sol de la escena sigue al modelo)
- Polvo flotando en los rayos de sol (partículas `Points` dentro de los haces,
  solo con clima `clear`) — detalle de "wow" barato

### 3.5 Criterios de aceptación (Boost 3)
- [ ] La escena corre ≥ 30 fps en la laptop del stand con todo activo
- [ ] Sin dependencias nuevas, sin internet (todo procedural/vendido)
- [ ] Los estados ON/DIM/OFF, clima, lluvia, personas y zonas siguen funcionando
      exactamente igual (la capa visual no toca la lógica)
- [ ] Vista lado a lado: antes/después no se confunden

**Estimado: 1 día.** Se ejecuta después del Boost 1 (los avatares de la cámara
se benefician de la escena nueva) y antes del Boost 2.

---

## FIXES DE BUGS EXISTENTES

| # | Bug | Fix |
|---|---|---|
| 1 | `list_scenarios()` dice "18 people" para `half_class`; son 12 | Corregir texto en `vision_routes.py` |
| 2 | `data/classroom_config.json` nunca se lee (constantes duplicadas en código) | Nuevo `backend/shared/config.py`: carga el JSON una vez; `thresholds.py` toma `BASELINE_WATTS`, vatios por zona y meta de ahorro del config (fallback a los valores actuales si el archivo no está). Alcance limitado a energía para no arriesgar la semana de feria |
| 3 | `digital_twin.update_people()` es código muerto | Eliminar el método (ya fue reemplazado por `update_people_positions`) |
| 4 | `run.sh` anuncia el frontend Vite en :5173 (roto: proxy mal + puerto 3000) | `run.sh` deja de levantar `frontend/` y abre `http://localhost:8000/app/` — el app real |

---

## NARRATIVA — actualización del guion

El boost cambia el momento más fuerte de la presentación. Ajustes en `GUION.md`
(y notas espejo en `PITCH.md`):

1. **Acto 3, nueva DEMO 0 (la estrella):** después de mostrar el 3D, activar la
   cámara real: *"Nuestro Vision Agent siempre simuló personas. Hasta hoy."*
   → el juez se ve detectado en el recuadro y su avatar aparece en el aula.
   Reemplaza la DEMO 1 (personas a cero con botón): el público se va del cuadro
   y las luces se apagan solas. **Mismo punto, con evidencia física.**
2. **Sección "La debilidad":** el texto *"no ve con una cámara: simula"* se
   reescribe — la visión ya es real en el stand; la debilidad honesta queda en
   que **no controla lámparas físicas** ( intacta, sigue siendo el momento de
   credibilidad).
3. **Números:** después del 40–60%, rematar con la Máquina del tiempo:
   *"No les traemos una proyección: les traemos mil años simulados. En el 90%
   de ellos, el ahorro está entre X y Y por ciento."*
4. `DEPLOY.md`: actualizar checklist del día de feria — correr `./run.sh` local
   (el WiFi de la feria no es confiable), permiso de cámara en Chrome, webcam
   conectada antes de abrir el navegador, Render solo como plan B.

---

## PLAN DE EJECUCIÓN (orden y estimados)

| Fase | Trabajo | Estimado |
|---|---|---|
| **0** | Descargar y verificar modelos TF.js offline (prueba de concepto en página suelta) | 0.5 día |
| **1** | Backend visión live: `vision.py` + rutas + fallback por staleness | 0.5 día |
| **2** | Frontend `LiveCameraPanel` + overlay + insignia LIVE + mapeo | 1 día |
| **3** | Prueba end-to-end Boost 1 (corte de WiFi incluido) y ajuste de umbrales | 0.5 día |
| **4** | Boost 3: aula 3D HD (renderer PBR, environment, texturas, detalle) | 1 día |
| **5** | `year_simulator.py` + rutas de simulación + verificación de rendimiento | 0.5 día |
| **6** | Panel Máquina del tiempo (contadores + histograma + percentiles) | 0.5 día |
| **7** | Bug fixes (1–4) | 0.5 día |
| **8** | Actualización GUION.md / PITCH.md / DEPLOY.md | 0.5 día |
| **9** | Ensayo general con webcam + TV; plan B documentado | 0.5 día |

**Total: ~6 días de trabajo.** Margen de 1 día antes de la feria. Si el tiempo
aprieta, el orden de sacrificio es: Boost 2 (Monte Carlo) primero en degradarse
a ×500 años, nunca el Boost 1 ni el Boost 3.

## VERIFICACIÓN

No hay suite de tests en el repo. Se agrega `backend/scripts/smoke_test.py`
(ejecutable con `python3`, sin dependencias nuevas) que verifica:
1. `run_decision_engine` con casos borde (vacío, luz alta, mixto).
2. `year_simulator`: 1 año y 100 años → invariantes (baseline = 512 kWh/año,
   ahorro ∈ (0, 100), kWh IA < baseline).
3. VisionAgent live: set_live_detections → occupancy correcto; staleness →
   regreso a simulado.
4. Carga de `shared/config.py`.

Además: verificación manual con `curl` de cada endpoint nuevo y recorrido
completo de la demo en el navegador con la red desconectada.

## RIESGOS Y MITIGACIÓN

| Riesgo | Prob. | Mitigación |
|---|---|---|
| COCO-SSD no carga offline (rutas de pesos absolutas) | Media | Fase 0 primero; plan B: MediaPipe Tasks Vision (WASM + .task vendibles) |
| Laptop lenta: <5 fps de detección | Media | Resolución 480p, `score>=0.5`, detección cada 200 ms; plan B: MediaPipe |
| Iluminación del stand confunde al detector | Baja | COCO-SSD es robusto; posición de webcam probada en ensayo general |
| Cámara requiere HTTPS fuera de localhost | Baja | La feria se corre en localhost (origen seguro); documentado en DEPLOY.md |
| Monte Carlo lento en la laptop | Baja | Tablas precalculadas; si aun así >20 s, default 500 años (se sigue viendo) |
| Se cae algo existente | Baja | El modo live es aditivo: un botón devuelve todo al estado actual exacto |

## CHECKLIST DÍA DE FERIA (se agregará a DEPLOY.md)

- [ ] Laptop con el repo + `pip install -r backend/requirements.txt` ya hecho
- [ ] `./run.sh` corriendo **local** (no depender del WiFi ni de Render)
- [ ] Webcam externa conectada y orientada al público antes de abrir Chrome
- [ ] Chrome abierto en `http://localhost:8000/app/` con permiso de cámara concedido
- [ ] TV/proyector como segunda pantalla (duplicada)
- [ ] Modelo de IA precargado (abrir la cámara una vez antes de la charla)
- [ ] Monte Carlo ×1000 ya ejecutado una vez (el resultado se muestra al instante
      si se re-ejecuta, pero el primer run tarda ~15 s)
- [ ] Plan B: capturas + video grabado de la demo (se graba en el ensayo general)
