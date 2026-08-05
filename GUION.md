# Guion de presentación — Smart Classroom AI

**Duración: 7:31** · 978 palabras habladas

Lo que está **[entre corchetes]** no se dice: es lo que haces.
Todo lo demás se dice tal cual.

---

**[Pantalla apagada. No abras el computador todavía. Párate al frente, no detrás
del escritorio. Respira. Mira a la gente.]**

---

## ACTO 1 · La situación · `0:00 – 0:49`

Piensen en su salón de clase. Once de la mañana: sol afuera, ventanas abiertas, y
las ocho lámparas del techo prendidas. Todas.

A las once y media suena el timbre y todos salen a descanso. El salón queda
vacío... y las ocho lámparas siguen prendidas.

Nadie las apagó. Y no es que a nadie le importe: es que **no es tarea de nadie**.
El profesor va de salón en salón; el aseador llega a las seis.

**[Pausa. Dos segundos.]**

Hicimos la cuenta: ocho lámparas de cuarenta vatios son **trescientos veinte
vatios**, ocho horas al día. Y el colegio paga eso igual, esté el salón lleno o
vacío, haya sol o no haya.

---

## ACTO 2 · La tensión · `0:49 – 1:48`

Aquí uno diría: fácil, pongan sensores de movimiento. Nosotras empezamos por ahí,
y encontramos tres problemas.

**[Cuenta con los dedos. Que se vea.]**

**Primero:** el sensor es ciego al sol. Un salón lleno a mediodía, con luz
entrando por la ventana, tiene las luces prendidas igual.

**Segundo:** no sabe *dónde* está la gente. Si quedan cinco estudiantes adelante
en un salón de treinta, prende las ocho lámparas.

**Y tercero, el grave: nadie compra lo que no puede medir primero.** Ningún
rector manda a cablear un salón por una promesa: pregunta cuánto se va a ahorrar
exactamente. Y la única forma de responderle sería instalando todo — justo lo que
no quiere pagar sin saber.

**[Baja la voz. Este es el nudo.]**

Ese círculo vicioso frena la eficiencia energética en los colegios de Colombia.
**No es un problema de tecnología: es un problema de evidencia.** Y ahí cambiamos
la pregunta.

---

## ACTO 3 · La solución · `1:48 – 4:45`

Dejamos de preguntar *"¿cómo apagamos las luces?"* y empezamos a preguntar
**"¿cómo probamos que apagarlas sirve, sin instalar nada?"**

La respuesta se llama **Gemelo Digital**. No la inventamos nosotras: es la
técnica con la que la NASA prueba naves antes de lanzarlas. Es una réplica
virtual que **se comporta** como lo real: no un dibujo — un modelo que corre.

**[AHORA abre la pantalla. Momento de revelación.]**

Este es nuestro salón. Cuatro zonas de iluminación, dos lámparas cada una.
Ventanas a la izquierda, tablero adelante.

**[Gira el modelo. Que vean que es 3D de verdad.]**

Y adentro corre el sistema de Inteligencia Artificial completo: **cinco agentes**.

**[Señala cada uno al nombrarlo.]**

El **Vision Agent** cuenta personas y en qué zona están. El **Light Sensor**
calcula la luz natural según hora y clima. El **Voice Agent** escucha órdenes por
voz. El **Digital Twin** mide la energía y la traduce a pesos y a CO₂. Y el
**Orquestador** es el cerebro: **cada cinco segundos** decide qué hace cada zona.

Los separamos así a propósito: **hoy el Vision Agent simula personas; mañana se
le conecta una cámara real y el resto del sistema no se entera.** Esa
arquitectura por capas es la lógica del **Internet de las Cosas** — objetos que
miden, se comunican y actúan. Hoy nuestros sensores son virtuales; el día que
sean físicos, solo cambia esa capa. Nada más.

**[DEMO 1 — personas a cero.]**

Saco a toda la gente del salón. Todas apagadas. Pero fíjense en el registro:
**no dice solo "apagué", dice por qué.** "Cero personas presentes." Cada decisión
queda escrita con su hora y su razón. Es **auditable**.

**[DEMO 2 — treinta personas, mediodía, despejado.]**

Ahora meto treinta estudiantes, mediodía, día despejado. Las zonas A y C tienen
ventana; B y D no.

**[Señala la pantalla.]**

Miren: **A y C apagadas** aunque estén llenas — "luz natural al ochenta y seis
por ciento, suficiente". **B y D prendidas.** Mismo salón, misma hora, la misma
gente.

Un sensor de movimiento no puede hacer esa distinción. **Este sistema decide zona
por zona, y cada zona tiene su propia razón.** Y hay un tercer estado: atenuado a
media potencia, cuando hay algo de luz pero no suficiente.

**[DEMO 3 — voz. Si el wifi está inestable, sáltala.]**

Y el profesor siempre manda: **"Enciende todas las luces."**

**[Las luces se prenden.]**

Regla número cuatro: **la voz humana anula a la IA.** La tecnología asiste; no
manda.

---

## Los números · `4:45 – 5:25`

¿Cuánto da? El Gemelo mide las dos versiones del mismo día: con Inteligencia
Artificial, **entre cuarenta y sesenta por ciento menos consumo.**

Cada kilovatio-hora consumido en Colombia genera **ciento veintiséis gramos de
CO₂** — factor oficial de la UPME. En un año escolar, un salón pasa de sesenta y
cuatro kilos a unos veintiséis. Los **treinta y ocho que se ahorran son casi dos
árboles al año**.

Lo decimos en árboles porque "treinta y ocho kilos de CO₂" no le significa nada a
nadie. Y en un colegio de cien salones, **cuatro toneladas cada año**.

---

## La debilidad · `5:25 – 6:53`

**[Cambia el tono: más bajo, más lento. Mira a los jueces.]**

Antes de terminar, la pregunta que yo haría en su lugar.

**Este sistema no ha controlado nunca una lámpara real.** Nuestro agente de
visión no ve con una cámara: simula. Nuestro sensor de luz no mide el sol: lo
modela. Los porcentajes que les mostré son **proyecciones de un modelo, no
mediciones de un salón físico**. Y no lo voy a maquillar.

**[Pausa. Ahora el giro.]**

Pero lo decidimos así, y no por falta de presupuesto. **Un Gemelo Digital se
construye precisamente para esto:** simular antes de construir no es la versión
barata de la ingeniería — es una etapa de la ingeniería. Boeing no estrella
aviones para probar un ala: la simula.

**No simulamos porque no pudiéramos instalar sensores. Simulamos porque instalar
sensores sin simular primero es hacerlo al revés.**

Y estos números no son una promesa: son un modelo con **todos sus supuestos a la
vista**, que cualquiera puede revisar y cambiar.

El siguiente paso ya lo tenemos: un salón, dos sensores y un microcontrolador,
menos de cien mil pesos. Ese montaje **no reemplaza al Gemelo: lo calibra.** Y
calibrado con un salón real, **el Gemelo predice los otros cuarenta sin instalar
nada.** Instrumentas uno, modelas todos.

---

## Cierre · `6:53 – 7:31`

**[Levanta la mirada. Baja el ritmo.]**

Y esto es lo que queremos que se lleven. No les traemos un salón ahorrando
energía: les traemos **la herramienta con la que se decide si vale la pena
hacerlo**, antes de comprar un solo sensor.

Este mismo Gemelo se reconfigura para una biblioteca o un auditorio: se cambian
las medidas en un archivo y la IA es la misma. **Lo que construimos no es un
salón: es un método.**

Y está en internet, funcionando en este momento.

**[Muestra la URL pública.]**

Muchas gracias.

---

# 📋 Recordatorios

**Sobre el tiempo.** Los `7:31` de arriba están medidos: 978 palabras a 150
palabras por minuto, más ~55 segundos de pausas y demostraciones. Es un ritmo
normal de presentación, no acelerado. **Cronométrate leyéndolo en voz alta una
vez** — si te da más de 7:30, aplica los recortes de abajo y quedas en 6:40.

**Si te pasas de tiempo, recorta en este orden:**

1. La demostración de voz — desde *"Y el profesor siempre manda"* hasta
   *"no manda"* (`−25 s`)
2. El párrafo que empieza *"Lo decimos en árboles…"* (`−15 s`)
3. El párrafo que empieza *"Los separamos así a propósito…"* (`−25 s`)

**Los tres momentos que deciden el pitch:**

1. `0:15` — El salón vacío con las luces prendidas. Si se ven ahí, ya los tienes.
2. `3:45` — "Zona A apagada, zona B prendida, mismo salón." Ahí entienden que
   esto no es un sensor de movimiento.
3. `5:30` — "Nunca ha controlado una lámpara real." Ahí se ganan el respeto,
   no lo pierden.

**Nunca recortes:** el círculo vicioso del Acto 2, la demostración de zona A
contra zona B, ni la sección de la debilidad.

**Antes de arrancar:** abre `smart-classroom-rtne.onrender.com/health` un minuto
antes — el servidor se duerme y tarda ~50 segundos en despertar. Usa Chrome. Ten
las URLs en papel y capturas en el celular como plan B.

> Las preguntas de los jueces, las respuestas preparadas y el fondo técnico
> completo de las tres áreas están en **PITCH.md**.
