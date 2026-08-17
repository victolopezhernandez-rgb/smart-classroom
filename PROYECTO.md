# Smart Classroom AI — estado del proyecto

Sistema multiagente que apaga, atenúa o enciende las luces de un salón según
cuánta gente hay y cuánta luz natural entra, y que mide cuánta energía se
ahorra. Todo el salón existe como **gemelo digital 3D**: no hay hardware.

Última actualización: 17 de agosto de 2026.

---

## 1 · Qué hace, en una frase por agente

| Agente | Archivo | Qué aporta al ciclo |
|---|---|---|
| **Orchestrator** | `backend/agents/orchestrator.py` | Cada 5 s pregunta a todos, decide y transmite |
| **Vision** | `backend/agents/vision.py` | Cuántas personas hay y en qué zona |
| **LightSensor** | `backend/agents/light_sensor.py` | Cuánta luz natural entra por zona |
| **Voice** | `backend/agents/voice.py` | Órdenes, escenas de clase y avisos de emergencia hablados |
| **DigitalTwin** | `backend/agents/digital_twin.py` | Estado del salón y contabilidad de energía |
| **Emergency** | `backend/agents/emergency.py` | Ruta de evacuación iluminada (añadido después del plan original) |

El plan original tenía 5; hoy son **6**. El de emergencias nació del Boost y
manda sobre todos los demás, incluida la voz.

---

## 2 · El salón

```
        ventanas (muro izquierdo, x = 0)
   ┌───────────────┬───────────────┐
   │  A frente-izq │  B frente-der │   y < 4   ← tablero al frente
   ├───────────────┼───────────────┤
   │  C atrás-izq  │  D atrás-der  │   y ≥ 4   ← puerta en D
   └───────────────┴───────────────┘
     x < 5           x ≥ 5
```

- 10 m × 8 m, 4 zonas, 2 lámparas de 40 W por zona → **320 W** con todo prendido.
- `ON` 80 W · `DIM` 40 W · `BLINK` 40 W (parpadea, prendida la mitad del tiempo) · `OFF` 0 W.
- Exposición a la ventana por zona: A 1.00 · C 0.70 · B 0.40 · D 0.20.
  Por eso A se apaga sola mucho antes que D.

Definido en `backend/skills/zone_mapping.py` y `backend/shared/thresholds.py`.

---

## 3 · Cómo decide

`backend/skills/decision_engine.py`, en este orden:

1. Salón vacío → **todo OFF**.
2. Luz natural ≥ 75 % en la zona → **OFF** (sobra sol).
3. Luz natural ≥ 40 % → **DIM** (medio sol, media luz).
4. Zona sin gente → **OFF**.
5. Si no → **ON**.

Y por encima de todo eso, en `orchestrator._decide()`:

```
EMERGENCIA  ▸  VOZ  ▸  MOTOR DE REGLAS
```

La emergencia gana incluso sobre la voz, a propósito: **la voz manda sobre la
comodidad, no sobre la seguridad.** Para recuperar el control hay que declarar
explícitamente que la emergencia terminó.

La luz natural sale de una senoide entre las 6:00 y las 18:00 multiplicada por
el clima (`clear` 1.00 · `cloudy` 0.55 · `overcast` 0.30 · `rainy` 0.15) y por
la exposición de cada zona — `backend/skills/natural_light_simulation.py`.

### La hora es la de Colombia, no la del servidor

Todo lo que dependa de «qué hora es en el salón» pasa por
`backend/shared/clock.py`, que responde en `America/Bogota`. **Nadie debe usar
`datetime.now()` a secas.**

El servidor de Render corre en UTC, cinco horas adelante. Con el reloj del
servidor, a la una de la tarde el gemelo creía que eran las seis: sol puesto,
luz natural en `0.0` en las cuatro zonas y la IA encendiendo todo — justo lo
contrario de lo que el proyecto quiere mostrar, y en plena franja de la feria.
Se puede cambiar de país con la variable de entorno `CLASSROOM_TZ`.

Ojo: esto solo se nota con el botón **Real** puesto. El backend arranca con la
hora simulada en **10 h**, así que al abrirlo la hora del servidor no se ve.

---

## 4 · Emergencias

`backend/skills/emergency_protocol.py`. La idea viene de la señalización de
evacuación real:

- **Luz fija (ON)** = por aquí se sale.
- **Luz intermitente (BLINK)** = aquí no te quedes.

La puerta está en la zona D. La ruta **no está escrita a mano**: se calcula con
la ocupación que reporta el VisionAgent. Si hay gente en A, su camino a la
puerta pasa por B o por C, así que esa zona intermedia también se enciende fija.
Es la misma integración entre agentes del modo normal, aplicada a evacuar.

La velocidad del parpadeo comunica gravedad antes de que nadie lea un cartel:
incendio 350 ms · sismo 600 ms · simulacro 900 ms.

---

## 5 · Cámara real

Opcional, y es lo que separa el proyecto de una simulación pura.

- Modelo **BlazeFace** (465 KB), **incluido en el repo** — funciona al clonar y
  también en el sitio publicado, sin descargar nada.
- Corre **100 % en el navegador**. Ninguna imagen sale del computador, ni
  siquiera hacia el backend: lo único que viaja son las coordenadas de zona.
- La cámara va **al frente del salón, junto al tablero**. Entonces:
  cara grande = cerca = frente (**A·B**); cara pequeña = lejos = fondo (**C·D**).
  La posición horizontal decide izquierda/derecha.
- Requiere origen seguro: `localhost` o HTTPS.
- Si no llegan detecciones en 8 s (`LIVE_STALE_SECONDS`), el VisionAgent vuelve
  solo a simulación. La feria no se cae si alguien tapa la cámara.

El resto del sistema no sabe si los datos vienen de la cámara o del simulador:
solo cambia la capa de sensores.

---

## 6 · El gemelo 3D

Todo vive en **`backend/static/index.html`** (~3100 líneas: React por CDN,
Three.js, sin paso de compilación). Lo que hay hoy:

- Vista de casa de muñecas: los muros del fondo son planos de una sola cara, así
  que desde afuera se ve el interior completo.
- **Ventanas hexagonales** caladas de verdad en el muro, no texturas.
- **Exterior envolvente**: pasto, árboles, matas al pie del muro, cordillera y
  cúpula de cielo pintada en canvas.
- **Zócalo y remate de concreto**. Sin ellos el salón flotaba sobre el pasto y
  se leía como maqueta de cartulina.
- **La hora del día manda sobre todo el exterior**: paleta de cielo, color e
  intensidad del sol, disco del sol visible y — lo importante — **la posición
  de la luz**. Mover la luz es lo que alarga las sombras al amanecer y las
  acorta al mediodía; sin eso, recolorear el cielo no convence a nadie.
- **El clima no repinta el cielo, lo agrisa y lo apaga.** Así un día nublado a
  las 7 sigue teniendo luz de amanecer, solo que lavada. Hora y clima se
  componen en vez de pisarse.
- Haces de sol y manchas hexagonales en el piso, calculados desde la posición
  real del sol.

**Detalle que costó encontrar:** Three.js trabaja en espacio lineal y sale a
pantalla en sRGB, así que multiplicar un color por 0.43 se ve como un 69 % de
brillo. Por eso las 6 y las 12 seguían pareciéndose aunque el código estuviera
bien. Se corrige con `dimmer(k) = k^2.2`.

### El orden de los paneles

De arriba abajo: **Controles Demo · Zonas · Voz · Alerta de Desastre · Consumo ·
Huella de Carbono.** Primero lo que el visitante toca, después lo que el sistema
responde. En pantalla ancha eso se lee bajando la columna derecha; en celular
todo se aplana en una sola columna y **el orden se mantiene igual**.

Cómo está hecho, por si hay que mover un panel: cada panel lleva una clase
(`s-demo`, `s-zones`, `s-voice`, `s-emg`, `s-energy`, `s-carbon`, `s-3d`). Por
debajo de 900 px las dos columnas se vuelven `display: contents` —dejan de
existir como cajas— y sus paneles pasan a ser hijos directos de `main`, donde
el orden lo decide la propiedad `order`. Así se cambia el orden en celular
tocando solo el CSS, sin duplicar marcado.

**Trampa que costó un rato:** una celda de grid no se encoge por debajo de su
contenido más ancho, y el lienzo 3D conserva en píxeles el tamaño que tenía en
escritorio. Resultado: en un celular de 375 px la columna se quedaba en 840 y la
página entera se iba de lado. Se arregla con `min-width: 0` en los hijos de
`main` — está comentado en el CSS.

---

## 7 · Estructura real del repositorio

```
smart-classroom/
├── backend/                     ← todo lo que corre
│   ├── main.py                  FastAPI: rutas, WebSocket, monta /app y /vendor
│   ├── agents/                  los 6 agentes
│   ├── skills/                  la lógica pura, sin estado
│   ├── routes/                  la API REST por agente
│   ├── shared/                  estado, umbrales, log, broadcaster, clock
│   ├── static/                  ← LA INTERFAZ REAL
│   │   ├── landing.html         página de entrada
│   │   ├── index.html           gemelo digital 3D + tablero
│   │   ├── empathy-map.html     entregables de la feria
│   │   ├── journey-map.html
│   │   └── vendor/              React, Three.js, Babel, BlazeFace (offline)
│   └── data/energy_logs.csv     mediciones (se regenera al correr)
├── agents/                      AGENT.md y SKILL_*.md — las instrucciones
├── shared_skills/               con que Claude Code construyó el sistema
├── deploy/                      generado; NO editar (y fuera de git a propósito)
├── scripts/build-deploy.sh      arma deploy/ desde backend/static/
├── .github/workflows/deploy.yml publica en GitHub Pages con cada push a main
├── frontend/                    ⚠️ React+Vite del primer commit — YA NO SE USA
├── CLAUDE.md   DEPLOY.md   PITCH.md   GUION.md   PLAN_BOOST.md
└── run.sh
```

⚠️ **Dos trampas heredadas, para que nadie pierda una tarde:**

1. `frontend/` es la versión React+Vite original. La interfaz que se usa y se
   publica es `backend/static/index.html`. `frontend/` quedó congelado en el
   primer commit.
2. Por lo mismo, **`run.sh` levanta el frontend viejo en el puerto 5173.** Para
   ver el proyecto de verdad, levanta solo el backend y abre `/app/`:

```bash
cd backend && python3 -m uvicorn main:app --reload --port 8000
```

Luego → **http://localhost:8000/app/**

---

## 8 · API

Todo bajo `/api/…`, documentado solo en `http://localhost:8000/docs`.

| Prefijo | Sirve para |
|---|---|
| `/api/twin` | `state`, `energy/history`, `energy/stats`, `report`, `mode`, `reset` |
| `/api/vision` | `occupancy`, `positions`, `scenarios`, `scenario`, `live`, `mode` |
| `/api/light` | `levels`, `thresholds`, `weather-options`, `weather`, `time` |
| `/api/voice` | `command`, `latest`, `pending`, `history`, `clear` |
| `/api/orchestrator` | `status`, `cycle`, `history`, `mode`, `clear-override` |
| `/api/emergency` | `status`, `types`, `trigger`, `clear` |

Además: `GET /health` (Render lo usa para el health check), `GET /state`,
y `WS /ws`, que empuja `STATE_UPDATE` y `LIGHTING_DECISION` a cada navegador
conectado.

Escenarios de ocupación: `empty` (0) · `few` (6) · `half_class` (12) ·
`full_class` (30) · `back_only` (12, solo al fondo).

---

## 9 · Voz

`backend/skills/command_parser.py` entiende español e inglés. Reconoce tres
cosas, y las busca **en este orden**: emergencia, escena, orden literal.

### Órdenes literales

| Dices | Pasa |
|---|---|
| «apaga todas las luces» | todo OFF, modo MANUAL |
| «enciende la zona A» | solo A en ON |
| «media luz en zona B» | B en DIM |
| «modo automático» | suelta el control y vuelve a AUTO |

### Escenas: se dice lo que se va a hacer, no qué luz tocar

Nadie dice «apaga las zonas A y B y atenúa C y D». Dice «vamos a ver una
película». Una escena traduce una intención de clase a un patrón de luces —
que es lo que hace una instalación real: el interruptor de verdad no está
etiquetado «zona A», está etiquetado «proyección».

| Dices | Escena | Luces |
|---|---|---|
| «vamos a ver una película», «pon el proyector», «diapositivas» | Proyección | A y B **OFF**, C y D **DIM** |
| «hora de leer», «hay examen», «taller escrito» | Lectura o examen | las cuatro **ON** |
| «nos vamos», «recreo», «se acabó la clase» | Salida | las cuatro **OFF** |
| «trabajo en grupo», «por equipos» | Trabajo en grupo | devuelve el mando a la IA |

Fíjate en la primera: una escena puede tratar cada zona distinto. Para proyectar
se apagan las de adelante, que son las que lavan la pantalla, y las de atrás
quedan atenuadas para poder tomar apuntes sin quedar a oscuras. **Eso es lo que
separa una señal de un interruptor.**

Lectura y examen encienden todo a propósito: ahí no se ahorra a costa de la
vista.

### Emergencias dichas de viva voz

Nadie grita «activar protocolo de evacuación tipo incendio». Grita «¡fuego!».

| Dices | Pasa |
|---|---|
| «hay un incendio», «fuego», «hay humo» | modo emergencia — incendio |
| «está temblando», «sismo», «terremoto» | modo emergencia — sismo |
| «esto es un simulacro» | modo simulacro |
| «ya pasó», «falsa alarma», «todo despejado» | termina la emergencia |

Dos detalles de diseño:

- La emergencia **no pasa por la cola de voz**. Se despacha en el mismo
  `POST /api/voice/command` (`backend/routes/voice_routes.py`), sin esperar al
  siguiente ciclo del Orquestador: entre gritar «¡fuego!» y ver la ruta
  iluminada no puede haber cinco segundos de nada.
- **Ninguna orden de luces la cancela.** Solo la apaga una frase explícita de
  «todo despejado». La voz manda sobre la comodidad, no sobre la seguridad.
- Por eso «clear» se revisa **antes** que los tipos de emergencia: «terminó el
  simulacro» contiene la palabra «simulacro», y al revés la volvería a encender.

La orden de voz **se queda puesta** hasta que se diga «modo automático»: no es
un pulso, es un override. Solo funciona en **Chrome**.

> Las frases de ejemplo que muestra el tablero están en `VOICE_EXAMPLES`
> (`backend/static/index.html`) y tienen que coincidir con las palabras clave de
> `command_parser.py`. Si se cambia una, se cambian las dos.

---

## 10 · Energía

- Base de comparación: 8 lámparas × 8 h = **2.56 kWh/día**.
- Meta: **40–60 % de ahorro**.
- Tarifa usada en el tablero: **800 COP/kWh**, 8 h/día, 200 días de clase.
- Cada ciclo de 5 s escribe una fila en `backend/data/energy_logs.csv`
  (`backend/skills/energy_tracker.py`).

> Pendiente conocido: los 800 COP/kWh están escritos en el frontend
> (`ComparisonPanel` en `index.html`) y no en el backend. Si algún día cambia la
> tarifa, hay que tocarlos ahí.

---

## 11 · Publicación

```
   NAVEGADOR
       ├── páginas ──► GITHUB PAGES  https://victolopezhernandez-rgb.github.io/smart-classroom/
       └── datos ────► RENDER        https://smart-classroom-rtne.onrender.com
```

GitHub Pages no ejecuta Python; por eso el backend vive aparte. Un `git push` a
`main` actualiza los dos en 1–3 minutos: el sitio lo arma el flujo de trabajo
`.github/workflows/deploy.yml` y el avance se ve en la pestaña **Actions**.
**Solo se publica lo que está en git.** Nunca edites `deploy/`: se regenera.

> Antes esto estaba en Netlify. Se mudó a GitHub Pages en agosto de 2026 al
> acabarse los créditos, y **no hubo que tocar una sola línea de código**: el
> gemelo elige a qué backend hablarle según dónde esté abierto, no según dónde
> esté publicado. `netlify.toml` quedó en el repositorio pero ya no se usa.

Detalles completos —incluido cómo volver a una versión anterior— en
[DEPLOY.md](DEPLOY.md).

### El día de la feria

- Abre `https://smart-classroom-rtne.onrender.com/health` **un minuto antes**.
  El plan gratuito de Render duerme el servidor tras 15 min sin uso, y despertar
  tarda ~50 s.
- Usa **Chrome**: la voz no funciona en Firefox.
- Lleva las dos URLs anotadas por si falla el wifi.
- Sin internet: `cd backend && python3 -m uvicorn main:app --port 8000` y
  `http://localhost:8000/app/`. Todo (React, Three.js, BlazeFace) está en
  `vendor/`, así que funciona offline.

---

## 12 · Los otros documentos

| Archivo | Para qué |
|---|---|
| `CLAUDE.md` | El plan con que se construyó, ya puesto al día. Incluye las convenciones que hay que respetar al tocar código |
| `DEPLOY.md` | Publicar, actualizar y rescatar el sitio |
| `PITCH.md` | Argumento y sustento del proyecto |
| `GUION.md` | Qué decir en la presentación |
| `PLAN_BOOST.md` | Las mejoras posteriores (cámara real, emergencias) |
| `agents/*/AGENT.md` | Las instrucciones con que Claude Code escribió cada agente |
