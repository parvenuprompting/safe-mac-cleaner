from dataclasses import dataclass

SCAN_PROFILES = {
    "Aangepaste scan": {},
    "Grote bestanden": {"size": 1000, "age": 0},
    "Oude bestanden": {"size": 100, "age": 180},
    "Oude downloads": {"size": 100, "age": 30},
}


@dataclass(frozen=True)
class ScanSettings:
    top_n: int
    age: int
    size: int
    mode: str

    @classmethod
    def from_values(cls, top_n, age, size, mode):
        return cls(
            top_n=max(1, min(int(top_n), 10000)),
            age=max(0, min(int(age), 36500)),
            size=max(0, min(int(size), 1000000)),
            mode=mode if mode in {"last_used", "last_modified"} else "last_used",
        )

    @classmethod
    def defaults(cls):
        return cls(top_n=100, age=30, size=100, mode="last_used")

    def as_dict(self):
        return {"top_n": self.top_n, "age": self.age, "size": self.size, "mode": self.mode}

    def with_profile(self, profile):
        values = self.as_dict()
        values.update(SCAN_PROFILES.get(profile, {}))
        return ScanSettings.from_values(**values)
