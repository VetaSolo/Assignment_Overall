from abc import ABC, abstractmethod
import uuid

class AccountFrozenError(Exception):
    pass

class AccountClosedError(Exception):
    pass

class InvalidOperationError(Exception):
    pass

class InsufficientFundsError(Exception):
    pass

class AbstractAccount(ABC):
    def __init__(self, id, owner_data, balance, account_status):
        self.id = id # уникальный идентификатор счёта
        self.owner_data = owner_data # данные владельца
        self._balance = balance # защищённый баланс
        self.account_status = account_status #статус счёта: активный, замороженный, закрытый
# абстрактные методы:
    @abstractmethod
    def deposit(self, amount):
        pass
    @abstractmethod
    def withdraw(self, amount):
        pass
    @abstractmethod
    def get_account_info():
        pass

class BankAccount(AbstractAccount):

    ALLOWED_CURRENCIES = ["RUB", "USD", "EUR", "KZT", "CNY"]

    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    CLOSED = "CLOSED"

    ALLOWED_STATUSES = [
        ACTIVE,
        FROZEN,
        CLOSED
    ]

    def __init__(self, id, owner_data, balance, account_status, currency):

        if id is None:
            id = str(uuid.uuid4())[:8]

        if account_status not in self.ALLOWED_STATUSES:
            raise InvalidOperationError("Неизвестный статус")

        if currency not in self.ALLOWED_CURRENCIES:
            raise InvalidOperationError("Неизвестная валюта")

        if balance < 0:
            raise InvalidOperationError("Баланс не может быть отрицательным")

        super().__init__(
            id,
            owner_data,
            balance,
            account_status
        )

        self.currency = currency



    def deposit(self, amount):
        if self.account_status == BankAccount.FROZEN:
            raise AccountFrozenError("Счет заморожен")
        
        if self.account_status == BankAccount.CLOSED:
            raise AccountClosedError("Счет закрыт")

        if amount <= 0:
            raise InvalidOperationError("Сумма должна быть положительной")
        
        self._balance += amount

    def withdraw(self, amount):
        if self.account_status == BankAccount.FROZEN:
            raise AccountFrozenError("Счет заморожен")
        
        if self.account_status == BankAccount.CLOSED:
            raise AccountClosedError("Счет закрыт")

        if amount <= 0:
            raise InvalidOperationError("Сумма должна быть положительной")

        if amount > self._balance:
            raise InsufficientFundsError("Недостаточно средств")
    
        self._balance -= amount
        
    
    def get_account_info(self):
        return { 
            "id": self.id,
            "balance": self._balance,
            "status": self.account_status,
            "currency": self.currency}
    
    def __str__(self):
        return (
            f"🏦 {type(self).__name__} | "
            f"👤 {self.owner_data} | "
            f"****{self.id[-4:]} | "
            f"📊 {self.account_status} | "
            f"💰 {self._balance} {self.currency}"
        )