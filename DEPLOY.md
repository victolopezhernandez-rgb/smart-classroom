# Publicar y actualizar el proyecto

## Cómo está montado

```
   NAVEGADOR
       │
       ├── páginas ──────► NETLIFY   (archivos estáticos)
       │
       └── datos ────────► RENDER    (Python + los 6 agentes)
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

## 🎥 Cámara real (Boost 1)

El modelo de visión es **BlazeFace**, un detector de **rostros**. Pesa 465 KB y
**está en el repo**, así que no hay que descargar nada: funciona al clonar y
también en el sitio publicado.

La detección corre **100% en el navegador**: ninguna imagen de la cámara sale
del computador, ni siquiera hacia el backend. Lo único que viaja son las
coordenadas de las zonas. Tampoco necesita internet, así que en la feria
funciona igual con `./run.sh`.

La cámara solo funciona en **origen seguro**: `localhost` o HTTPS. Netlify da
HTTPS, así que sirve en los dos casos.

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

Para verificar la carga offline, con el server arriba:
`http://localhost:8000/app/_test_vision.html` → debe imprimir `RESULT: OFFLINE_LOAD_OK`.

Los detectores de cuerpo COCO-SSD (~83 MB) son plan B y **no** están en el repo
por su tamaño. Si algún día hacen falta:
`python3 backend/scripts/fetch_vision_models.py --all` (necesita internet).

---

## Crear el sitio en Netlify (solo la primera vez)

1. Entra a [app.netlify.com](https://app.netlify.com) → **Add new site** →
   **Import an existing project** → **GitHub** → elige este repositorio.
2. Netlify lee `netlify.toml` y rellena solo el build:
   - Branch: **`main`**
   - Build command: `bash scripts/build-deploy.sh`
   - Publish directory: `deploy`
3. **Deploy site.** En 1–2 minutos queda publicado en una URL
   `https://algo-random.netlify.app`, que puedes renombrar en
   **Site configuration → Change site name**.

> ⚠️ La rama de producción tiene que ser **`main`**. La rama de pruebas
> `prueba-coco-ssd` **no se puede publicar**: usa un modelo de 65 MB que no está
> en git, así que allá la cámara daría 404.

El backend ya está en Render y acepta peticiones desde cualquier origen, así que
no hay que tocar nada más: la app publicada se conecta sola.

---

## ⚠️ El día de la feria

- Abre `https://smart-classroom-rtne.onrender.com/health` **un minuto antes**
  de presentar. El plan gratuito duerme el servidor tras 15 min sin uso.
- Usa **Chrome** — el control por voz no funciona en Firefox.
- Lleva las dos URLs anotadas por si falla el wifi.
