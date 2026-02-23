from dataclasses import dataclass, field

@dataclass
class Room:
    id: str
    room_type: str  # 'combat', 'treasure', 'rest', 'merchant', 'boss'
    connections: list[str] = field(default_factory=list)
    cleared: bool = False
    revealed: bool = False

    def reveal(self) -> None:
        self.revealed = True

    def clear(self) -> None:
        self.cleared = True

    def is_accessible(self) -> bool:
        """Returns True if revealed (and inherently connected to a cleared room conceptually)."""
        return self.revealed

