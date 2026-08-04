# Publicar el proyecto en internet

El proyecto tiene dos mitades que van a servicios distintos:

| Mitad | Qué es | Dónde va | Por qué |
|---|---|---|---|
| Páginas web | `deploy/` | **Netlify** | Son archivos estáticos |
| Cerebro (API) | `backend/` | **Render** | Necesita correr Python |

Netlify no puede correr Python, por eso el backend va aparte.

---

## Parte 1 · Backend en Render

> ⚠️ Render no acepta arrastrar carpetas: necesita leer el código desde GitHub.
> Este paso es obligatorio antes de continuar.

### 1.1 · Subir el código a GitHub

En la terminal, dentro de la carpeta del proyecto:

```bash
git init
git add .
git commit -m "Smart Classroom AI"
```

Luego crea un repositorio vacío en [github.com/new](https://github.com/new) (sin README) y conecta:

```bash
git remote add origin https://github.com/TU-USUARIO/smart-classroom.git
git branch -M main
git push -u origin main
```

El archivo `.gitignore` ya evita que se suba `node_modules`, así que esta vez no
dará el error de `_baseIntersection.js`.

### 1.2 · Crear el servicio en Render

1. Entra a [render.com](https://render.com) y regístrate con tu cuenta de GitHub.
2. **New → Web Service** y elige el repositorio que acabas de subir.
3. Render leerá el archivo `render.yaml` y rellenará todo solo. Verifica que diga:

   | Campo | Valor |
   |---|---|
   | Root Directory | `backend` |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
   | Instance Type | `Free` |

4. **Create Web Service.** Tarda unos 3 minutos.

### 1.3 · Copiar la URL

Al terminar, Render te da una dirección parecida a:

```
https://smart-classroom-api.onrender.com
```

Compruébala abriendo `https://TU-URL.onrender.com/health` en el navegador.
Debe responder `{"status":"healthy"}`.

**Copia esa URL, la necesitas en el paso siguiente.**

---

## Parte 2 · Conectar las páginas al backend

Abre `deploy/app/index.html` y busca esta línea cerca del inicio (línea ~20):

```js
: "https://smart-classroom-api.onrender.com";
```

Reemplázala por **tu** URL de Render. Guarda el archivo.

> Si Render te dio exactamente ese nombre, no hay que cambiar nada.

---

## Parte 3 · Páginas en Netlify

1. Entra a [app.netlify.com/drop](https://app.netlify.com/drop)
2. Arrastra **únicamente la carpeta `deploy/`** — no la carpeta del proyecto completo.
3. Listo. Netlify te da una URL tipo `https://algo-random.netlify.app`

Puedes cambiar ese nombre en **Site configuration → Change site name**.

### Qué contiene `deploy/`

```
deploy/
├── index.html          ← página principal (la landing)
├── vendor/             ← React y Three.js
└── app/
    ├── index.html      ← el gemelo digital 3D
    ├── landing.html
    ├── empathy-map.html
    └── journey-map.html
```

Son 9 archivos, 4 MB. El error anterior ocurría porque arrastrabas la carpeta
completa con `node_modules` dentro (unos 30.000 archivos de librerías).

---

## Comprobación final

Abre tu sitio de Netlify. En la app 3D, arriba a la derecha debe decir
**🟢 Conectado**. Si dice 🔴 Conectando:

| Causa | Solución |
|---|---|
| El backend está dormido | Espera 50 segundos y recarga |
| La URL quedó mal | Revisa la línea del paso 2 |
| Falta la `s` en `https` | Debe ser `https://`, no `http://` |

---

## ⚠️ Importante para el día de la feria

El plan gratuito de Render **duerme el servidor tras 15 minutos sin uso**.
La primera visita después de eso tarda ~50 segundos en despertar.

**Antes de presentar:** abre `https://TU-URL.onrender.com/health` un minuto
antes de que llegue el jurado. Así el backend ya está despierto y la demo
responde al instante.
