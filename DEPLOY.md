# Publicar y actualizar el proyecto

## Cómo está montado

```
   NAVEGADOR
       │
       ├── páginas ──────► NETLIFY   (archivos estáticos)
       │
       └── datos ────────► RENDER    (Python + los 5 agentes)
                           https://smart-classroom-rtne.onrender.com
```

Netlify no puede ejecutar Python; por eso el backend vive aparte.

---

## Actualizar la página (el flujo normal)

### 1 · Edita el original

| Quieres cambiar | Edita este archivo |
|---|---|
| La página principal | `backend/static/landing.html` |
| El gemelo digital 3D | `backend/static/index.html` |
| El mapa de empatía | `backend/static/empathy-map.html` |
| El journey map | `backend/static/journey-map.html` |
| La lógica de los agentes | `backend/agents/…` |

### 2 · Sube el cambio

```bash
git add -A && git commit -m "describe tu cambio" && git push
```

### 3 · Ya está

Netlify y Render detectan el push y se actualizan solos en 1–3 minutos.

> ⚠️ **Nunca edites nada dentro de `deploy/`.** Esa carpeta se regenera
> automáticamente y tus cambios se perderían. El original vive en
> `backend/static/`.

---

## Ver los cambios antes de publicar

```bash
bash scripts/build-deploy.sh
```

Genera `deploy/` en tu computador para revisarlo localmente.

---

## Si algo sale mal

**Volver a la versión anterior:** en Netlify, pestaña **Deploys** → elige un
despliegue anterior → **Publish deploy**. Vuelve atrás en segundos.

**El sitio no se actualizó:** revisa la pestaña **Deploys** en Netlify. Si el
build falló, el error aparece en el log.

**La app 3D dice 🔴 Conectando:** el backend está dormido. Abre
`https://smart-classroom-rtne.onrender.com/health` y espera 50 segundos.

---

## 🎥 Cámara real (Boost 1) — un paso obligatorio tras clonar

> **Estás en la rama `prueba-coco-ssd`.** Es la versión con detector de
> **cuerpo entero**, para compararla contra la de **rostros** que está en
> `main`. Ver "Cuál de las dos usar" más abajo.

El modelo de visión es **COCO-SSD**, un detector de objetos del que solo se usa
la clase `person`. Los pesos no están en el repo. Con internet, una sola vez:

```bash
python3 backend/scripts/fetch_vision_models.py     # ~65 MB, tarda un par de minutos
python3 backend/scripts/fetch_vision_models.py --check   # confirma que quedó completo
```

Quedan en `backend/static/vendor/models/` (ignorado por git). A partir de ahí la
detección corre **100% en el navegador y sin internet**: ninguna imagen de la
cámara sale del computador.

Qué mide y cómo: la posición horizontal decide izquierda/derecha del salón
(A·C vs B·D), y el **tamaño de la caja** decide frente/fondo, porque alguien se
ve más grande cuanto más cerca está. La cámara va **al frente del salón, junto
al tablero**, así que acercarse a ella es acercarse al frente:

| En cámara | En el salón |
|---|---|
| caja grande (cerca) | frente → zonas **A·B** |
| caja pequeña (lejos) | fondo → zonas **C·D** |

Con cuerpos hay una trampa que con rostros no existe: al acercarse, la cabeza o
los pies se salen del cuadro y **la caja queda recortada**, así que el alto deja
de crecer justo en el rango que más importa. Por eso, si la caja toca el borde
de arriba o el de abajo se mide por el **ancho** (el tramo de hombros) y si no,
por el **alto**, que tiene más rango. Cada recuadro dice en pantalla cuál de las
dos se usó y cuánto dio — sirve para calibrar.

**Calibrar:** párate donde vas a estar en la feria, lee el número del recuadro y
ajusta `BODY_NEAR_H` / `BODY_FAR_H` / `BODY_NEAR_W` / `BODY_FAR_W` en
`backend/static/index.html`. Si algún día la cámara se pone al fondo del salón,
hay que invertir el `1 -` de `depthFromBody()`.

---

## 🔬 Cuál de las dos usar

|  | `main` — rostros (BlazeFace) | `prueba-coco-ssd` — cuerpos |
|---|---|---|
| Pesos | 465 KB | 65 MB |
| Carga | 27 ms | 1.4 s |
| Inferencia | ~30 ms | ~65 ms |
| Alcance | hasta ~2 m (modelo de corto alcance) | varios metros |
| Señal de distancia | tamaño de la cara, nunca recortada | tamaño de la caja, se recorta de cerca |
| Falla si… | la persona está de espaldas o muy lejos | hay poca separación entre personas |

Para cambiar de una a otra:

```bash
git checkout main            # rostros
git checkout prueba-coco-ssd # cuerpos
```

Los pesos de ambos ya están en `backend/static/vendor/models/`, así que cambiar
de rama no obliga a volver a descargar nada.

Para verificar la carga offline, con el server arriba:
`http://localhost:8000/app/_test_vision.html` → debe imprimir `RESULT: OFFLINE_LOAD_OK`.

La cámara solo funciona en **origen seguro**: `localhost` o HTTPS. En la feria se
corre local (`./run.sh`), así que no hay problema.

---

## ⚠️ El día de la feria

- Abre `https://smart-classroom-rtne.onrender.com/health` **un minuto antes**
  de presentar. El plan gratuito duerme el servidor tras 15 min sin uso.
- Usa **Chrome** — el control por voz no funciona en Firefox.
- Lleva las dos URLs anotadas por si falla el wifi.
