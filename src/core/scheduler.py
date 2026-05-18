"""
Módulo: scheduler.py — Planificador de Procesos (CPU Scheduler)

Simula un planificador que decide la ejecución de procesos (FCFS, SJF)
en un modelo determinista por ticks, con soporte para llegadas dinámicas
y ráfagas de I/O estocásticas (Modo Batch).
"""
from __future__ import annotations

import random
from collections import deque
from enum import Enum, auto

from src.core.process import PCB, ProcessState, ExitReason
from src.core.resource import ResourcePool
from src.ui.logger import Logger

# Constantes de simulación I/O estocástica
IO_PROBABILITY: float = 0.10
IO_WAIT_MIN: int = 2
IO_WAIT_MAX: int = 5

class SchedulingAlgorithm(Enum):
    """Algoritmos de planificación soportados."""
    FCFS = auto()
    SJF = auto()

class Scheduler:
    """Planificador de procesos del SO simulado."""

    def __init__(
        self,
        resources: ResourcePool,
        logger: Logger,
        algorithm: SchedulingAlgorithm = SchedulingAlgorithm.FCFS,
    ) -> None:
        # Colas principales del planificador
        self.ready_queue: deque[PCB] = deque()
        self.waiting_queue: list[PCB] = []
        self.all_processes: list[PCB] = []
        
        # Referencias a módulos de hardware virtual
        self.resources: ResourcePool = resources
        self.algorithm: SchedulingAlgorithm = algorithm
        self.current_process: PCB | None = None
        self.clock: int = 0
        self.logger: Logger = logger

    def register_process(self, pcb: PCB) -> None:
        """Añade un proceso en estado NEW a la lista general del sistema."""
        self.all_processes.append(pcb)
        self.logger.log(
            f"REGISTRADO: PID {pcb.pid} ({pcb.name}) | "
            f"Burst={pcb.cpu_burst} | RAM={pcb.mem_mb}MB | "
            f"Llegada=t{pcb.arrival_time}",
            self.clock,
        )

    def admit_process(self, pcb: PCB) -> bool:
        """Transfiere un proceso de NEW a READY si hay RAM suficiente."""
        # Validación de integridad de estado inicial
        if pcb.state != ProcessState.NEW:
            self.logger.log(f"ERROR: PID {pcb.pid} no esta en NEW ({pcb.state.name}).", self.clock)
            return False

        # Verifica y reserva RAM al admitir el proceso
        if not self.resources.request(cpu=0, ram=pcb.mem_mb):
            self.logger.log(
                f"RECHAZADO: PID {pcb.pid} ({pcb.name}) necesita "
                f"{pcb.mem_mb} MB, disponible: {self.resources.available_ram} MB.",
                self.clock,
            )
            return False

        # Inicia ciclo de vida en memoria
        pcb.transition(ProcessState.READY)
        self.ready_queue.append(pcb)

        self.logger.log(
            f"ADMITIDO: PID {pcb.pid} ({pcb.name}) -> READY | "
            f"Burst={pcb.cpu_burst} | RAM={pcb.mem_mb}MB",
            self.clock,
        )
        return True

    def _handle_arrivals(self) -> None:
        """Admite procesos cuyo arrival_time <= clock."""
        # Filtra procesos que acaban de llegar en el clock actual
        pending = [
            p for p in self.all_processes
            if p.state == ProcessState.NEW and p.arrival_time <= self.clock
        ]
        # Ordena para determinismo ante colisiones
        pending.sort(key=lambda p: p.arrival_time)
        for pcb in pending:
            self.admit_process(pcb)

    def _handle_waiting(self) -> None:
        """Decrementa tiempo de espera I/O y transfiere procesos a READY si terminan."""
        completed_io = []
        for pcb in self.waiting_queue:
            pcb.io_wait_time -= 1
            if pcb.io_wait_time <= 0:
                completed_io.append(pcb)

        # Retorna a cola READY los procesos que finalizaron operaciones I/O
        for pcb in completed_io:
            self.waiting_queue.remove(pcb)
            pcb.transition(ProcessState.READY)
            self.ready_queue.append(pcb)
            self.logger.log(f"I/O COMPLETO: PID {pcb.pid} ({pcb.name}) -> READY", self.clock)

    def _select_next(self) -> PCB | None:
        """Selecciona el próximo proceso de la cola de listos según el algoritmo."""
        if not self.ready_queue:
            return None

        # Despachador principal según algoritmo configurado
        if self.algorithm == SchedulingAlgorithm.FCFS:
            return self.ready_queue.popleft()
        elif self.algorithm == SchedulingAlgorithm.SJF:
            # Encuentra el trabajo más corto (SJF no apropiativo)
            shortest = min(self.ready_queue, key=lambda p: p.time_remaining)
            self.ready_queue.remove(shortest)
            return shortest

        return self.ready_queue.popleft()

    def _execute_tick(self, pcb: PCB) -> bool:
        """
        Avanza la ejecución del proceso actual en un tick.
        Simula solicitudes aleatorias de I/O (paso a WAITING).
        """
        # Decrementa ejecución
        pcb.time_remaining -= 1
        self.logger.log(
            f"TICK: PID {pcb.pid} ({pcb.name}) | "
            f"Restante: {pcb.time_remaining}/{pcb.cpu_burst}",
            self.clock,
        )

        # Lógica de interrupción estocástica por solicitud de recurso I/O
        if pcb.time_remaining > 0 and random.random() < IO_PROBABILITY:
            io_ticks: int = random.randint(IO_WAIT_MIN, IO_WAIT_MAX)
            pcb.io_wait_time = io_ticks
            pcb.transition(ProcessState.WAITING)
            
            # Libera solo la CPU, mantiene la RAM asignada al proceso
            self.resources.release(cpu=1, ram=0)
            self.waiting_queue.append(pcb)
            self.current_process = None

            self.logger.log(
                f"I/O REQUEST: PID {pcb.pid} ({pcb.name}) -> WAITING ({io_ticks} ticks)",
                self.clock,
            )
            return True
        return False

    def execute_cycle(self) -> str:
        """Ejecuta un ciclo completo (un tick) del planificador."""
        # Avanza el reloj principal y procesa eventos pasivos (llegadas e I/O)
        self.clock += 1
        self._handle_arrivals()
        self._handle_waiting()

        # Context Switch si hay disponibilidad de CPU
        if self.current_process is None:
            next_pcb = self._select_next()
            if next_pcb is None:
                self.logger.log("IDLE: Cola vacia, CPU ociosa.", self.clock)
                return f"[Tick {self.clock}] CPU ociosa -- cola vacia."

            # Reintenta si hay condición de carrera con CPU
            if not self.resources.request(cpu=1, ram=0):
                self.ready_queue.appendleft(next_pcb)
                return f"[Tick {self.clock}] No hay CPU disponible."

            next_pcb.transition(ProcessState.RUNNING)
            self.current_process = next_pcb
            self.logger.log(
                f"DISPATCH: PID {next_pcb.pid} ({next_pcb.name}) -> RUNNING "
                f"[{self.algorithm.name}]",
                self.clock,
            )

        assert self.current_process is not None
        # Ejecución del tick actual sobre el proceso en CPU
        io_requested = self._execute_tick(self.current_process)

        if io_requested:
            return f"[Tick {self.clock}] Proceso solicito I/O -> WAITING."

        # Cierre y limpieza si el proceso terminó su Burst
        if self.current_process.time_remaining <= 0:
            finished = self.current_process
            finished.transition(ProcessState.TERMINATED)
            finished.exit_reason = ExitReason.NORMAL
            
            # Liberación total de recursos (CPU y RAM)
            self.resources.release(cpu=1, ram=finished.mem_mb)
            self.logger.log(
                f"TERMINADO: PID {finished.pid} ({finished.name}) completo.",
                self.clock,
            )
            self.current_process = None
            return f"[Tick {self.clock}] PID {finished.pid} TERMINADO."

        return f"[Tick {self.clock}] PID {self.current_process.pid} ejecutando."

    def is_simulation_complete(self) -> bool:
        """Retorna True si todos los procesos han terminado."""
        if not self.all_processes:
            return True
        # Verifica clausura comprobando estado terminal de toda la lista
        return all(p.state == ProcessState.TERMINATED for p in self.all_processes)

    def set_algorithm(self, algorithm: SchedulingAlgorithm) -> None:
        """Cambia el algoritmo de planificación en uso."""
        self.algorithm = algorithm
        self.logger.log(f"ALGORITMO: {algorithm.name}", self.clock)
