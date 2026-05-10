# Simulador Gestor de Procesos

Un simulador híbrido de Sistema Operativo enfocado en la gestión de procesos, algoritmos de planificación y comunicación entre procesos (IPC).

## Estructura del Proyecto

```text
simulador-gestor-procesos/
├── README.md
├── .gitignore
├── LICENSE
├── main.py                    # Interfaz gráfica principal (GUI - tkinter)
├── src/
│   ├── core/                  # Núcleo del sistema operativo simulado
│   │   ├── process.py         # PCB, estados (5-state model), PID
│   │   ├── scheduler.py       # Algoritmos FCFS y SJF
│   │   └── resource.py        # Gestión de CPU y memoria (ResourcePool)
│   ├── ipc/                   # Comunicación entre procesos (IPC)
│   │   └── producer_consumer.py  # Productor-Consumidor con hilos y semáforos
│   └── ui/                    # Interfaz y registros auxiliares
│       └── logger.py          # Sistema de logs con timestamps
├── tests/                     # Tests unitarios
├── examples/                  # Scripts de demostración
├── docs/                      # Documentación y diagramas
├── capturas/                  # Capturas de pantalla de la interfaz
├── benches/                   # Pruebas de rendimiento
└── .github/                   # Configuración para integración continua (CI)
```

## Requisitos

- Python 3.x
- `tkinter` (usualmente incluido en la instalación estándar de Python).

## Ejecución

Para iniciar la interfaz gráfica del simulador:

```bash
py main.py
```

## Características

- **Creación de procesos**: Nombre, ráfaga de CPU y memoria RAM configurables.
- **Algoritmos de planificación**: FCFS (First Come First Served) y SJF (Shortest Job First).
- **Gestión de estados**: Modelo de 5 estados (NEW, READY, RUNNING, WAITING, TERMINATED).
- **Operaciones sobre procesos**: Suspensión, reanudación y terminación forzada (Kill).
- **IPC**: Demostración del problema Productor-Consumidor con hilos reales y semáforos.
- **Monitoreo en tiempo real**: CPU, RAM, colas de procesos y registro de logs.
