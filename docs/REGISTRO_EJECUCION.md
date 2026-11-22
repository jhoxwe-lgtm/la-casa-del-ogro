# Registro de ejecución — Ejercicio 4

**Proyecto:** La Casa del Ogro. **Equipo:** José Molina, Ana Murillo y Felipe Cáceres.  
**Rama de mejora:** `quality/ejercicio4-auditoria`.

## 1. Línea base v3 (histórica)
| Campo | Valor |
|---|---|
| Commit | `30890233b278dd1181255e30773551889012950f` |
| Entorno | Linux x86_64; Python 3.13.5; Pytest 9.0.2 |
| Total/ejecutados/aprobados | 58/58/58 |
| Fallidos/bloqueados | 0/0 |
| Duración | 9,91 s |

Esta línea base no corresponde a v4.

## 2. Historial de ejecución v4

| Ejecución | Commit probado | Total | Aprobados | Fallidos | Bloqueados | Duración | Estado |
|---|---|---:|---:|---:|---:|---:|---|
| GitHub Actions run #1 | `206b09a9b7c3fce8887ce6e23b96a5d158358fda` | 62 | 61 | 1 | 0 | 7,88 s | Falló CP-RF-04-01; el caso no mantenía una segunda habitación ocupada durante la comprobación simultánea. |
| GitHub Actions run #4 | `5cd414356550f4e5f3bbd52c5c1600900a3daea6` | 62 | 62 | 0 | 0 | 12,60 s | Aprobado después de corregir RF-04. |

**Ejecución aprobada:** [GitHub Actions run #4](https://github.com/jhoxwe-lgtm/la-casa-del-ogro/actions/runs/45051510264).  
**Evidencia completa registrada:** [`evidence/pytest_results_v4.txt`](../evidence/pytest_results_v4.txt).  
**Artefacto generado por CI:** [pytest-results.zip](https://github.com/jhoxwe-lgtm/la-casa-del-ogro/actions/runs/45051510264/artifacts/14765257623).

## 3. Cobertura de caja blanca
La cobertura fue medida sobre la regla aislada `casa_ogro.rules`, no sobre toda la aplicación.

| Módulo | Sentencias | No ejecutadas | Ramas | Parciales | Cobertura |
|---|---:|---:|---:|---:|---:|
| `casa_ogro/rules.py` | 6 | 0 | 4 | 0 | 100 % |

## 4. Resumen automatizado vigente
| Métrica | Resultado |
|---|---:|
| Casos planificados | 62 |
| Casos ejecutados | 62 |
| Aprobados | 62 |
| Fallidos | 0 |
| Bloqueados | 0 |
| Porcentaje de aprobación automatizada | 100 % |

Este porcentaje corresponde únicamente a la suite automatizada de la rama v4. No implica que todos los RNF estén validados.

## 5. Pruebas manuales del navegador

| ID | Fecha | Commit de código | Entorno/navegador | Estado | Evidencia |
|---|---|---|---|---|---|
| CP-SYS-RESERVA-01 | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| CP-SYS-AFORO-01 | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| CP-SYS-RNF01-01 | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| CP-SYS-RNF02-01 | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| CP-SYS-RNF03-01 | Pendiente | Pendiente | Pendiente | Bloqueado: período mensual no completado | Pendiente |
| CP-SYS-RNF04-01 | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| CP-SYS-RNF05-01 | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |

## 6. Interpretación por requisito
- **Validado:** caso ejecutado y evidencia cumple.
- **Parcial:** se verificó parte del comportamiento, pero falta métrica o entorno.
- **No validado:** no fue ejecutado o no cumple.
- **Bloqueado:** no pudo ejecutarse y la causa quedó registrada.

RNF-03 no se valida hasta medir disponibilidad mensual del 99 %. RNF-04 requiere medir interacciones reales. RNF-02 y RNF-05 requieren repetición en el equipo/entorno de presentación. Los recorridos de navegador siguen pendientes y no se incluyen en el total de 62 pruebas automatizadas.
