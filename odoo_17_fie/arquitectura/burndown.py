# Burndown Chart (trabajo restante acumulado vs. línea ideal)
# Matplotlib puro, sin estilos/colores específicos

import matplotlib.pyplot as plt

# -----------------------------
# 1) Datos (6 sprints reales)
# -----------------------------
sprints = ["Sprint 1", "Sprint 2", "Sprint 3", "Sprint 4", "Sprint 5", "Sprint 6"]
estimado = [35, 30, 25, 18, 10, 30]
real     = [32, 34, 23, 18,  9, 35]

# --------------------------------------------
# 2) Cálculo del burndown (acumulado restante)
# --------------------------------------------
total = sum(estimado)              # 148 h
n = len(sprints)                   # 6 sprints

# Etiquetas con punto de inicio (Sprint 0 / Inicio)
x_labels = ["Inicio"] + sprints

# Línea ideal: total -> 0 en n pasos (n+1 puntos: 0..n)
step = total / n
ideal = [max(total - i*step, 0) for i in range(n + 1)]

# Restante real: total menos acumulado real tras cada sprint (n+1 puntos, con inicio)
restante_real = [total]
acum = 0
for r in real:
    acum += r
    restante_real.append(max(total - acum, 0))  # no bajar de 0

# --------------------------------------------
# 3) Gráfico: restante real vs. línea ideal
# --------------------------------------------
plt.figure(figsize=(9, 5))
plt.plot(x_labels, restante_real, marker="o", label="Línea real (ejecutada)")
plt.plot(x_labels, ideal, marker="o", linestyle=":", label="Línea ideal (planificada)")

plt.title("Burndown Chart del proyecto EduCV – Esfuerzo restante por sprint")
plt.xlabel("Iteración (Sprint)")
plt.ylabel("Esfuerzo restante acumulado (horas)")
plt.ylim(0, total)                 # escala estándar: 0 → total planificado
plt.grid(True, linestyle=":", alpha=0.6)
plt.legend(loc="best")
plt.tight_layout()

# Guardar (opcional)
# plt.savefig("burndown_tesis.png", dpi=300)

plt.show()
