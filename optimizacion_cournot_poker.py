import numpy as np
import matplotlib.pyplot as plt
 
# ----------------------------------------------------
# PARAMETROS DEL TRABAJO
# ----------------------------------------------------
 
LIMITE_CVAR_J1 = 50
BENEFICIO_MINIMO_J2 = 5
 
# ----------------------------------------------------
# MEJOR RESPUESTA JUGADOR 1
# max mu1
# s.a. R1 <= L
# ----------------------------------------------------
 
def mejor_respuesta_j1(mu1, R1, capacidad1, q2):
mejor_q1 = None
mejor_valor = -1e100
 
for q1 in np.linspace(0, capacidad1, 300):
 
if R1(q1, q2) > LIMITE_CVAR_J1:
continue
 
valor = mu1(q1, q2)
 
if valor > mejor_valor:
mejor_valor = valor
mejor_q1 = q1
 
return mejor_q1, mejor_valor
 
 
# ----------------------------------------------------
# MEJOR RESPUESTA JUGADOR 2
# min R2
# s.a. mu2 >= beneficio minimo
# ----------------------------------------------------
 
def mejor_respuesta_j2(mu2, R2, capacidad2, q1):
mejor_q2 = None
mejor_riesgo = 1e100
 
for q2 in np.linspace(0, capacidad2, 300):
 
if mu2(q1, q2) < BENEFICIO_MINIMO_J2:
continue
 
riesgo = R2(q1, q2)
 
if riesgo < mejor_riesgo:
mejor_riesgo = riesgo
mejor_q2 = q2
 
return mejor_q2, mejor_riesgo
 
 
# ----------------------------------------------------
# CURVAS DE MEJORES RESPUESTAS
# ----------------------------------------------------
 
def calcular_curvas_br(
mu1,
mu2,
R1,
R2,
capacidad1,
capacidad2):
 
puntos_br1 = []
puntos_br2 = []
 
malla1 = np.linspace(0, capacidad2, 100)
 
for q2 in malla1:
 
br, _ = mejor_respuesta_j1(
mu1,
R1,
capacidad1,
q2
)
 
puntos_br1.append(br)
 
malla2 = np.linspace(0, capacidad1, 100)
 
for q1 in malla2:
 
br, _ = mejor_respuesta_j2(
mu2,
R2,
capacidad2,
q1
)
 
puntos_br2.append(br)
 
return malla1, puntos_br1, malla2, puntos_br2
 
 
# ----------------------------------------------------
# EQUILIBRIO APROXIMADO
# ----------------------------------------------------
 
def equilibrio_nash(
mu1,
mu2,
R1,
R2,
capacidad1,
capacidad2):
 
mejor_error = 1e100
 
equilibrio = None
 
for q1 in np.linspace(0, capacidad1, 100):
 
br2, _ = mejor_respuesta_j2(
mu2,
R2,
capacidad2,
q1
)
 
if br2 is None:
continue
 
br1, _ = mejor_respuesta_j1(
mu1,
R1,
capacidad1,
br2
)
 
if br1 is None:
continue
 
error = abs(q1 - br1)
 
if error < mejor_error:
 
mejor_error = error
 
equilibrio = (
q1,
br2,
mu1(q1, br2),
mu2(q1, br2),
R1(q1, br2),
R2(q1, br2)
)
 
return equilibrio
 
 
# ----------------------------------------------------
# RESTRICCIONES ACTIVAS
# ----------------------------------------------------
 
def restricciones_activas(
mu1,
mu2,
R1,
R2,
capacidad1,
capacidad2):
 
activas = []
 
for q1 in np.linspace(0, capacidad1, 50):
 
for q2 in np.linspace(0, capacidad2, 50):
 
riesgo1 = R1(q1, q2)
beneficio2 = mu2(q1, q2)
 
if abs(riesgo1 - LIMITE_CVAR_J1) < 0.5:
 
activas.append(
(
q1,
q2,
"CVaR jugador 1 activo"
)
)
 
if abs(beneficio2 - BENEFICIO_MINIMO_J2) < 0.5:
 
activas.append(
(
q1,
q2,
"Beneficio minimo jugador 2 activo"
)
)
 
return activas
 
 
# ----------------------------------------------------
# CASOS INVIABLES
# ----------------------------------------------------
 
def buscar_inviabilidad(
mu1,
mu2,
R1,
R2,
capacidad1,
capacidad2):
 
inviables = []
 
for q1 in np.linspace(0, capacidad1, 40):
 
existe = False
 
for q2 in np.linspace(0, capacidad2, 40):
 
cumple = (
mu2(q1, q2)
>= BENEFICIO_MINIMO_J2
)
 
if cumple:
existe = True
break
 
if not existe:
 
inviables.append(q1)
 
return inviables
 
 
# ----------------------------------------------------
# COMPARACION CON COURNOT CLASICO
# ----------------------------------------------------
 
def br1_cournot(q2, a=100, b=1, c=10):
 
return max(
0,
(a - c - b*q2)/(2*b)
)
 
 
def br2_cournot(q1, a=100, b=1, c=10):
 
return max(
0,
(a - c - b*q1)/(2*b)
)
 
 
# ----------------------------------------------------
# GRAFICAS
# ----------------------------------------------------
 
def graficar_br(
x1,
br1,
x2,
br2):
 
plt.figure(figsize=(8, 6))
 
plt.plot(
x1,
br1,
linewidth=2,
label="BR1(q2)"
)
 
plt.plot(
x2,
br2,
linewidth=2,
label="BR2(q1)"
)
 
plt.xlabel("Decision del rival")
plt.ylabel("Mejor respuesta")
 
plt.title(
"Curvas de mejores respuestas"
)
 
plt.grid(True)
plt.legend()
 
plt.savefig(
"curvas_mejores_respuestas.png",
dpi=300
)
 
plt.show()
 
 
# ----------------------------------------------------
# INFORME AUTOMATICO
# ----------------------------------------------------
 
def generar_resumen(
equilibrio,
activas,
inviables):
 
print("\n")
print("=" * 60)
print("RESULTADOS DEL MODELO")
print("=" * 60)
 
if equilibrio:
 
q1, q2, mu1v, mu2v, r1, r2 = equilibrio
 
print("\nEquilibrio aproximado")
 
print(f"q1* = {q1:.3f}")
print(f"q2* = {q2:.3f}")
 
print(f"Beneficio esperado J1 = {mu1v:.3f}")
print(f"Beneficio esperado J2 = {mu2v:.3f}")
 
print(f"CVaR J1 = {r1:.3f}")
print(f"CVaR J2 = {r2:.3f}")
 
print("\nRestricciones activas detectadas")
 
for r in activas[:20]:
print(r)
 
print(
f"\nNumero de restricciones activas: "
f"{len(activas)}"
)
 
print(
f"\nCasos inviables encontrados: "
f"{len(inviables)}"
)
