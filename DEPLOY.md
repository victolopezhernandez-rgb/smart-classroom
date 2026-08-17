# Publicar y actualizar el proyecto

## Cómo está montado

```
   NAVEGADOR
       │
       ├── páginas ──────► GITHUB PAGES   (archivos estáticos)
       │                   https://victolopezhernandez-rgb.github.io/smart-classroom/
       │
       └── datos ────────► RENDER         (Python + los 6 agentes)
                           https://smart-classroom-rtne.onrender.com
```

GitHub Pages no puede ejecutar Python; por eso el backend vive aparte.

El sitio se publica solo con el flujo de trabajo `.github/workflows/deploy.yml`:
cada `push` a `main` corre `scripts/build-deploy.sh` y sube el resultado. No hay
que entrar a ninguna consola ni conectar ninguna cuenta.

> Como el sitio cuelga de `/smart-classroom/` y no de la raíz del dominio, el
> flujo de trabajo le pasa `BASE_PATH=/smart-classroom/` al script, que antepone
> ese prefijo a las rutas `/vendor/…` y `/app/…`. Sin eso todo daría 404. Si
> algún día le pones dominio propio, cambia ese valor a `/`.

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

GitHub Pages y Render detectan el push y se actualizan solos en 1–3 minutos.
El avance se ve en la pestaña **Actions** del repositorio.

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

**Volver a la versión anterior:** deshaz el commit y vuelve a empujar. Como cada
push republica el sitio, el `git revert` es el botón de retroceso:

```bash
git revert HEAD && git push
```

**El sitio no se actualizó:** mira la pestaña **Actions** del repositorio. Si el
flujo de trabajo falló, el error sale en el registro del paso que se puso rojo.
Para volver a publicar sin cambiar nada: **Actions** → *Publicar en GitHub
Pages* → **Run workflow**.

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

La cámara solo funciona en **origen seguro**: `localhost` o HTTPS. GitHub Pages
da HTTPS, así que sirve en los dos casos.

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

## Cómo quedó montada la publicación (ya está hecho)

No hay nada que configurar: todo está en `.github/workflows/deploy.yml`, dentro
del repositorio. Se explica aquí por si hay que rehacerlo o mudarlo a otro lado.

- Se dispara con cada `push` a `main`, y también a mano desde **Actions**.
- Arma el sitio con `BASE_PATH=/smart-classroom/ bash scripts/build-deploy.sh`.
- Sube la carpeta `deploy/` como artefacto y la publica en GitHub Pages.
- El paso `configure-pages` lleva `enablement: true`, así que prende Pages solo
  la primera vez sin tener que entrar a **Settings**.

`deploy/` está en `.gitignore` **a propósito**: no se sube a git, se genera en
cada publicación. Por eso nunca hay que editarla ni versionarla.

> ⚠️ Solo se publica **`main`**. La rama de pruebas `prueba-coco-ssd` **no se
> puede publicar**: usa un modelo de 65 MB que no está en git, así que allá la
> cámara daría 404.

El backend ya está en Render y acepta peticiones desde cualquier origen, así que
no hay que tocar nada más: la app publicada se conecta sola. El gemelo decide a
qué backend hablarle según dónde esté abierto (`window.API_BASE` en
`index.html`): en `localhost` habla con el servidor local, y en cualquier otro
sitio con Render. Por eso mudarse de Netlify a Pages no obligó a tocar código.

> `netlify.toml` sigue en el repositorio, pero **ya no se usa**. Se puede borrar
> cuando quieras; no molesta.

---

## ⚠️ El día de la feria

- Abre `https://smart-classroom-rtne.onrender.com/health` **un minuto antes**
  de presentar. El plan gratuito duerme el servidor tras 15 min sin uso.
- Usa **Chrome** — el control por voz no funciona en Firefox.
- Lleva las dos URLs anotadas por si falla el wifi:
  - Sitio: `https://victolopezhernandez-rgb.github.io/smart-classroom/`
  - Backend: `https://smart-classroom-rtne.onrender.com`
