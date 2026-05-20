# PSYCHE SIMULACRA — Lecciones de Simulaciones Exitosas
## Qué tomar y qué descartar de los reyes de la simulación de vida

> *No estamos haciendo un videojuego.  
> Estamos haciendo una simulación de sociedad que construye  
> un inconsciente colectivo con arquetipos.*  
>
> *Pero ellos ya resolvieron problemas que nosotros vamos a tener.*

---

## EL PROBLEMA CENTRAL DE TODA SIMULACIÓN DE VIDA

Antes de analizar cada juego, hay que nombrar el problema que todos
intentaron resolver de formas distintas:

**¿Cómo hacer que agentes simples produzcan comportamiento que parezca complejo?**

La respuesta de cada juego es diferente, y esa diferencia es la lección.

---

## THE SIMS 1 — La Economía de las Necesidades

### Qué hicieron bien

Will Wright diseñó el sistema más elegante de necesidades que existe
en simulación de vida. Ocho variables (hambre, energía, higiene, vejiga,
diversión, social, comodidad, entorno) cada una decayendo a su propia tasa,
cada una con umbrales que modifican el humor base del agente.

**La brillantez:** no modelaron personalidad compleja. Modelaron
**la tiranía de las necesidades básicas** — y dejaron que la personalidad
emergiera de cómo cada Sim priorizaba satisfacerlas.

Un Sim con rasgo "perezoso" no es que "decide ser perezoso".
Es que su tasa de decay de energía es más lenta y su umbral de
disconfort por fatiga es más alto. La pereza es una parametrización,
no un estado.

```
LECCIÓN DIRECTA PARA PSYCHE:
Las necesidades biológicas (hambre, fatiga, energía) no son variables
decorativas. Son el motor que fuerza al agente a actuar aunque
"no quiera". Un agente con hambre alta NO puede quedarse quieto
elaborando símbolos — tiene que salir a buscar comida.
La tensión entre necesidad biológica y proceso psicológico
es donde nace el drama.
```

### El Mood como función de todas las necesidades

```python
# Sims 1 — simplificado conceptualmente
def calculate_mood(sim):
    mood = 0
    for need in sim.needs:
        # Cada necesidad contribuye al humor con su propio peso
        mood += need.current_value * need.mood_weight
    return mood  # -100 → +100

# Para Psyche: el humor_base no es un valor independiente
# Es una función de todas las capas del agente
def calculate_humor_base(agent):
    necesidades  = calcular_satisfaccion_necesidades(agent)
    arquetipos   = calcular_tension_arquetipica(agent)
    campo        = collective_field.get_presion_sobre(agent)
    vinulos      = calcular_calidad_red_social(agent)
    clima        = clima_actual.get_mood_modifier()
    
    return weighted_sum([necesidades, arquetipos, campo, vinulos, clima])
```

### Qué descartar

Los Sims no tienen inconsciente. Sus motivaciones son completamente
transparentes — el jugador siempre sabe por qué un Sim hace algo.
En Psyche, el agente tiene que poder actuar por razones que
**ni él mismo comprende** — eso es el complejo jungiano en acción.

---

## RIMWORLD — Sistemas que se Cruzan Generando Narrativa

### Qué hicieron bien

Rimworld es el ejemplo más sofisticado de **emergencia narrativa**
en videojuegos. No tiene historia — tiene sistemas que colisionan
y producen historias que nadie diseñó.

**La columna vertebral:** cada colono tiene rasgos que modifican
umbrales y probabilidades. No hay un script de "colono psicótico" —
hay un rasgo `psicótico` que baja el umbral de mental break
y sube la probabilidad de actuar con violencia bajo stress.

```python
# Rimworld — mental break system (conceptual)
MENTAL_BREAK_THRESHOLD = {
    "normal":    0.20,   # Rompe si mood < 20%
    "sensible":  0.35,   # Rompe antes
    "duro":      0.10,   # Aguanta más
    "psicótico": 0.40,   # Rompe fácil Y la reacción es violenta
}

# Cuando rompe, el tipo de break depende de los rasgos
BREAK_TYPES = {
    "psicótico":   ["ataque_aleatorio", "destruccion_propiedad"],
    "solitario":   ["huida", "aislamiento"],
    "masoquista":  ["autolesion"],
    "religioso":   ["rezo_compulsivo"],
}
```

**Lo más valioso de Rimworld:** los rasgos **no se cancelan entre sí**.
Un colono puede ser `amable` Y `psicótico`. Eso significa que bajo
condiciones normales es el más cooperativo del grupo — y bajo stress
extremo es el más peligroso. Esa contradicción interna es exactamente
lo que Jung describe como la relación entre Persona y Sombra.

```
LECCIÓN DIRECTA PARA PSYCHE:
Los arquetipos no se cancelan entre sí. Un agente puede tener
héroe: 0.80 Y sombra: 0.75 simultáneamente.
Eso no es inconsistencia — es la estructura de una personalidad
compleja. El héroe con sombra alta es el más poderoso Y el más
peligroso. Jung lo llamó el héroe que lleva su propio monstruo.

Los complejos se activan por umbral, no por estado permanente.
Un agente con complejo de abandono no está siempre en crisis —
está latente hasta que el contexto lo dispara.
Ese disparo es el drama.
```

### El sistema de relaciones de Rimworld

Rimworld rastrea opiniones entre colonos como modificadores acumulados:

```python
# Opinion = suma de todos los modificadores activos
opinion_A_sobre_B = (
    +30  # "Me salvó la vida"
    -20  # "Me atacó en mental break"
    +10  # "Compartimos cuarto"
    -15  # "Tiene rasgo que odio (irresponsable)"
    +5   # "Me dio regalos"
)
# Total: +10 → relación tensa pero positiva
```

**La clave:** cada modificador tiene una **vida útil** — decae con el tiempo.
Los eventos recientes pesan más que los viejos. Pero algunos modificadores
son permanentes ("me salvó la vida" no se olvida nunca).

```
LECCIÓN DIRECTA PARA PSYCHE:
El bond_strength no es un número estático.
Es la suma de todos los eventos compartidos, cada uno con su
propio peso y tasa de decay.
Un trauma compartido no decae — es un entrelazamiento permanente.
Una ayuda cotidiana decae lentamente.
Un insulto público decae rápido si hay reconciliación.
```

### Qué descartar

Rimworld no tiene inconsciente colectivo. El "mood" de la colonia
es solo el promedio de los moods individuales — no hay campo emergente.
Tampoco hay arquetipos — los rasgos son etiquetas que modifican
probabilidades, no estructuras simbólicas con vida propia.

---

## SPORE — La Escala como Narrativa

### Qué hicieron bien

Spore resolvió un problema que nosotros tenemos:
**¿cómo mostrar la emergencia de complejidad social desde lo más simple?**

La estructura en fases (célula → criatura → tribu → civilización → espacio)
es una arquitectura de complejidad incremental perfecta.
Cada fase tiene sus propias reglas, y las fases anteriores
**dejan huellas** en las fases posteriores.

```
LECCIÓN DIRECTA PARA PSYCHE:
El estado arcaico (cazadores-recolectores) no es solo el punto
de partida — es la fase que determina los rasgos fundacionales
que van a persistir en todas las fases posteriores.

Un grupo que en la fase arcaica resolvió sus conflictos con
cooperación va a tener una estructura de campo colectivo distinta
a uno que los resolvió con dominancia.
Esa diferencia fundacional nunca desaparece — se transforma,
pero deja huella en el inconsciente colectivo.

El mito fundador siempre habla del primer modo de resolver
el problema de la supervivencia.
```

### La criatura como vector de capacidades

En Spore, las partes del cuerpo no son cosméticas — cada una
agrega una capacidad. No hay habilidades abstractas — hay
consecuencias físicas concretas de cada decisión de diseño.

```
ANALOGÍA PARA PSYCHE:
Los arquetipos no son etiquetas — son capacidades concretas.

heroe alto → capacidad de acción bajo presión (+efectividad en crisis)
sabio alto → capacidad de generar símbolos (+probabilidad proto-mito)
trickster alto → capacidad de disrumpir patrones (+varianza en interacciones)
madre alto → capacidad de sostener vínculos (+estabilidad de red)

No son "tipos de personalidad" — son vectores de capacidad
que determinan qué puede hacer el agente en cada contexto.
```

### Qué descartar

Spore simplificó demasiado la transición entre fases — cada una
es básicamente un juego distinto con reglas distintas.
No hay continuidad psicológica real entre la criatura y la civilización.

En Psyche, la continuidad psicológica es exactamente lo que importa.
El campo colectivo es el hilo que conecta todas las fases.

---

## BLACK & WHITE 2 — La Criatura como Inconsciente

### Qué hicieron bien

Black & White 2 tiene el sistema más cercano a Jung de todos:
**la Criatura es literalmente el inconsciente del jugador**.

La Criatura aprende por refuerzo — tus reacciones la moldean.
Si castigás la agresión, aprende a ser pacífica. Pero los impulsos
que reprimiste no desaparecen — aparecen en comportamientos
inesperados cuando la Criatura está sin supervisión.

Eso es la Sombra jungiana en código.

```
LECCIÓN DIRECTA PARA PSYCHE:
Lo que se reprime no desaparece — se desplaza.

Si un agente tiene un impulso (agresividad alta) pero su
contexto social lo sanciona constantemente, ese impulso
no se reduce — se acumula en el complejo correspondiente
y eventualmente explota en un contexto de menor control social.

El agente que "siempre se porta bien" en público
y de vez en cuando hace algo inexplicable —
eso es la Sombra. Tiene que estar en el sistema.

Implementación:
Si un arquetipo tiene peso alto pero el agente lo suprime
consistentemente (bond social lo penaliza), el arquetipo
no decae — se convierte en "arquetipo reprimido"
que sube la probabilidad de colapso conductual bajo stress.
```

### El sistema de influencia de aldea

En B&W2, cada aldea tiene necesidades colectivas (comida, madera,
diversión, espiritualidad). El jugador las satisface o no.
Cuando la aldea está bien satisfecha, genera milagros —
capacidades que el jugador puede usar.

La espiritualidad como necesidad colectiva con efectos mecánicos
es la idea más cercana a "campo colectivo con retroalimentación".

```
LECCIÓN DIRECTA PARA PSYCHE:
El campo colectivo no es solo un registro pasivo.
Es una variable que tiene efectos mecánicos sobre los agentes.

Un campo con alta carga de "cohesion" genuinamente
hace que las interacciones sean más cooperativas.
Un campo con alta carga de "miedo" genuinamente
hace que los agentes actúen con más agresividad defensiva.

El campo retroalimenta — no solo registra.
```

### Qué descartar

El sistema de B&W2 requiere un jugador como dios externo.
En Psyche no hay jugador — el investigador observa, no interviene
(salvo en experimentos controlados).

La Criatura es una sola entidad inconsciente — en Psyche,
cada agente tiene su propio inconsciente, y el colectivo emerge
de la interacción de todos ellos.

---

## SÍNTESIS — La Tabla de Sabiduría Destilada

| Juego | Problema que resolvió | Cómo | Aplicación a Psyche |
|-------|----------------------|------|---------------------|
| **Sims 1** | Necesidades que fuerzan acción | Decay rates + umbrales de disconfort | Sistema de hambre/fatiga/sociabilidad con tiranía real |
| **Sims 1** | Personalidad como parametrización | Rasgos = modificadores de umbrales | Arquetipos = modificadores de probabilidades conductuales |
| **Rimworld** | Contradicción interna | Rasgos no se cancelan, se activan por umbral | Héroe + Sombra coexisten — la Sombra espera su momento |
| **Rimworld** | Relaciones como historia acumulada | Opinion = suma de eventos con decay diferencial | bond_strength = suma de eventos ponderados + entrelazamientos permanentes |
| **Rimworld** | Emergencia narrativa | Sistemas que colisionan producen historias | El drama emerge de necesidades × arquetipos × campo × clima |
| **Spore** | Continuidad entre fases | Las fases dejan huellas en las siguientes | El estado arcaico imprime el campo fundacional que persiste |
| **Spore** | Capacidades concretas | Partes del cuerpo = habilidades reales | Arquetipos = vectores de capacidad, no etiquetas |
| **B&W2** | Lo reprimido no desaparece | Criatura aprende pero impulsos persisten | Arquetipo reprimido = complejo latente que explota bajo stress |
| **B&W2** | Campo colectivo con retroalimentación | Necesidades de aldea generan capacidades | Campo no solo registra — modifica probabilidades de todos los agentes |

---

## LO QUE NINGUNO RESOLVIÓ — Y QUE PSYCHE TIENE QUE INVENTAR

### 1. El inconsciente como sistema autónomo

Ningún juego de la lista tiene una capa de inconsciente genuinamente
separada de la conducta observable.

En todos, lo que ves es todo lo que hay.
En Psyche, tiene que haber algo que el agente no ve de sí mismo
y que sin embargo determina su conducta.

Eso es el complejo jungiano — y no existe en ninguna simulación de vida.

### 2. El símbolo como unidad funcional

En todos los juegos, las "ideas" y los "valores" son decorativos.
En Rimworld, que un colono sea "ateo" solo afecta su relación
con colonos religiosos — no produce símbolos, no construye campo,
no genera mitos.

En Psyche, un símbolo tiene que ser una **unidad funcional**
con carga medible que se contagia, se transforma, cristaliza
y retroalimenta. Nada de eso existe en ningún juego conocido.

### 3. El mito como agente sin cuerpo

En ningún juego existe la posibilidad de que una narrativa colectiva
tenga efectos causales sobre los agentes individuales.

En Psyche, un mito emergente tiene que poder cambiar el comportamiento
de agentes que no vivieron el evento que lo generó.
Eso convierte al mito en un tipo de agente sin cuerpo — una entidad
que actúa sobre el sistema aunque no tenga representación física.

### 4. La individuación como arco narrativo

Todos los juegos tienen progresión — los Sims compran muebles mejores,
los colonos de Rimworld suben habilidades, las criaturas de Spore
evolucionan físicamente.

Ninguno tiene **individuación psicológica** — el proceso jungiano
donde la psique integra sus contradicciones y el Self emerge.

En Psyche, un agente que atraviesa un trauma, lo procesa en sueños,
integra su Sombra, y emerge con una configuración arquetípica
cualitativamente distinta — eso no existe en ningún juego.
Tenemos que inventarlo.

---

## PRINCIPIOS DE DISEÑO DESTILADOS

De todo lo anterior, estos son los principios que Psyche debería
adoptar como mandatos de diseño:

```
1. LAS NECESIDADES MANDAN
   Un agente hambriento no filosofa.
   La biología interrumpe la psicología — siempre.
   El drama nace de esa interrupción.

2. LOS RASGOS NO SE CANCELAN — SE ACTIVAN POR UMBRAL
   Héroe y Sombra coexisten.
   Bajo condiciones normales, el héroe es visible.
   Bajo stress extremo, la Sombra emerge.
   La contradicción interna no es un bug — es el personaje.

3. LAS RELACIONES SON HISTORIA ACUMULADA
   bond_strength no es un número — es una memoria.
   Algunos eventos tienen decay cero (entrelazamiento).
   Otros decaen rápido. El balance es la relación.

4. LO REPRIMIDO EXPLOTA
   Si un arquetipo es consistentemente suprimido por presión social,
   no desaparece — se acumula como complejo latente.
   La explosión es proporcional al tiempo de represión.

5. EL CAMPO RETROALIMENTA — NO SOLO REGISTRA
   El inconsciente colectivo tiene efectos causales.
   Un campo con alta carga de miedo produce agentes más miedosos.
   No es metáfora — es un modificador de probabilidades.

6. EL COLAPSO ES INFORMACIÓN
   Un grupo que muere antes de generar cultura
   es un experimento válido con resultados negativos.
   No es un error — es un dato sobre las condiciones
   mínimas necesarias para que la cultura emerja.

7. LOS MITOS SON AGENTES SIN CUERPO
   Una vez que un mito cristaliza en el campo,
   tiene efectos causales independientes de los agentes que lo generaron.
   El mito actúa. No es decoración.
```

---

*Psyche Simulacra — Lecciones de Simulaciones Exitosas v1.0*
