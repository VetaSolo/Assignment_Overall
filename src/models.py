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



class SavingsAccount(BankAccount):

    def __init__(self, id, owner_data, balance, account_status, currency, min_balance, monthly_return):

        if monthly_return <= 0:
            raise InvalidOperationError("Месячная ставка должна быть положительной")
        

        super().__init__(
                id,
                owner_data,
                balance,
                account_status,
                currency
            )
    
        self.min_balance = min_balance # минимальный остаток
        self.monthly_return = monthly_return # месячная ставка доходности

    def apply_monthly_interest(self):
        self._balance += self._balance * (self.monthly_return / 100) 

    def withdraw(self, amount):
        super().withdraw(amount)
        if self._balance - amount < self.min_balance:
            raise InvalidOperationError("Нельзя опуститься ниже минимального остатка")
        

    def get_account_info(self):
        return { 
            "id": self.id,
            "balance": self._balance,
            "status": self.account_status,
            "currency": self.currency,
            "monthly return": self.monthly_return,
            "min balance":self.min_balance
            }
    
    def __str__(self):
        return (
            f"🏦 {type(self).__name__} | "
            f"👤 {self.owner_data} | "
            f"****{self.id[-4:]} | "
            f"📊 {self.account_status} | "
            f"💰 {self._balance} {self.currency}| "
            f"🔒 {self.monthly_return}| "
            f"📈 {self.min_balance}"
        )

class PremiumAccount(BankAccount):
    def __init__(self, id, owner_data, balance, account_status, currency, withdraw_limit, overdraft_limit, commission):

        if withdraw_limit <= 0:
            raise InvalidOperationError("Лимит на снятие должен быть положительным")
        if overdraft_limit < 0:
            raise InvalidOperationError("Овердрафт не может быть отрицательным")
        if commission < 0:
            raise InvalidOperationError("Комиссия не может быть отрицательной")

        super().__init__(
                        id,
                        owner_data,
                        balance,
                        account_status,
                        currency
                    )


        self.withdraw_limit = withdraw_limit
        self.overdraft_limit = overdraft_limit
        self.commission = commission

    def withdraw(self, amount):
        if amount > self.withdraw_limit:
            raise InvalidOperationError("Превышен лимит на снятие")
        
        if self._balance - amount < -self.overdraft_limit:
            raise InsufficientFundsError("Недостаточно средств с учетом овердрафта")

        amount += self.commission

        self._balance -= amount

    def get_account_info(self):
        return { 
            "id": self.id,
            "balance": self._balance,
            "status": self.account_status,
            "currency": self.currency,
            "withdraw limit": self.withdraw_limit,
            "overdraft limit":self.overdraft_limit,
            "commission":self.commission
            }

    def __str__(self):
        return (
            f"🏦 {type(self).__name__} | "
            f"👤 {self.owner_data} | "
            f"****{self.id[-4:]} | "
            f"📊 {self.account_status} | "
            f"💰 {self._balance} {self.currency}| "
            f"🔒 {self.withdraw_limit}| "
            f"📈 overdraft limit: {self.overdraft_limit}| "
            f"💸 commission: {self.commission}"
        )
    
class InvestmentAccount(BankAccount):
    def __init__(self, id, owner_data, balance, account_status, currency, portfolio):

        if not isinstance(portfolio, dict):
            raise InvalidOperationError("Портфель должен быть словарем")    

        super().__init__(
            id,
            owner_data,
            balance,
            account_status,
            currency
        )
        self.portfolio = portfolio

    def project_yearly_growth(self, yearly_return):
        if yearly_return <= 0:
            raise InvalidOperationError("Годовая доходность должна быть положительной")
        total_value = sum(self.portfolio.values())

        projected_value = total_value * (
            1 + yearly_return / 100
        )

        return projected_value

    def get_account_info(self):
        return { 
            "id": self.id,
            "balance": self._balance,
            "status": self.account_status,
            "currency": self.currency,
            "portfolio": self.portfolio
            }

    def __str__(self):
        return (
            f"🏦 {type(self).__name__} | "
            f"👤 {self.owner_data} | "
            f"****{self.id[-4:]} | "
            f"📊 {self.account_status} | "
            f"💰 {self._balance} {self.currency}| "
            f"📈 {self.portfolio}"
        )