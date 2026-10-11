# Conexión con la Unidad 1: CVaR, dualidad y sensibilidad

## 1. Dos problemas de optimización distintos

El optimizador actual no resuelve un problema diferenciable continuo. En una
observación pública `o`, enumera el conjunto finito de acciones legales
`A(o)`. Para cada acción `a`, un conjunto muestral común `s=1,...,S` produce
beneficios netos de mano `X_s(a)` mediante el motor y una regla fija de
continuación rival. Con pérdidas `ell_s(a)=-X_s(a)`, el objetivo de J1 es

`max { mean_s X_s(a) : a en A(o), CVaR_alpha(ell(a)) <= R }`.

J2 puede enumerar las mismas acciones para minimizar CVaR bajo un beneficio
mínimo. La enumeración da el óptimo exacto **del problema discreto muestral
especificado**, salvo tolerancia de factibilidad; no certifica el valor sobre
todas las cartas, rivales, políticas ni sesiones posibles. Como no se calcula
gradiente ni se relaja la acción discreta, KKT no es una herramienta necesaria
para elegir entre acciones. Tampoco se presume convexidad de la optimización en
probabilidades de acción.

## 2. Subproblema continuo de CVaR

Una vez fijadas las pérdidas `ell_s`, probabilidades `p_s >= 0` con suma uno y
`0 < alpha < 1`, el CVaR de cola superior es el valor de

```text
minimizar   eta + sum_s p_s u_s/(1-alpha)
sujeto a    ell_s - eta - u_s <= 0       para todo s
            -u_s <= 0                    para todo s
            eta libre
```

`eta` es el umbral VaR. Si `p_s>0`, se puede tomar `u_s=max(ell_s-eta,0)` en
una solución óptima; si `p_s=0`, el objetivo no penaliza `u_s`, así que una
solución puede dejar exceso de holgura y aun ser óptima. Los coeficientes son
constantes y las restricciones son afines: este es un
programa lineal, luego convexo. Con una distribución finita válida el primal
es factible (por ejemplo, `eta=max ell`, `u=0`) y tiene valor finito; la
formulación CVaR discreta alcanza un mínimo.

## 3. Lagrangiana y KKT

Sea `c_s=p_s/(1-alpha)`. Con multiplicadores `z_s >= 0` para
`ell_s-eta-u_s <= 0` y `beta_s >= 0` para `-u_s <= 0`, la Lagrangiana es

```text
L = eta + sum_s c_s u_s
    + sum_s z_s (ell_s - eta - u_s) - sum_s beta_s u_s.
```

Las condiciones son

```text
estacionariedad en eta: 1 - sum_s z_s = 0
estacionariedad en u_s: c_s - z_s - beta_s = 0
factibilidad primal:    ell_s - eta - u_s <= 0,  u_s >= 0
factibilidad dual:      z_s >= 0, beta_s >= 0
complementariedad:      z_s (ell_s-eta-u_s)=0, beta_s u_s=0.
```

Una restricción activa puede tener multiplicador cero. Los empates de pérdida
pueden hacer no únicos `eta`, `u`, `z` o `beta`; se verifica la validez de la
solución y sus residuos, no que el solver devuelva un representante particular.

## 4. Dualidad

Al minimizar la Lagrangiana sobre `eta` libre, su coeficiente debe ser cero:
`sum z_s=1`. Al minimizar sobre `u_s>=0`, debe cumplirse
`c_s-z_s>=0`, por lo que `0<=z_s<=p_s/(1-alpha)`. Queda el dual

```text
maximizar   sum_s z_s ell_s
sujeto a    sum_s z_s=1
            0 <= z_s <= p_s/(1-alpha).
```

Es también un LP factible y acotado. La dualidad fuerte de programación lineal
da igualdad entre primal y dual; no necesitamos invocar Slater como si la
enumeración de póker fuera convexa. Los pesos duales asignan masa total uno y
no más de `p_s/(1-alpha)` a cada escenario: priorizan las pérdidas mayores y
fraccionan el átomo de frontera cuando la cola corta una probabilidad.
`z_s` pertenece a **este cálculo de CVaR**. No es automáticamente el
multiplicador ni el precio sombra del límite `R` en el problema de selección de
acciones.

El módulo académico resuelve primal y dual con SciPy `linprog`/HiGHS y recupera
`z=-marginals` de las restricciones `<=` del primal; esta conversión de signo
se verifica con KKT. Calcula tres valores (ordenación habitual, primal y dual),
residuos de estacionariedad, factibilidad, complementariedad y brecha. Se usa
`abs_tol=1e-8`, `rel_tol=1e-8`, con umbral por residuo
`abs_tol+rel_tol*max(1,escala)`. Solo `status=0` para ambos LP y todos los
residuos dentro de sus umbrales producen `validated=true`. SciPy 1.18.1 se fija
en el lockfile; la API y el signo están documentados por
[SciPy `linprog`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linprog.html).

## 5. Ejemplo manual

Para `ell=(100,20,-10)`, `p=(.05,.15,.80)` y `alpha=.90`, la cola tiene masa
`.10`: toma `.05` de la pérdida 100 y `.05` de la pérdida 20. Luego

```text
eta=20, u=(80,0,0)
CVaR = 20 + (.05*80)/.10 = 60
z=(.5,.5,0), beta=(0,1,8)
dual = .5*100 + .5*20 = 60.
```

La masa dual máxima del primer escenario es `.05/.10=.5`; los `.5` restantes
proceden del siguiente escenario. Los CSV conservan además ejemplos con pesos
desiguales, empate, pérdidas negativas y probabilidad nula. Una fuente original
para la representación CVaR con umbral y exceso es Rockafellar y Uryasev (2002),
[manuscrito de los autores](https://sites.math.washington.edu/~rtr/papers/rtr187-CVaR2.pdf).
La presente formulación discreta, certificados y experimentos son desarrollo
del proyecto.

## 6. Aplicación al motor

Para una observación fijada por semilla, se generan 32 escenarios privados de
continuación, comunes a las acciones. Cada lista contiene la pérdida neta de
mano real de cada acción legal, con la regla `stable`; se certifica su CVaR
por los tres métodos. No se confunden beneficio neto de mano, incremento desde
la decisión (que incluye lo ya aportado) ni resultado neto de sesión. Esta
prueba certifica el cálculo de CVaR **para esa distribución muestral dada**;
no certifica que la continuación represente perfectamente al rival ni la
optimalidad global del póker.

## 7. Sensibilidad local del límite de riesgo

Para las pérdidas y medias congeladas de cada acción legal se estudia

`V(R)=max { mean(a) : CVaR(a)<=R }`.

La observación ilustrativa es determinista: reparto de semilla 730001, primera
mano, ciega pequeña, capital 455, estado inicial sin subida rival, cartas
propias fijadas por ese reparto; se toma una única muestra de 128 escenarios,
semilla `unit1-sensitivity-fixed-scenarios-v1`. Se eligió por protocolo antes
de observar el resultado y **no representa la población**. Los umbrales de
factibilidad son CVaR `1`, `10`, `17.3125` y `30` fichas. La región `R<1` no
tiene acción factible; la emergencia se registra aparte y no es un valor de
`V`. En los puntos factibles, el objetivo no decrece al ampliar `R`, como
exige la inclusión de conjuntos factibles. Al añadir acciones factibles, el
valor de una optimización finita es escalonado y la acción ganadora cambia en
los umbrales correspondientes. No hay derivada suave ni se interpreta un
salto como multiplicador KKT del límite en este problema discreto.

Esta monotonía es del problema local con escenarios fijos. No implica que el
beneficio ni el CVaR de una sesión completa sean monótonos en `R`: la política
altera manos futuras, saldos y estados.

## 8. Estabilidad al cambiar el número de escenarios

El experimento compara `S=32,128,512` en ocho estados prefijados: posiciones,
con y sin subida, tres capitales, y repartos con semillas 710001–710008. Son
estratos deliberados para cubrir situaciones, no una muestra aleatoria
representativa. Se cruzan cinco semillas de planificación. Dentro de cada
semilla, 32 y 128 son prefijos de la misma muestra de 512; todas las acciones
comparten los mismos escenarios. Política `risk`, `R=10`, `alpha=.90`,
continuación rival `stable` y reglas constantes. Antes de comparar, las
acciones elegidas se vuelven a evaluar con 2048 escenarios comunes e
independientes de planificación por observación. A alpha .90 la cola equivale
a 204.8 escenarios; se informa error estándar de la media y aproximación del
error estándar de la media de cola, que no sustituye intervalos robustos para
CVaR.

`S=512` es solo referencia de mayor tamaño. Frecuencia de cambio, factibilidad,
emergencias, dispersión de estimaciones y tiempo dependen de estos estados,
semillas, política de continuación y resolución del motor. El coste crece
aproximadamente con S; aumentar S no elimina el error del modelo de rival ni
garantiza convergencia monótona de una acción seleccionada. No se ajustan
parámetros con la muestra independiente de evaluación.

## 9. Relación con apuntes y alcance

La Unidad 1 aporta las herramientas generales de convexidad, Lagrangiana, KKT,
cualificaciones, dualidad y sensibilidad: *M4 – Unit 1, Beamers*, diapositivas
42–66 y 68–71 (perturbaciones y función valor); *M4 – Block 1, Formulaires*,
pp. 1–2; *M4 – Block 1, Lectures*, pp. 7–18 (desigualdades, dualidad, CQs y
convexidad); y *M4 – Unit 1, Exercises*, pp. 10–19 (desigualdades, primal-dual
y problemas mixtos). Estos PDF locales se consultaron pero no se publican en
este repositorio. CVaR y su LP se incorporan como ampliación de riesgo, no se
atribuyen a una derivación literal de esos apuntes.

Se corrigen dos afirmaciones demasiado fuertes de las fuentes: *Lectures*, p. 8,
presenta `g_i(x)=0 => lambda_i>0`, aunque complementariedad solo permite afirmar
`lambda_i>0 => g_i(x)=0`; una restricción activa puede tener multiplicador cero.
Además, *Formulaires*, p. 3, atribuye unicidad a convexidad sola, y *Lectures*,
p. 18, afirma unicidad a partir de convexidad del conjunto: convexidad permite
concluir que todo mínimo local es global, pero no lo hace único. Hace falta una
hipótesis más fuerte, como convexidad estricta del objetivo para minimizar.

Las diapositivas 68–71 conectan valor óptimo y perturbaciones bajo regularidad,
y advierten de cambios del conjunto activo y falta de diferenciabilidad. Aquí la
curva local es escalonada por la finitud de acciones: la semejanza es conceptual,
no autoriza a usar la fórmula de envolvente. Además, la fórmula del apunte para
una minimización usa su convención de signos; no se traslada sin cambio a la
maximización `V(R)`.

## 10. Reproducir

Desde la raíz, con el entorno virtual activado:

```bash
python -m poker.academic cvar --out results/unit1/cvar
python -m poker.academic sensitivity --out results/unit1/sensitivity --scenarios 128
python -m poker.academic stability --out results/unit1/stability-pilot --observations 1 --planner-seeds 1 --evaluation-scenarios 256
python -m poker.academic stability --out results/unit1/stability --observations 8 --planner-seeds 5 --evaluation-scenarios 2048
python -m pytest -q
```

La tanda final conserva `observations.json`, manifiesto, resultados por decisión,
evaluación independiente, tablas CSV y figuras. No reemplaza ni altera las
3000 sesiones históricas de `results/study/`.
