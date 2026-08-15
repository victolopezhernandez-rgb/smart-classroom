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

El modelo de visión es **BlazeFace**, un detector de **rostros**. Los pesos no
están en el repo. Con internet, una sola vez:

```bash
python3 backend/scripts/fetch_vision_models.py     # <1 MB, tarda segundos
python3 backend/scripts/fetch_vision_models.py --check   # confirma que quedó completo
```

Quedan en `backend/static/vendor/models/` (ignorado por git). A partir de ahí la
detección corre **100% en el navegador y sin internet**: ninguna imagen de la
cámara sale del computador.

Qué mide y cómo: la posición horizontal del rostro decide izquierda/derecha del
salón (A·C vs B·D), y el **tamaño** del rostro decide frente/fondo, porque una
cara se ve más grande cuanto más cerca está. La cámara va **al frente del salón,
junto al tablero**, así que acercarse a ella es acercarse al frente:

| En cámara | En el salón |
|---|---|
| cara grande (cerca) | frente → zonas **A·B** |
| cara pequeña (lejos) | fondo → zonas **C·D** |

Si algún día la cámara se pone al fondo del salón, hay que invertir el `1 -` de
`depthFromFace()` en `backend/static/index.html`.

Con `--all` se bajan además los detectores de cuerpo COCO-SSD (~83 MB), que
quedan como plan B pero ya no los usa la demo.

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
