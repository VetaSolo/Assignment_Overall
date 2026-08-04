from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from unittest import result
from decimal import Decimal
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
        self._balance = Decimal(str(balance)) # защищённый баланс
        self.account_status = account_status #статус счёта: активный, замороженный, закрытый
# абстрактные методы:
    @abstractmethod
    def deposit(self, amount):
        pass
    @abstractmethod
    def withdraw(self, amount):
        pass
    @abstractmethod
    def get_account_info(self):
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

        amount = Decimal(str(amount))

        if amount <= 0:
            raise InvalidOperationError(
                "Сумма должна быть положительной"
            )

        self._balance += amount

    def withdraw(self, amount):
        if self.account_status == BankAccount.FROZEN:
            raise AccountFrozenError("Счет заморожен")

        if self.account_status == BankAccount.CLOSED:
            raise AccountClosedError("Счет закрыт")

        amount = Decimal(str(amount))

        if amount <= 0:
            raise InvalidOperationError(
                "Сумма должна быть положительной"
            )

        if amount > self._balance:
            raise InsufficientFundsError(
                "Недостаточно средств"
            )

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
            f"👤 {self.owner_data.full_name} | "
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
        monthly_return = Decimal(
            str(self.monthly_return)
        )

        interest = (
            self._balance
            * monthly_return
            / Decimal("100")
        )

        self._balance += interest 

    def withdraw(self, amount):
        amount = Decimal(str(amount))
        min_balance = Decimal(str(self.min_balance))

        if self._balance - amount < min_balance:
            raise InvalidOperationError(
                "Нельзя опуститься ниже минимального остатка"
            )

        super().withdraw(amount)
        

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
    def __init__(
        self,
        id,
        owner_data,
        balance,
        account_status,
        currency,
        withdraw_limit,
        overdraft_limit,
        commission
    ):
        withdraw_limit = Decimal(str(withdraw_limit))
        overdraft_limit = Decimal(str(overdraft_limit))
        commission = Decimal(str(commission))

        if withdraw_limit <= 0:
            raise InvalidOperationError(
                "Лимит на снятие должен быть положительным"
            )

        if overdraft_limit < 0:
            raise InvalidOperationError(
                "Овердрафт не может быть отрицательным"
            )

        if commission < 0:
            raise InvalidOperationError(
                "Комиссия не может быть отрицательной"
            )

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
        if self.account_status == BankAccount.FROZEN:
            raise AccountFrozenError("Счет заморожен")

        if self.account_status == BankAccount.CLOSED:
            raise AccountClosedError("Счет закрыт")

        amount = Decimal(str(amount))

        if amount <= 0:
            raise InvalidOperationError(
                "Сумма должна быть положительной"
            )

        if amount > self.withdraw_limit:
            raise InvalidOperationError(
                f"Превышен лимит снятия: "
                f"{self.withdraw_limit} {self.currency}"
            )

        commission_amount = (
            amount
            * self.commission
            / Decimal("100")
        )

        total_amount = amount + commission_amount

        available_funds = (
            self._balance + self.overdraft_limit
        )

        if total_amount > available_funds:
            raise InsufficientFundsError(
                "Недостаточно средств с учетом "
                "овердрафта и комиссии"
            )
        self._balance -= total_amount


    def get_account_info(self):
        return {
            "id": self.id,
            "balance": self._balance,
            "status": self.account_status,
            "currency": self.currency,
            "withdraw limit": self.withdraw_limit,
            "overdraft limit": self.overdraft_limit,
            "commission": self.commission
        }

    def __str__(self):
        return (
            f"🏦 {type(self).__name__} | "
            f"👤 {self.owner_data} | "
            f"****{self.id[-4:]} | "
            f"📊 {self.account_status} | "
            f"💰 {self._balance} {self.currency} | "
            f"🔒 withdraw limit: {self.withdraw_limit} | "
            f"📈 overdraft limit: {self.overdraft_limit} | "
            f"💸 commission: {self.commission}%"
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

class Client:
    def __init__(self, full_name, status, contacts, age, password):
        self.full_name = full_name
        self.id = str(uuid.uuid4())[:8]
        self.status = status
        self.account_numbers = []
        self.contacts = contacts
        self.password = password
        self.age = age
        self.is_blocked = False
        self.failed_attempts = 0
        self.transactions = []
        self.accounts = []

        if self.age < 18:
                    raise InvalidOperationError("Клиент должен быть старше 18 лет")

    def show_history(self):
        for transaction in self.transactions:
            print(
                transaction.id,
                transaction.transaction_type,
                transaction.amount,
                transaction.status
            )

class Bank:

    EXCHANGE_RATES_TO_RUB = {
        "RUB": Decimal("1"),
        "USD": Decimal("90"),
        "EUR": Decimal("100"),
        "KZT": Decimal("0.20"),
        "CNY": Decimal("12.50")
    }

    def __init__(self):
        self.clients = []
        self.accounts = []
        self.suspicious_actions = []

    def add_client(self, client):
        if client not in self.clients:
            self.clients.append(client)

    def open_account(self, client, account):
        if client not in self.clients:
            raise InvalidOperationError(
                "Клиент не зарегистрирован"
            )

        if account in self.accounts:
            raise InvalidOperationError(
                "Счёт уже зарегистрирован в банке"
            )

        if account.id in client.account_numbers:
            raise InvalidOperationError(
                "У клиента уже есть счёт с таким ID"
            )

        account.owner_data = client

        self.accounts.append(account)
        client.account_numbers.append(account.id)
        client.accounts.append(account)

    def close_account(self, account):
        account.account_status = BankAccount.CLOSED

    def freeze_account(self, account):
        account.account_status = BankAccount.FROZEN

    def unfreeze_account(self, account):
        account.account_status = BankAccount.ACTIVE

    def authenticate_client(self, client, password):

        # клиент не зарегистрирован
        if client not in self.clients:
            raise InvalidOperationError(
                "Клиент не найден"
            )

        # клиент уже заблокирован
        if client.is_blocked:
            self.suspicious_actions.append(
                f"Попытка входа заблокированного клиента: {client.full_name}"
            )
            raise InvalidOperationError(
                "Клиент заблокирован"
            )

        # правильный пароль
        if client.password == password:
            client.failed_attempts = 0
            return True

        # неправильный пароль
        client.failed_attempts += 1

        self.suspicious_actions.append(
            f"Неверный пароль клиента: {client.full_name}"
        )

        # 3 ошибки = блокировка
        if client.failed_attempts >= 3:
            client.is_blocked = True
            self.suspicious_actions.append(
                f"Клиент заблокирован: {client.full_name}"
            )
            raise InvalidOperationError(
                "Слишком много попыток. Клиент заблокирован"
            )

        return False

    def check_operation_time(self):
        from datetime import datetime
        current_time = datetime.now().time()
        if (
            datetime.strptime("00:00", "%H:%M").time()
            <= current_time <
            datetime.strptime("05:00", "%H:%M").time()
        ):
            raise InvalidOperationError(
                "Операции недоступны с 00:00 до 05:00"
            )    
    def search_accounts(self, client):
        return [
            account
            for account in self.accounts
            if account.owner_data.id == client.id
        ]
    def get_clients_ranking(self):
        ranking = []

        for client in self.clients:
            balance_rub = Decimal("0")

            for account in self.accounts:
                if account.owner_data.id == client.id:
                    balance_rub += self.convert_to_rub(
                        account._balance,
                        account.currency
                    )

            ranking.append(
                {
                    "client": client.full_name,
                    "client_id": client.id,
                    "balance": balance_rub,
                    "currency": "RUB"
                }
            )

        return sorted(
            ranking,
            key=lambda item: item["balance"],
            reverse=True
        )

        return sorted(
            ranking,
            key=lambda x: x["balance"],
            reverse=True
        )

    def transaction_statistics(self, transactions):
            result = {
                "total":0,
                "completed":0,
                "failed":0
            }
            for transaction in transactions:
                result["total"] += 1
                if transaction.status == Transaction.COMPLETED:
                    result["completed"] += 1
                if transaction.status == Transaction.FAILED:
                    result["failed"] += 1
            return result
    def get_total_balance(self):
            
        total = {}
        for account in self.accounts:
            if account.currency not in total:
                total[account.currency] = Decimal("0")
            total[account.currency] += account._balance
        return total
    def convert_to_rub(self, amount, currency):
        if currency not in self.EXCHANGE_RATES_TO_RUB:
            raise InvalidOperationError(
                f"Неизвестен курс валюты: {currency}"
            )

        amount = Decimal(str(amount))
        rate = self.EXCHANGE_RATES_TO_RUB[currency]

        return amount * rate

class Transaction:
    CREATED = "CREATED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    PENDING = "PENDING"

    ALLOWED_TRANSACTION_STATUSES = [
        CREATED,
        PROCESSING,
        COMPLETED,
        FAILED,
        CANCELLED,
        PENDING
    ]

    TRANSFER = "TRANSFER"
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"

    ALLOWED_TRANSACTION_TYPES = [
        TRANSFER,
        DEPOSIT,
        WITHDRAW
    ]

    def __init__(
        self,
        transaction_type,
        amount,
        currency,
        sender,
        receiver,
        commission=0,
        priority=0
    ):
        amount = Decimal(str(amount))
        commission = Decimal(str(commission))

        if transaction_type not in self.ALLOWED_TRANSACTION_TYPES:
            raise InvalidOperationError(
                "Неизвестный тип транзакции"
            )

        if amount <= 0:
            raise InvalidOperationError(
                "Сумма должна быть положительной"
            )

        if commission < 0:
            raise InvalidOperationError(
                "Комиссия не может быть отрицательной"
            )

        self.id = str(uuid.uuid4())[:8]
        self.transaction_type = transaction_type
        self.amount = amount
        self.currency = currency
        self.sender = sender
        self.receiver = receiver
        self.commission = commission
        self.status = self.CREATED
        self.created_at = datetime.now()
        self.execute_at = None
        self.failure_reason = None
        self.priority = priority
        self.retry_count = 0

        
class TransactionQueue:
    def __init__(self):
        self.queue = []

    def add_transaction(self, transaction):
        self.queue.append(transaction)
        self.queue.sort(key=lambda x: x.priority, reverse=True) 

    def get_next_transaction(self):
        for transaction in self.queue:
            if (
                transaction.execute_at is None
                or transaction.execute_at <= datetime.now()
            ):
                self.queue.remove(transaction)
                return transaction
        return None

    def cancel_transaction(self, transaction):
        if transaction in self.queue:
            transaction.status = Transaction.CANCELLED
            self.queue.remove(transaction) 

    def delayed_transaction(self, transaction, delay_time):

        if delay_time <= 0:
            raise InvalidOperationError(
                "Время задержки должно быть положительным")
        if transaction not in self.queue:
            raise InvalidOperationError(
                "Транзакция отсутствует в очереди"
            )

        transaction.execute_at = (
            datetime.now() +
            timedelta(minutes=delay_time)
        )

    def __str__(self):
        return f"TransactionQueue({len(self.queue)} transactions)"
    
class TransactionProcessor:

    EXCHANGE_RATES = {
        ("RUB", "USD"): Decimal("0.0125"),
        ("USD", "RUB"): Decimal("80"),

        ("RUB", "EUR"): Decimal("0.0111111111"),
        ("EUR", "RUB"): Decimal("90"),

        ("USD", "EUR"): Decimal("0.9"),
        ("EUR", "USD"): Decimal("1.11"),

        ("RUB", "KZT"): Decimal("6.5"),
        ("KZT", "RUB"): Decimal("0.1538461538"),

        ("RUB", "CNY"): Decimal("0.09"),
        ("CNY", "RUB"): Decimal("11")
    }

    def __init__(self, transaction_queue, risk_analyzer, audit_log, bank ):
        self.transaction_queue = transaction_queue
        self.error_log = []
        self.max_retries = 3
        self.risk_analyzer = risk_analyzer
        self.audit_log = audit_log
        self.bank = bank

    def convert_currency(
        self,
        amount,
        from_currency,
        to_currency
    ):
        amount = Decimal(str(amount))

        if from_currency == to_currency:
            return amount

        rate = self.EXCHANGE_RATES.get(
            (from_currency, to_currency)
        )

        if rate is None:
            raise InvalidOperationError(
                "Конвертация невозможна"
            )

        return amount * rate

    def process_transactions(self):
        while True:
            transaction = (
                self.transaction_queue
                .get_next_transaction()
            )
            if not transaction:
                break
            try:
                # анализ риска
                risk, reasons = (
                    self.risk_analyzer
                    .analyze(transaction)
                )
                self.audit_log.add_record(
                    risk,
                    f"Transaction {transaction.id}: {reasons}"
                )
                # опасная операция
                if risk == RiskAnalyzer.HIGH:

                    transaction.status = Transaction.FAILED
                    transaction.failure_reason = (
                        "Операция заблокирована системой безопасности"
                    )

                    self.audit_log.add_record(
                        AuditLog.HIGH,
                        f"Transaction {transaction.id} blocked"
                    )

                    continue

                self._process_transaction(transaction)

                transaction.status = (Transaction.COMPLETED)
                
                if transaction.sender:
                    transaction.sender.owner_data.transactions.append(
                        transaction
                        )
                if transaction.receiver:

                    if (
                        transaction.sender is None
                        or transaction.receiver.owner_data != transaction.sender.owner_data
                    ):
                        transaction.receiver.owner_data.transactions.append(
                            transaction
                        )
                
                
                self.audit_log.add_record(
                    AuditLog.LOW,
                    f"Transaction {transaction.id} completed"
                )
            except Exception as e:

                transaction.retry_count += 1
                if transaction.retry_count < self.max_retries:
                    transaction.status = Transaction.PENDING
                    self.transaction_queue.add_transaction(
                        transaction
                    )
                    self.audit_log.add_record(
                        AuditLog.MEDIUM,
                        f"Transaction {transaction.id} retry "
                        f"{transaction.retry_count}/{self.max_retries}"
                    )
                else:
                    transaction.status = Transaction.FAILED
                    transaction.failure_reason = str(e)
                    self.error_log.append(str(e))
                    self.audit_log.add_record(
                        AuditLog.HIGH,
                        f"Transaction {transaction.id} failed: {e}"
                    )


    def _process_transaction(self, transaction):

        self.bank.check_operation_time()
        transaction.status = Transaction.PROCESSING

        if (
            transaction.sender
            and transaction.sender.account_status
            != BankAccount.ACTIVE
        ):
            raise InvalidOperationError(
                "Счет отправителя недоступен"
            )

        if (
            transaction.receiver
            and transaction.receiver.account_status
            != BankAccount.ACTIVE
        ):
            raise InvalidOperationError(
                "Счет получателя недоступен"
            )

        if transaction.transaction_type == Transaction.DEPOSIT:
            if transaction.receiver is None:
                raise InvalidOperationError(
                    "Не указан счет получателя"
                )

            transaction.receiver.deposit(
                transaction.amount
            )

        elif transaction.transaction_type == Transaction.WITHDRAW:
            if transaction.sender is None:
                raise InvalidOperationError(
                    "Не указан счет отправителя"
                )

            transaction.sender.withdraw(
                transaction.amount
            )

        elif transaction.transaction_type == Transaction.TRANSFER:
            if (
                transaction.sender is None
                or transaction.receiver is None
            ):
                raise InvalidOperationError(
                    "Для перевода нужны отправитель и получатель"
                )

            commission = self.calculate_commission(
                transaction
            )

            transaction.commission = commission

            total_amount = (
                transaction.amount + commission
            )

            converted_amount = self.convert_currency(
                transaction.amount,
                transaction.sender.currency,
                transaction.receiver.currency
            )

            transaction.sender.withdraw(
                total_amount
            )

            transaction.receiver.deposit(
                converted_amount
            )
    def is_external_transfer(self, transaction):
        if transaction.transaction_type != Transaction.TRANSFER:
            return False

        if transaction.sender is None or transaction.receiver is None:
            return False

        return (
            transaction.sender.owner_data.id
            != transaction.receiver.owner_data.id
        )

    def calculate_commission(self, transaction):
        if not self.is_external_transfer(transaction):
            return Decimal("0")

        return (
            Decimal(str(transaction.amount))
            * Decimal("0.02")
        )

    

class AuditLog:

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

    ALLOWED_LEVELS = [
        LOW,
        MEDIUM,
        HIGH
    ]

    def __init__(self, filename="audit.log"):
        self.records = []
        self.filename = filename

    def add_record(self, level, message):

        if level not in self.ALLOWED_LEVELS:
            raise InvalidOperationError(
                "Неизвестный уровень важности"
            )
        record = {
            "time": datetime.now(),
            "level": level,
            "message": message
        }
        self.records.append(record)
        with open(self.filename, "a", encoding="utf-8") as file:
            file.write(
                f"{record['time']} | "
                f"{record['level']} | "
                f"{record['message']}\n"
            )
    def filter_records(self, level):
        if level not in self.ALLOWED_LEVELS:
            raise InvalidOperationError(
                "Неизвестный уровень важности"
            )
        return [
            record
            for record in self.records
            if record["level"] == level
        ]
    def __str__(self):
        return (
            f"AuditLog(records={len(self.records)})"
        )

class RiskAnalyzer:

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

    def __init__(self):
        # история операций клиентов
        self.transaction_history = {}
        # известные получатели
        self.known_receivers = {}
        # подозрительные операции
        self.suspicious_operations = {}

    def analyze(self, transaction):
        risk_level = self.LOW
        reasons = []

        # 1. Крупная сумма
        if transaction.amount >= 500000:
            risk_level = self.HIGH
            reasons.append("Крупная сумма операции")
        elif transaction.amount >= 100000:
            risk_level = self.MEDIUM

        sender = None
        if transaction.sender:
            sender = transaction.sender.owner_data

        # 2. Частые операции
        if sender:
            if sender not in self.transaction_history:
                self.transaction_history[sender] = []

            self.transaction_history[sender].append(datetime.now())

            recent_operations = [
                t
                for t in self.transaction_history[sender]
                if datetime.now() - t < timedelta(minutes=5)
            ]

            if len(recent_operations) >= 12:
                if risk_level != self.HIGH:
                    risk_level = self.MEDIUM

                reasons.append(
                    "Слишком много операций за короткое время"
                )

        # 3. Новый получатель
        if (
            sender
            and transaction.transaction_type == Transaction.TRANSFER
            and transaction.receiver
        ):
            receiver = transaction.receiver.id

            if sender not in self.known_receivers:
                self.known_receivers[sender] = set()

            is_new_receiver = (
                receiver not in self.known_receivers[sender]
            )

            if is_new_receiver:
                reasons.append("Перевод на новый счёт")

                if risk_level != self.HIGH:
                    risk_level = self.MEDIUM

                self.known_receivers[sender].add(receiver)

                if len(self.known_receivers[sender]) > 3:
                    reasons.append("Много новых получателей")

        # 4. Ночное время
        current_hour = datetime.now().hour
        if 0 <= current_hour < 5:
            risk_level = self.HIGH
            reasons.append("Операция в ночное время")

        if risk_level != self.LOW:
            self.suspicious_operations[transaction.id] = {
                "transaction": transaction,
                "risk": risk_level,
                "reason": reasons
            }

        return risk_level, reasons

    def get_suspicious_operations(self):
        return list(self.suspicious_operations.values())

    def get_client_risk_profile(self):
        profile = {}

        for item in self.suspicious_operations.values():
            transaction = item["transaction"]

            if transaction.sender is None:
                continue

            client = transaction.sender.owner_data

            if client not in profile:
                profile[client] = {
                    "risk": item["risk"],
                    "count": 0,
                    "reasons": []
                }

            profile[client]["count"] += 1
            profile[client]["reasons"].extend(
                item["reason"]
            )

            if item["risk"] == self.HIGH:
                profile[client]["risk"] = self.HIGH

            elif (
                item["risk"] == self.MEDIUM
                and profile[client]["risk"] != self.HIGH
            ):
                profile[client]["risk"] = self.MEDIUM

        return profile