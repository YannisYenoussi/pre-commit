import os

from dotenv import load_dotenv

load_dotenv()

OPERATIONS = ("add", "subtract", "multiply", "divide")


def get_password() -> str:
    """Lit le secret depuis l'environnement, sans jamais l'afficher."""
    password = os.getenv("APP_PASSWORD")
    if not password:
        raise RuntimeError("APP_PASSWORD n'est pas configuré")
    return password


def calculate(a: float, b: float, operation: str) -> float:
    """Calcule une opération explicitement autorisée (remplace eval())."""
    if operation == "add":
        return a + b
    if operation == "subtract":
        return a - b
    if operation == "multiply":
        return a * b
    if operation == "divide":
        if b == 0:
            raise ValueError("Division par zéro")
        return a / b
    raise ValueError("Opération non autorisée")


def get_message() -> str:
    try:
        a = float(input("Premier nombre : "))
        b = float(input("Second nombre : "))
    except ValueError as exc:
        raise ValueError("Saisie numérique invalide") from exc
    operation = input(f"Opération {OPERATIONS} : ").strip()
    return f"Résultat : {calculate(a, b, operation)}"


if __name__ == "__main__":
    print(get_message())
