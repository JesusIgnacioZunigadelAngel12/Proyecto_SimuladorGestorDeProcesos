"""
Módulo: resource.py — Pool de Recursos del Sistema

Gestiona la asignación y liberación de recursos (CPU, RAM).
"""

class ResourcePool:
    """Pool de recursos del sistema simulado."""

    def __init__(self, cpu_cores: int = 1, ram_mb: int = 4096) -> None:
        if cpu_cores < 1:
            raise ValueError(f"cpu_cores debe ser >= 1, recibido: {cpu_cores}.")
        if ram_mb < 1:
            raise ValueError(f"ram_mb debe ser >= 1, recibido: {ram_mb}.")

        # Totales físicos del sistema
        self.total_cpu: int = cpu_cores
        self.total_ram: int = ram_mb

        # Recursos disponibles en tiempo real
        self.available_cpu: int = cpu_cores
        self.available_ram: int = ram_mb

    def request(self, cpu: int, ram: int) -> bool:
        """Intenta asignar recursos a un proceso."""
        if cpu < 0 or ram < 0:
            raise ValueError(f"Recursos negativos no permitidos: cpu={cpu}, ram={ram}.")

        # Verifica que la petición no exceda la capacidad máxima instalada
        if cpu > self.total_cpu or ram > self.total_ram:
            return False

        # Verifica si hay disponibilidad actual
        if cpu > self.available_cpu or ram > self.available_ram:
            return False

        # Consume los recursos de forma atómica
        self.available_cpu -= cpu
        self.available_ram -= ram
        return True

    def release(self, cpu: int, ram: int) -> bool:
        """Devuelve recursos al pool."""
        if cpu < 0 or ram < 0:
            raise ValueError(f"Recursos negativos no permitidos: cpu={cpu}, ram={ram}.")

        # Previene "double-free" validando que no se supere el total original
        if self.available_cpu + cpu > self.total_cpu:
            return False
        if self.available_ram + ram > self.total_ram:
            return False

        # Libera recursos restaurando el contador
        self.available_cpu += cpu
        self.available_ram += ram
        return True

    def __str__(self) -> str:
        # Calcula el uso actual para el reporte visual
        cpu_used: int = self.total_cpu - self.available_cpu
        ram_used: int = self.total_ram - self.available_ram

        return (
            f"+======================================+\n"
            f"|        RECURSOS DEL SISTEMA          |\n"
            f"+======================================+\n"
            f"|  CPU: {cpu_used}/{self.total_cpu} nucleos en uso{' ' * (13 - len(f'{cpu_used}/{self.total_cpu}'))}|\n"
            f"|  RAM: {ram_used}/{self.total_ram} MB en uso{' ' * (15 - len(f'{ram_used}/{self.total_ram}'))}|\n"
            f"+======================================+"
        )
