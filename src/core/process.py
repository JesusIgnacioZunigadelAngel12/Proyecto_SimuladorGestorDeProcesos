"""
Módulo: process.py — Bloque de Control de Proceso (PCB)

Define la estructura de datos que representa un proceso en el SO,
incluyendo sus estados, atributos y validación de transiciones.
"""

import random
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import ClassVar

class ProcessState(Enum):
    """Estados del ciclo de vida de un proceso."""
    NEW = auto()
    READY = auto()
    RUNNING = auto()
    WAITING = auto()
    TERMINATED = auto()

class ExitReason(Enum):
    """Motivo de terminación del proceso."""
    NORMAL = auto()
    ERROR = auto()
    DEADLOCK = auto()

# Matriz estricta de control de transiciones de estados de procesos (FSM)
VALID_TRANSITIONS: dict[ProcessState, frozenset[ProcessState]] = {
    ProcessState.NEW: frozenset({ProcessState.READY}),
    ProcessState.READY: frozenset({ProcessState.RUNNING}),
    ProcessState.RUNNING: frozenset({
        ProcessState.READY,
        ProcessState.WAITING,
        ProcessState.TERMINATED,
    }),
    ProcessState.WAITING: frozenset({ProcessState.READY}),
    ProcessState.TERMINATED: frozenset(),
}

# Parámetros por defecto para la generación automática en Modo Batch
BURST_MIN: int = 3
BURST_MAX: int = 15
MEM_MIN: int = 64
MEM_MAX: int = 512
ARRIVAL_MIN: int = 0
ARRIVAL_MAX: int = 20

@dataclass
class PCB:
    """Bloque de Control de Proceso (Process Control Block)."""

    # Contador estático de la clase para autogenerar PIDs
    _next_pid: ClassVar[int] = 1

    name: str = "Proceso"
    cpu_burst: int = -1
    mem_mb: int = -1
    arrival_time: int = -1

    pid: int = field(init=False)
    state: ProcessState = field(init=False, default=ProcessState.NEW)
    time_remaining: int = field(init=False)
    io_wait_time: int = field(init=False, default=0)
    exit_reason: ExitReason | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        # Asignación atómica de PID
        self.pid = PCB._next_pid
        PCB._next_pid += 1

        # Generación aleatoria en modo batch si no se proveen valores base
        if self.cpu_burst == -1:
            self.cpu_burst = random.randint(BURST_MIN, BURST_MAX)
        if self.mem_mb == -1:
            self.mem_mb = random.randint(MEM_MIN, MEM_MAX)
        if self.arrival_time == -1:
            self.arrival_time = random.randint(ARRIVAL_MIN, ARRIVAL_MAX)

        # Validaciones de integridad estructural
        if self.cpu_burst < 1:
            raise ValueError(f"cpu_burst debe ser >= 1, recibido: {self.cpu_burst}.")
        if self.mem_mb < 1:
            raise ValueError(f"mem_mb debe ser >= 1, recibido: {self.mem_mb}.")
        if self.arrival_time < 0:
            raise ValueError(f"arrival_time debe ser >= 0, recibido: {self.arrival_time}.")

        # Inicializa contador de vida al máximo teórico
        self.time_remaining = self.cpu_burst

    def transition(self, new_state: ProcessState) -> None:
        """Cambia el estado del proceso validando las transiciones legales."""
        allowed: frozenset[ProcessState] = VALID_TRANSITIONS.get(self.state, frozenset())

        # Valida contra la Máquina de Estados Finitos para prevenir errores de kernel
        if new_state not in allowed:
            raise ValueError(
                f"Transicion INVALIDA: {self.state.name} -> {new_state.name} "
                f"para PID={self.pid}."
            )
        self.state = new_state

    def __str__(self) -> str:
        """Representación en texto del estado del PCB."""
        # Formateos opcionales dependientes del estado
        exit_info: str = f" | Razón: {self.exit_reason.name}" if self.exit_reason else ""
        io_info: str = f" | I/O: {self.io_wait_time} ticks" if self.state == ProcessState.WAITING and self.io_wait_time > 0 else ""

        return (
            f"[PID {self.pid:>3}] {self.name:<15} | "
            f"Estado: {self.state.name:<10} | "
            f"CPU: {self.time_remaining}/{self.cpu_burst} ticks | "
            f"RAM: {self.mem_mb} MB | "
            f"Llegada: t={self.arrival_time}{io_info}{exit_info}"
        )

    @classmethod
    def reset_pid_counter(cls) -> None:
        """Reinicia el generador de PIDs para nuevos lotes."""
        cls._next_pid = 1
