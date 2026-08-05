import inspect
import json
import os
import sys
import tempfile
from datetime import datetime as RealDateTime
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

import matplotlib

matplotlib.use("Agg")

import models
from models import *
from utils import ReportBuilder


# ==========================================================
# Вспомогательные классы и функции
# ==========================================================


class DaytimeDateTime(RealDateTime):
    """Фиксированное дневное время для предсказуемых тестов."""

    @classmethod
    def now(cls, tz=None):
        return cls(
            2026,
            8,
            5,
            12,
            0,
            0,
            tzinfo=tz
        )


class NighttimeDateTime(RealDateTime):
    """Фиксированное ночное время для проверки ограничений."""

    @classmethod
    def now(cls, tz=None):
        return cls(
            2026,
            8,
            5,
            2,
            0,
            0,
            tzinfo=tz
        )


class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0

    def section(self, title):
        print("\n" + "=" * 70)
        print(title)
        print("=" * 70)

    def check(self, test_name, condition, details=""):
        if condition:
            self.passed += 1
            status = "✅ ПРОЙДЕН"
        else:
            self.failed += 1
            status = "❌ НЕ ПРОЙДЕН"

        print(f"\n{status}: {test_name}")

        if details:
            print(details)

    def check_exception(
        self,
        test_name,
        expected_exception,
        operation
    ):
        try:
            operation()

        except expected_exception as error:
            self.check(
                test_name,
                True,
                (
                    f"Получено ожидаемое исключение: "
                    f"{type(error).__name__}: {error}"
                )
            )

        except Exception as error:
            self.check(
                test_name,
                False,
                (
                    f"Ожидалось {expected_exception.__name__}, "
                    f"получено {type(error).__name__}: {error}"
                )
            )

        else:
            self.check(
                test_name,
                False,
                (
                    f"Ожидалось исключение "
                    f"{expected_exception.__name__}"
                )
            )

    def summary(self):
        total = self.passed + self.failed

        print("\n" + "=" * 70)
        print("ИТОГИ ТЕСТИРОВАНИЯ")
        print("=" * 70)

        print(f"Всего проверок: {total}")
        print(f"Пройдено: {self.passed}")
        print(f"Не пройдено: {self.failed}")

        if self.failed == 0:
            print("\n✅ ВСЕ ТРЕБОВАНИЯ ПРОШЛИ ПРОВЕРКУ")
        else:
            print(
                "\n❌ ЕСТЬ НЕПРОЙДЕННЫЕ ПРОВЕРКИ"
            )


def create_client(
    name,
    phone,
    age=30,
    password="1234"
):
    return Client(
        name,
        "ACTIVE",
        phone,
        age,
        password
    )


def create_services():
    bank = Bank()
    risk = RiskAnalyzer()
    audit = AuditLog()
    queue = TransactionQueue()

    processor = TransactionProcessor(
        queue,
        risk,
        audit,
        bank
    )

    # Для большинства тестов операции разрешены
    # независимо от текущего времени компьютера.
    bank.check_operation_time = lambda: None

    return bank, risk, audit, queue, processor


def create_fake_datetime_module(fake_datetime):
    """
    Создаёт временную замену модуля datetime.

    Нужна для Bank.check_operation_time(), потому что
    этот метод импортирует datetime внутри себя.
    """
    import datetime as real_datetime_module

    fake_module = ModuleType("datetime")

    for attribute_name in dir(real_datetime_module):
        setattr(
            fake_module,
            attribute_name,
            getattr(
                real_datetime_module,
                attribute_name
            )
        )

    fake_module.datetime = fake_datetime

    return fake_module


def get_first_method(instance, method_names):
    for method_name in method_names:
        method = getattr(
            instance,
            method_name,
            None
        )

        if callable(method):
            return method

    return None


def get_audit_records(audit):
    possible_attributes = [
        "records",
        "logs",
        "entries",
        "audit_records"
    ]

    for attribute_name in possible_attributes:
        value = getattr(
            audit,
            attribute_name,
            None
        )

        if isinstance(value, list):
            return value

    return None


# ==========================================================
# ДЕНЬ 1
# ==========================================================


def test_day_1(runner):
    runner.section(
        "ДЕНЬ 1. БАЗОВАЯ МОДЕЛЬ БАНКОВСКИХ СЧЕТОВ"
    )

    client = create_client(
        "Клиент первого дня",
        "+79990001001"
    )

    # ------------------------------------------------------
    # AbstractAccount
    # ------------------------------------------------------

    abstract_methods = getattr(
        AbstractAccount,
        "__abstractmethods__",
        set()
    )

    runner.check(
        "AbstractAccount является абстрактным классом",
        inspect.isabstract(AbstractAccount),
        f"Абстрактные методы: {abstract_methods}"
    )

    runner.check(
        "AbstractAccount содержит обязательные методы",
        {
            "deposit",
            "withdraw",
            "get_account_info"
        }.issubset(abstract_methods),
        f"Найдены методы: {abstract_methods}"
    )

    runner.check_exception(
        "AbstractAccount нельзя создать напрямую",
        TypeError,
        lambda: AbstractAccount(
            None,
            client,
            1000,
            BankAccount.ACTIVE
        )
    )

    # ------------------------------------------------------
    # BankAccount
    # ------------------------------------------------------

    account = BankAccount(
        None,
        client,
        1000,
        BankAccount.ACTIVE,
        "RUB"
    )

    runner.check(
        "ID счёта создаётся автоматически",
        (
            isinstance(account.id, str)
            and len(account.id) == 8
        ),
        f"Созданный ID: {account.id}"
    )

    runner.check(
        "Баланс является защищённым Decimal-полем",
        (
            hasattr(account, "_balance")
            and isinstance(
                account._balance,
                Decimal
            )
        ),
        (
            f"Тип баланса: "
            f"{type(account._balance).__name__}"
        )
    )

    runner.check(
        "Счёт хранит данные владельца и статус",
        (
            account.owner_data is client
            and account.account_status
            == BankAccount.ACTIVE
        )
    )

    runner.check(
        "Поддерживаются все требуемые валюты",
        set(
            [
                "RUB",
                "USD",
                "EUR",
                "KZT",
                "CNY"
            ]
        ).issubset(
            set(BankAccount.ALLOWED_CURRENCIES)
        ),
        (
            f"Разрешённые валюты: "
            f"{BankAccount.ALLOWED_CURRENCIES}"
        )
    )

    # ------------------------------------------------------
    # Валидация
    # ------------------------------------------------------

    runner.check_exception(
        "Нельзя создать счёт с отрицательным балансом",
        InvalidOperationError,
        lambda: BankAccount(
            None,
            client,
            -1,
            BankAccount.ACTIVE,
            "RUB"
        )
    )

    runner.check_exception(
        "Нельзя создать счёт с неизвестной валютой",
        InvalidOperationError,
        lambda: BankAccount(
            None,
            client,
            100,
            BankAccount.ACTIVE,
            "BTC"
        )
    )

    runner.check_exception(
        "Нельзя создать счёт с неизвестным статусом",
        InvalidOperationError,
        lambda: BankAccount(
            None,
            client,
            100,
            "UNKNOWN",
            "RUB"
        )
    )

    # ------------------------------------------------------
    # Пополнение и снятие
    # ------------------------------------------------------

    account.deposit(500)
    account.withdraw(200)

    runner.check(
        "Валидное пополнение и снятие работают",
        account._balance == Decimal("1300"),
        f"Фактический баланс: {account._balance}"
    )

    runner.check_exception(
        "Нельзя пополнить счёт на нулевую сумму",
        InvalidOperationError,
        lambda: account.deposit(0)
    )

    runner.check_exception(
        "Нельзя снять отрицательную сумму",
        InvalidOperationError,
        lambda: account.withdraw(-100)
    )

    runner.check_exception(
        "Нельзя снять больше доступного баланса",
        InsufficientFundsError,
        lambda: account.withdraw(100000)
    )

    # ------------------------------------------------------
    # Замороженный и закрытый счёт
    # ------------------------------------------------------

    frozen_account = BankAccount(
        None,
        client,
        1000,
        BankAccount.FROZEN,
        "RUB"
    )

    runner.check_exception(
        "Замороженный счёт нельзя пополнять",
        AccountFrozenError,
        lambda: frozen_account.deposit(100)
    )

    runner.check_exception(
        "С замороженного счёта нельзя снимать",
        AccountFrozenError,
        lambda: frozen_account.withdraw(100)
    )

    closed_account = BankAccount(
        None,
        client,
        1000,
        BankAccount.CLOSED,
        "RUB"
    )

    runner.check_exception(
        "Закрытый счёт нельзя пополнять",
        AccountClosedError,
        lambda: closed_account.deposit(100)
    )

    runner.check_exception(
        "С закрытого счёта нельзя снимать",
        AccountClosedError,
        lambda: closed_account.withdraw(100)
    )

    # ------------------------------------------------------
    # get_account_info и __str__
    # ------------------------------------------------------

    account_info = account.get_account_info()

    runner.check(
        "get_account_info возвращает сведения о счёте",
        (
            account_info["id"] == account.id
            and account_info["balance"]
            == account._balance
            and account_info["status"]
            == account.account_status
            and account_info["currency"]
            == account.currency
        ),
        f"Информация: {account_info}"
    )

    string_value = str(account)

    runner.check(
        "__str__ содержит обязательные сведения",
        all(
            value in string_value
            for value in [
                "BankAccount",
                client.full_name,
                account.id[-4:],
                account.account_status,
                str(account._balance),
                account.currency
            ]
        ),
        f"Результат __str__: {string_value}"
    )


# ==========================================================
# ДЕНЬ 2
# ==========================================================


def test_day_2(runner):
    runner.section(
        "ДЕНЬ 2. ПРОДВИНУТЫЕ ТИПЫ СЧЕТОВ"
    )

    client = create_client(
        "Клиент второго дня",
        "+79990002001"
    )

    # ------------------------------------------------------
    # Наследование
    # ------------------------------------------------------

    for account_class in [
        SavingsAccount,
        PremiumAccount,
        InvestmentAccount
    ]:
        runner.check(
            (
                f"{account_class.__name__} наследуется "
                f"от BankAccount"
            ),
            issubclass(
                account_class,
                BankAccount
            )
        )

    # ------------------------------------------------------
    # SavingsAccount
    # ------------------------------------------------------

    savings = SavingsAccount(
        None,
        client,
        10000,
        BankAccount.ACTIVE,
        "RUB",
        5000,
        5
    )

    runner.check(
        "SavingsAccount хранит min_balance и ставку",
        (
            Decimal(str(savings.min_balance))
            == Decimal("5000")
            and Decimal(str(savings.monthly_return))
            == Decimal("5")
        )
    )

    initial_savings_balance = savings._balance

    try:
        savings.apply_monthly_interest()

        expected_balance = (
            initial_savings_balance
            + initial_savings_balance
            * Decimal("5")
            / Decimal("100")
        )

        runner.check(
            "SavingsAccount начисляет месячный процент",
            savings._balance == expected_balance,
            (
                f"Ожидалось: {expected_balance}\n"
                f"Получено: {savings._balance}"
            )
        )

    except Exception as error:
        runner.check(
            "SavingsAccount начисляет месячный процент",
            False,
            f"{type(error).__name__}: {error}"
        )

    runner.check_exception(
        "SavingsAccount защищает минимальный остаток",
        InvalidOperationError,
        lambda: savings.withdraw(6000)
    )

    # ------------------------------------------------------
    # PremiumAccount
    # ------------------------------------------------------

    premium = PremiumAccount(
        None,
        client,
        1000,
        BankAccount.ACTIVE,
        "RUB",
        1500,
        500,
        2
    )

    try:
        premium.withdraw(1200)

        runner.check(
            "PremiumAccount поддерживает овердрафт",
            premium._balance == Decimal("-200"),
            f"Баланс: {premium._balance}"
        )

    except Exception as error:
        runner.check(
            "PremiumAccount поддерживает овердрафт",
            False,
            f"{type(error).__name__}: {error}"
        )

    runner.check_exception(
        "PremiumAccount проверяет лимит снятия",
        InvalidOperationError,
        lambda: premium.withdraw(1600)
    )

    runner.check(
        "PremiumAccount хранит фиксированную комиссию",
        premium.commission == Decimal("2"),
        f"Комиссия: {premium.commission}"
    )

    # ------------------------------------------------------
    # InvestmentAccount
    # ------------------------------------------------------

    investment = InvestmentAccount(
        None,
        client,
        100000,
        BankAccount.ACTIVE,
        "RUB",
        {
            "stocks": 150000,
            "bonds": 100000,
            "etf": 50000
        }
    )

    runner.check(
        "InvestmentAccount содержит требуемые активы",
        set(investment.portfolio.keys())
        == {
            "stocks",
            "bonds",
            "etf"
        },
        f"Портфель: {investment.portfolio}"
    )

    initial_portfolio = (
        investment.portfolio.copy()
    )

    try:
        investment.withdraw(20000)

        runner.check(
            "InvestmentAccount имеет отдельное снятие",
            (
                investment._balance
                == Decimal("80000")
                and investment.portfolio
                == initial_portfolio
            ),
            (
                f"Баланс: {investment._balance}\n"
                f"Портфель: {investment.portfolio}"
            )
        )

    except Exception as error:
        runner.check(
            "InvestmentAccount имеет отдельное снятие",
            False,
            f"{type(error).__name__}: {error}"
        )

    try:
        projected_value = (
            investment.project_yearly_growth(10)
        )

        runner.check(
            "InvestmentAccount прогнозирует годовой рост",
            projected_value == Decimal("330000"),
            f"Прогноз: {projected_value}"
        )

    except Exception as error:
        runner.check(
            "InvestmentAccount прогнозирует годовой рост",
            False,
            f"{type(error).__name__}: {error}"
        )

    # ------------------------------------------------------
    # Полиморфизм
    # ------------------------------------------------------

    for account_class in [
        SavingsAccount,
        PremiumAccount,
        InvestmentAccount
    ]:
        runner.check(
            (
                f"{account_class.__name__} "
                f"переопределяет withdraw()"
            ),
            (
                account_class.withdraw
                is not BankAccount.withdraw
            )
        )

        runner.check(
            (
                f"{account_class.__name__} "
                f"переопределяет get_account_info()"
            ),
            (
                account_class.get_account_info
                is not BankAccount.get_account_info
            )
        )

        runner.check(
            (
                f"{account_class.__name__} "
                f"переопределяет __str__()"
            ),
            (
                account_class.__str__
                is not BankAccount.__str__
            )
        )


# ==========================================================
# ДЕНЬ 3
# ==========================================================


def test_day_3(runner):
    runner.section(
        "ДЕНЬ 3. СИСТЕМА BANK"
    )

    # ------------------------------------------------------
    # Client
    # ------------------------------------------------------

    client = create_client(
        "Клиент банка",
        "+79990003001",
        age=25
    )

    runner.check(
        "Client хранит ФИО, ID и статус",
        (
            client.full_name == "Клиент банка"
            and bool(client.id)
            and client.status == "ACTIVE"
        ),
        (
            f"ID: {client.id}, "
            f"статус: {client.status}"
        )
    )

    runner.check(
        "Client хранит список номеров счетов",
        isinstance(
            client.account_numbers,
            list
        )
    )

    contact_attributes = [
        "contact",
        "contacts",
        "phone",
        "phone_number"
    ]

    has_contact = any(
        hasattr(client, attribute_name)
        for attribute_name in contact_attributes
    )

    runner.check(
        "Client хранит контактные данные",
        has_contact,
        (
            "Проверялись поля: "
            + ", ".join(contact_attributes)
        )
    )

    runner.check_exception(
        "Клиент младше 18 лет не создаётся",
        InvalidOperationError,
        lambda: create_client(
            "Несовершеннолетний",
            "+79990003002",
            age=17
        )
    )

    # ------------------------------------------------------
    # Bank
    # ------------------------------------------------------

    bank = Bank()

    bank.add_client(client)

    account = BankAccount(
        None,
        client,
        10000,
        BankAccount.ACTIVE,
        "RUB"
    )

    bank.open_account(
        client,
        account
    )

    runner.check(
        "Bank.add_client добавляет клиента",
        client in bank.clients
    )

    runner.check(
        "Bank.open_account открывает счёт",
        (
            account in bank.accounts
            and account in client.accounts
            and account.id
            in client.account_numbers
        )
    )

    found_accounts = bank.search_accounts(
        client
    )

    runner.check(
        "Bank.search_accounts находит счета клиента",
        account in found_accounts,
        f"Найдено счетов: {len(found_accounts)}"
    )

    bank.freeze_account(account)

    runner.check(
        "Bank.freeze_account замораживает счёт",
        account.account_status
        == BankAccount.FROZEN
    )

    bank.unfreeze_account(account)

    runner.check(
        "Bank.unfreeze_account активирует счёт",
        account.account_status
        == BankAccount.ACTIVE
    )

    bank.close_account(account)

    runner.check(
        "Bank.close_account закрывает счёт",
        account.account_status
        == BankAccount.CLOSED
    )

    # ------------------------------------------------------
    # Аутентификация
    # ------------------------------------------------------

    auth_bank = Bank()

    auth_client = create_client(
        "Клиент авторизации",
        "+79990003003",
        password="correct"
    )

    auth_bank.add_client(auth_client)

    runner.check(
        "Правильный пароль проходит проверку",
        auth_bank.authenticate_client(
            auth_client,
            "correct"
        ) is True
    )

    auth_bank.authenticate_client(
        auth_client,
        "wrong-1"
    )

    auth_bank.authenticate_client(
        auth_client,
        "wrong-2"
    )

    runner.check_exception(
        "Три неверные попытки блокируют клиента",
        InvalidOperationError,
        lambda: auth_bank.authenticate_client(
            auth_client,
            "wrong-3"
        )
    )

    runner.check(
        "После трёх ошибок клиент заблокирован",
        auth_client.is_blocked is True
    )

    runner.check(
        "Подозрительные действия сохраняются",
        len(auth_bank.suspicious_actions) >= 3,
        (
            f"Записей: "
            f"{len(auth_bank.suspicious_actions)}"
        )
    )

    # ------------------------------------------------------
    # Ночное ограничение
    # ------------------------------------------------------

    time_bank = Bank()

    night_module = create_fake_datetime_module(
        NighttimeDateTime
    )

    with patch.dict(
        sys.modules,
        {"datetime": night_module}
    ):
        runner.check_exception(
            "Операции запрещены с 00:00 до 05:00",
            InvalidOperationError,
            time_bank.check_operation_time
        )

    daytime_module = create_fake_datetime_module(
        DaytimeDateTime
    )

    try:
        with patch.dict(
            sys.modules,
            {"datetime": daytime_module}
        ):
            time_bank.check_operation_time()

        daytime_allowed = True

    except Exception:
        daytime_allowed = False

    runner.check(
        "Днём операции разрешены",
        daytime_allowed
    )

    # ------------------------------------------------------
    # Баланс и рейтинг
    # ------------------------------------------------------

    analytics_bank = Bank()

    rub_client = create_client(
        "RUB клиент",
        "+79990003004"
    )

    usd_client = create_client(
        "USD клиент",
        "+79990003005"
    )

    analytics_bank.add_client(rub_client)
    analytics_bank.add_client(usd_client)

    rub_account = BankAccount(
        None,
        rub_client,
        100000,
        BankAccount.ACTIVE,
        "RUB"
    )

    usd_account = BankAccount(
        None,
        usd_client,
        2000,
        BankAccount.ACTIVE,
        "USD"
    )

    analytics_bank.open_account(
        rub_client,
        rub_account
    )

    analytics_bank.open_account(
        usd_client,
        usd_account
    )

    total_balance = (
        analytics_bank.get_total_balance()
    )

    runner.check(
        "get_total_balance разделяет валюты",
        (
            total_balance["RUB"]
            == Decimal("100000")
            and total_balance["USD"]
            == Decimal("2000")
        ),
        f"Баланс: {total_balance}"
    )

    ranking = (
        analytics_bank.get_clients_ranking()
    )

    runner.check(
        "get_clients_ranking учитывает конвертацию",
        (
            ranking[0]["client"]
            == "USD клиент"
            and ranking[0]["balance"]
            == analytics_bank.convert_to_rub(
                Decimal("2000"),
                "USD"
            )
            and ranking[0]["currency"]
            == "RUB"
        ),
        f"Рейтинг: {ranking}"
    )


# ==========================================================
# ДЕНЬ 4
# ==========================================================


def test_day_4(runner):
    runner.section(
        "ДЕНЬ 4. СИСТЕМА ТРАНЗАКЦИЙ"
    )

    client_1 = create_client(
        "Отправитель транзакции",
        "+79990004001"
    )

    client_2 = create_client(
        "Получатель транзакции",
        "+79990004002"
    )

    sender = BankAccount(
        None,
        client_1,
        10000,
        BankAccount.ACTIVE,
        "RUB"
    )

    receiver = BankAccount(
        None,
        client_2,
        1000,
        BankAccount.ACTIVE,
        "RUB"
    )

    # ------------------------------------------------------
    # Transaction
    # ------------------------------------------------------

    transaction = Transaction(
        Transaction.TRANSFER,
        1000,
        "RUB",
        sender,
        receiver,
        priority=5
    )

    runner.check(
        "Transaction содержит обязательные поля",
        (
            bool(transaction.id)
            and transaction.transaction_type
            == Transaction.TRANSFER
            and transaction.amount
            == Decimal("1000")
            and transaction.currency == "RUB"
            and transaction.sender is sender
            and transaction.receiver is receiver
            and transaction.commission
            == Decimal("0")
            and transaction.status
            == Transaction.CREATED
            and transaction.created_at is not None
            and transaction.failure_reason is None
        )
    )

    runner.check_exception(
        "Transaction запрещает отрицательную сумму",
        InvalidOperationError,
        lambda: Transaction(
            Transaction.TRANSFER,
            -1,
            "RUB",
            sender,
            receiver
        )
    )

    runner.check_exception(
        "Transaction проверяет валюту",
        InvalidOperationError,
        lambda: Transaction(
            Transaction.TRANSFER,
            100,
            "BTC",
            sender,
            receiver
        )
    )

    # ------------------------------------------------------
    # TransactionQueue
    # ------------------------------------------------------

    priority_queue = TransactionQueue()

    low_priority = Transaction(
        Transaction.DEPOSIT,
        10,
        "RUB",
        None,
        receiver,
        priority=1
    )

    high_priority = Transaction(
        Transaction.DEPOSIT,
        10,
        "RUB",
        None,
        receiver,
        priority=10
    )

    medium_priority = Transaction(
        Transaction.DEPOSIT,
        10,
        "RUB",
        None,
        receiver,
        priority=5
    )

    priority_queue.add_transaction(
        low_priority
    )

    priority_queue.add_transaction(
        high_priority
    )

    priority_queue.add_transaction(
        medium_priority
    )

    first_transaction = (
        priority_queue.get_next_transaction()
    )

    runner.check(
        "TransactionQueue учитывает приоритет",
        first_transaction is high_priority
    )

    delayed_queue = TransactionQueue()

    delayed_transaction = Transaction(
        Transaction.DEPOSIT,
        10,
        "RUB",
        None,
        receiver
    )

    delayed_queue.add_transaction(
        delayed_transaction
    )

    delayed_queue.delayed_transaction(
        delayed_transaction,
        5
    )

    runner.check(
        "TransactionQueue поддерживает отложенные операции",
        (
            delayed_transaction.execute_at
            is not None
            and delayed_queue.get_next_transaction()
            is None
        ),
        (
            f"Время выполнения: "
            f"{delayed_transaction.execute_at}"
        )
    )

    cancel_queue = TransactionQueue()

    cancelled_transaction = Transaction(
        Transaction.DEPOSIT,
        10,
        "RUB",
        None,
        receiver
    )

    cancel_queue.add_transaction(
        cancelled_transaction
    )

    cancel_queue.cancel_transaction(
        cancelled_transaction
    )

    runner.check(
        "TransactionQueue отменяет транзакции",
        (
            cancelled_transaction.status
            == Transaction.CANCELLED
            and cancelled_transaction
            not in cancel_queue.queue
        )
    )

    # ------------------------------------------------------
    # Валюта транзакции: DEPOSIT
    # ------------------------------------------------------

    (
        deposit_bank,
        deposit_risk,
        deposit_audit,
        deposit_queue,
        deposit_processor
    ) = create_services()

    deposit_client = create_client(
        "Клиент пополнения",
        "+79990004003"
    )

    deposit_bank.add_client(
        deposit_client
    )

    usd_account = BankAccount(
        None,
        deposit_client,
        100,
        BankAccount.ACTIVE,
        "USD"
    )

    deposit_bank.open_account(
        deposit_client,
        usd_account
    )

    deposit_transaction = Transaction(
        Transaction.DEPOSIT,
        800,
        "RUB",
        None,
        usd_account
    )

    deposit_queue.add_transaction(
        deposit_transaction
    )

    with patch.object(
        models,
        "datetime",
        DaytimeDateTime
    ):
        deposit_processor.process_transactions()

    runner.check(
        "DEPOSIT использует валюту транзакции",
        (
            deposit_transaction.status
            == Transaction.COMPLETED
            and usd_account._balance
            == Decimal("110")
            and deposit_transaction.receiver_credit
            == Decimal("10.0000")
        ),
        (
            f"Баланс: {usd_account._balance} USD\n"
            f"Зачислено: "
            f"{deposit_transaction.receiver_credit} USD"
        )
    )

    # ------------------------------------------------------
    # Валюта транзакции: WITHDRAW
    # ------------------------------------------------------

    withdraw_transaction = Transaction(
        Transaction.WITHDRAW,
        800,
        "RUB",
        usd_account,
        None
    )

    deposit_queue.add_transaction(
        withdraw_transaction
    )

    with patch.object(
        models,
        "datetime",
        DaytimeDateTime
    ):
        deposit_processor.process_transactions()

    runner.check(
        "WITHDRAW использует валюту транзакции",
        (
            withdraw_transaction.status
            == Transaction.COMPLETED
            and usd_account._balance
            == Decimal("100")
            and withdraw_transaction.sender_debit
            == Decimal("10.0000")
        ),
        (
            f"Списано: "
            f"{withdraw_transaction.sender_debit} USD\n"
            f"Баланс: {usd_account._balance} USD"
        )
    )

    # ------------------------------------------------------
    # Перевод и комиссия
    # ------------------------------------------------------

    (
        transfer_bank,
        transfer_risk,
        transfer_audit,
        transfer_queue,
        transfer_processor
    ) = create_services()

    transfer_sender_client = create_client(
        "Валютный отправитель",
        "+79990004004"
    )

    transfer_receiver_client = create_client(
        "Валютный получатель",
        "+79990004005"
    )

    transfer_bank.add_client(
        transfer_sender_client
    )

    transfer_bank.add_client(
        transfer_receiver_client
    )

    transfer_sender = BankAccount(
        None,
        transfer_sender_client,
        100,
        BankAccount.ACTIVE,
        "USD"
    )

    transfer_receiver = BankAccount(
        None,
        transfer_receiver_client,
        0,
        BankAccount.ACTIVE,
        "RUB"
    )

    transfer_bank.open_account(
        transfer_sender_client,
        transfer_sender
    )

    transfer_bank.open_account(
        transfer_receiver_client,
        transfer_receiver
    )

    currency_transfer = Transaction(
        Transaction.TRANSFER,
        100,
        "RUB",
        transfer_sender,
        transfer_receiver
    )

    transfer_queue.add_transaction(
        currency_transfer
    )

    with patch.object(
        models,
        "datetime",
        DaytimeDateTime
    ):
        transfer_processor.process_transactions()

    runner.check(
        "TRANSFER использует валюту транзакции",
        (
            currency_transfer.status
            == Transaction.COMPLETED
            and currency_transfer.commission
            == Decimal("2")
            and currency_transfer.sender_debit
            == Decimal("1.2750")
            and currency_transfer.receiver_credit
            == Decimal("100")
            and transfer_sender._balance
            == Decimal("98.7250")
            and transfer_receiver._balance
            == Decimal("100")
        ),
        (
            f"Комиссия: "
            f"{currency_transfer.commission} RUB\n"
            f"Списано: "
            f"{currency_transfer.sender_debit} USD\n"
            f"Зачислено: "
            f"{currency_transfer.receiver_credit} RUB"
        )
    )

    # ------------------------------------------------------
    # Внутренний перевод без комиссии
    # ------------------------------------------------------

    internal_client = create_client(
        "Внутренний клиент",
        "+79990004006"
    )

    internal_account_1 = BankAccount(
        None,
        internal_client,
        5000,
        BankAccount.ACTIVE,
        "RUB"
    )

    internal_account_2 = BankAccount(
        None,
        internal_client,
        1000,
        BankAccount.ACTIVE,
        "RUB"
    )

    internal_transfer = Transaction(
        Transaction.TRANSFER,
        1000,
        "RUB",
        internal_account_1,
        internal_account_2
    )

    runner.check(
        "Внутренний перевод выполняется без комиссии",
        transfer_processor.calculate_commission(
            internal_transfer
        ) == Decimal("0")
    )

    # ------------------------------------------------------
    # PremiumAccount без двойной комиссии
    # ------------------------------------------------------

    (
        premium_bank,
        premium_risk,
        premium_audit,
        premium_queue,
        premium_processor
    ) = create_services()

    premium_client = create_client(
        "Premium отправитель",
        "+79990004007"
    )

    premium_receiver_client = create_client(
        "Premium получатель",
        "+79990004008"
    )

    premium_bank.add_client(premium_client)
    premium_bank.add_client(
        premium_receiver_client
    )

    premium_sender = PremiumAccount(
        None,
        premium_client,
        10000,
        BankAccount.ACTIVE,
        "RUB",
        5000,
        1000,
        1
    )

    premium_receiver = BankAccount(
        None,
        premium_receiver_client,
        0,
        BankAccount.ACTIVE,
        "RUB"
    )

    premium_bank.open_account(
        premium_client,
        premium_sender
    )

    premium_bank.open_account(
        premium_receiver_client,
        premium_receiver
    )

    premium_transfer = Transaction(
        Transaction.TRANSFER,
        1000,
        "RUB",
        premium_sender,
        premium_receiver
    )

    premium_queue.add_transaction(
        premium_transfer
    )

    with patch.object(
        models,
        "datetime",
        DaytimeDateTime
    ):
        premium_processor.process_transactions()

    runner.check(
        "PremiumAccount не начисляет комиссию дважды",
        (
            premium_transfer.status
            == Transaction.COMPLETED
            and premium_transfer.commission
            == Decimal("10")
            and premium_transfer.sender_debit
            == Decimal("1010")
            and premium_sender._balance
            == Decimal("8990")
            and premium_receiver._balance
            == Decimal("1000")
        ),
        (
            f"Комиссия: "
            f"{premium_transfer.commission}\n"
            f"Списано: "
            f"{premium_transfer.sender_debit}\n"
            f"Баланс: {premium_sender._balance}"
        )
    )

    # ------------------------------------------------------
    # Повторные попытки и фиксация ошибок
    # ------------------------------------------------------

    (
        error_bank,
        error_risk,
        error_audit,
        error_queue,
        error_processor
    ) = create_services()

    error_sender_client = create_client(
        "Отправитель ошибки",
        "+79990004009"
    )

    error_receiver_client = create_client(
        "Получатель ошибки",
        "+79990004010"
    )

    error_bank.add_client(
        error_sender_client
    )

    error_bank.add_client(
        error_receiver_client
    )

    error_sender = BankAccount(
        None,
        error_sender_client,
        1000,
        BankAccount.ACTIVE,
        "RUB"
    )

    frozen_receiver = BankAccount(
        None,
        error_receiver_client,
        0,
        BankAccount.FROZEN,
        "RUB"
    )

    failed_transaction = Transaction(
        Transaction.TRANSFER,
        100,
        "RUB",
        error_sender,
        frozen_receiver
    )

    error_queue.add_transaction(
        failed_transaction
    )

    with patch.object(
        models,
        "datetime",
        DaytimeDateTime
    ):
        error_processor.process_transactions()

    runner.check(
        "Processor выполняет повторные попытки",
        (
            failed_transaction.status
            == Transaction.FAILED
            and failed_transaction.retry_count
            == error_processor.max_retries
        ),
        (
            f"Статус: {failed_transaction.status}\n"
            f"Попытки: "
            f"{failed_transaction.retry_count}"
        )
    )

    runner.check(
        "Processor фиксирует ошибки",
        len(error_processor.error_log) >= 1,
        f"Ошибки: {error_processor.error_log}"
    )

    # ------------------------------------------------------
    # 10 транзакций
    # ------------------------------------------------------

    (
        batch_bank,
        batch_risk,
        batch_audit,
        batch_queue,
        batch_processor
    ) = create_services()

    batch_client = create_client(
        "Клиент пакета",
        "+79990004011"
    )

    batch_bank.add_client(batch_client)

    batch_account = BankAccount(
        None,
        batch_client,
        0,
        BankAccount.ACTIVE,
        "RUB"
    )

    batch_bank.open_account(
        batch_client,
        batch_account
    )

    batch_transactions = []

    for index in range(10):
        batch_transaction = Transaction(
            Transaction.DEPOSIT,
            100,
            "RUB",
            None,
            batch_account,
            priority=index
        )

        batch_transactions.append(
            batch_transaction
        )

        batch_queue.add_transaction(
            batch_transaction
        )

    with patch.object(
        models,
        "datetime",
        DaytimeDateTime
    ):
        batch_processor.process_transactions()

    runner.check(
        "Очередь обрабатывает 10 транзакций",
        (
            all(
                item.status
                == Transaction.COMPLETED
                for item in batch_transactions
            )
            and batch_account._balance
            == Decimal("1000")
        ),
        (
            f"Завершено: "
            f"{sum(item.status == Transaction.COMPLETED for item in batch_transactions)}"
        )
    )


# ==========================================================
# ДЕНЬ 5
# ==========================================================


def test_day_5(runner):
    runner.section(
        "ДЕНЬ 5. АУДИТ И РИСК-АНАЛИЗ"
    )

    # ------------------------------------------------------
    # AuditLog
    # ------------------------------------------------------

    audit = AuditLog()

    audit.add_record(
        AuditLog.LOW,
        "Обычная операция"
    )

    audit.add_record(
        AuditLog.MEDIUM,
        "Операция требует внимания"
    )

    audit.add_record(
        AuditLog.HIGH,
        "Опасная операция"
    )

    records = get_audit_records(audit)

    runner.check(
        "AuditLog сохраняет записи в памяти",
        (
            records is not None
            and len(records) >= 3
        ),
        f"Количество записей: {len(records) if records is not None else 0}"
    )

    filter_method = get_first_method(
        audit,
        [
            "filter_by_level",
            "filter_records",
            "get_records_by_level",
            "filter_logs"
        ]
    )

    runner.check(
        "AuditLog содержит метод фильтрации",
        filter_method is not None,
        (
            "Ожидался один из методов: "
            "filter_by_level, filter_records, "
            "get_records_by_level, filter_logs"
        )
    )

    if filter_method is not None:
        try:
            filtered_records = filter_method(
                AuditLog.HIGH
            )

            runner.check(
                "AuditLog фильтрует записи",
                len(filtered_records) >= 1,
                (
                    f"Найдено записей HIGH: "
                    f"{len(filtered_records)}"
                )
            )

        except Exception as error:
            runner.check(
                "AuditLog фильтрует записи",
                False,
                f"{type(error).__name__}: {error}"
            )

    save_method = get_first_method(
        audit,
        [
            "save_to_file",
            "export_to_file",
            "write_to_file",
            "save"
        ]
    )

    runner.check(
        "AuditLog содержит метод сохранения в файл",
        save_method is not None,
        (
            "Ожидался один из методов: "
            "save_to_file, export_to_file, "
            "write_to_file, save"
        )
    )

    if save_method is not None:
        with tempfile.TemporaryDirectory() as temp_dir:
            audit_path = (
                Path(temp_dir)
                / "audit.log"
            )

            try:
                save_method(
                    str(audit_path)
                )

                runner.check(
                    "AuditLog сохраняет файл",
                    (
                        audit_path.exists()
                        and audit_path.stat().st_size > 0
                    ),
                    f"Путь: {audit_path}"
                )

            except Exception as error:
                runner.check(
                    "AuditLog сохраняет файл",
                    False,
                    f"{type(error).__name__}: {error}"
                )

    # ------------------------------------------------------
    # RiskAnalyzer: крупная сумма
    # ------------------------------------------------------

    sender_client = create_client(
        "Рискованный отправитель",
        "+79990005001"
    )

    receiver_client = create_client(
        "Рискованный получатель",
        "+79990005002"
    )

    sender = BankAccount(
        None,
        sender_client,
        1000000,
        BankAccount.ACTIVE,
        "RUB"
    )

    receiver = BankAccount(
        None,
        receiver_client,
        0,
        BankAccount.ACTIVE,
        "RUB"
    )

    large_risk = RiskAnalyzer()

    large_transaction = Transaction(
        Transaction.TRANSFER,
        600000,
        "RUB",
        sender,
        receiver
    )

    with patch.object(
        models,
        "datetime",
        DaytimeDateTime
    ):
        risk_level, reasons = (
            large_risk.analyze(
                large_transaction
            )
        )

    runner.check(
        "Крупная сумма получает высокий риск",
        (
            risk_level == RiskAnalyzer.HIGH
            and "Крупная сумма операции"
            in reasons
        ),
        (
            f"Риск: {risk_level}\n"
            f"Причины: {reasons}"
        )
    )

    # ------------------------------------------------------
    # Частые операции
    # ------------------------------------------------------

    frequent_risk = RiskAnalyzer()

    with patch.object(
        models,
        "datetime",
        DaytimeDateTime
    ):
        last_level = None
        last_reasons = None

        for _ in range(12):
            frequent_transaction = Transaction(
                Transaction.WITHDRAW,
                10,
                "RUB",
                sender,
                None
            )

            last_level, last_reasons = (
                frequent_risk.analyze(
                    frequent_transaction
                )
            )

    runner.check(
        "Частые операции считаются подозрительными",
        (
            last_level == RiskAnalyzer.MEDIUM
            and any(
                "Слишком много операций"
                in reason
                for reason in last_reasons
            )
        ),
        (
            f"Риск: {last_level}\n"
            f"Причины: {last_reasons}"
        )
    )

    # ------------------------------------------------------
    # Новый получатель
    # ------------------------------------------------------

    new_receiver_risk = RiskAnalyzer()

    new_receiver_transaction = Transaction(
        Transaction.TRANSFER,
        1000,
        "RUB",
        sender,
        receiver
    )

    with patch.object(
        models,
        "datetime",
        DaytimeDateTime
    ):
        new_level, new_reasons = (
            new_receiver_risk.analyze(
                new_receiver_transaction
            )
        )

    runner.check(
        "Первый перевод на новый счёт подозрительный",
        (
            new_level == RiskAnalyzer.MEDIUM
            and "Перевод на новый счёт"
            in new_reasons
        ),
        (
            f"Риск: {new_level}\n"
            f"Причины: {new_reasons}"
        )
    )

    # Получатель не должен становиться известным
    # только после анализа.
    known_before_success = (
        new_receiver_risk
        .known_receivers
        .get(sender_client, set())
    )

    runner.check(
        "Анализ не регистрирует получателя до успеха",
        receiver.id not in known_before_success,
        (
            f"Известные получатели: "
            f"{known_before_success}"
        )
    )

    new_receiver_risk.register_successful_transaction(
        new_receiver_transaction
    )

    known_after_success = (
        new_receiver_risk
        .known_receivers
        .get(sender_client, set())
    )

    runner.check(
        "Успешная операция регистрирует получателя",
        receiver.id in known_after_success,
        (
            f"Известные получатели: "
            f"{known_after_success}"
        )
    )

    # ------------------------------------------------------
    # Ночная операция
    # ------------------------------------------------------

    night_risk = RiskAnalyzer()

    night_transaction = Transaction(
        Transaction.WITHDRAW,
        100,
        "RUB",
        sender,
        None
    )

    with patch.object(
        models,
        "datetime",
        NighttimeDateTime
    ):
        night_level, night_reasons = (
            night_risk.analyze(
                night_transaction
            )
        )

    runner.check(
        "Ночная операция получает высокий риск",
        (
            night_level == RiskAnalyzer.HIGH
            and "Операция в ночное время"
            in night_reasons
        ),
        (
            f"Риск: {night_level}\n"
            f"Причины: {night_reasons}"
        )
    )

    # ------------------------------------------------------
    # Блокировка опасной операции
    # ------------------------------------------------------

    (
        block_bank,
        block_risk,
        block_audit,
        block_queue,
        block_processor
    ) = create_services()

    block_bank.add_client(sender_client)
    block_bank.add_client(receiver_client)

    blocked_transaction = Transaction(
        Transaction.TRANSFER,
        600000,
        "RUB",
        sender,
        receiver
    )

    initial_sender_balance = sender._balance
    initial_receiver_balance = receiver._balance

    block_queue.add_transaction(
        blocked_transaction
    )

    with patch.object(
        models,
        "datetime",
        DaytimeDateTime
    ):
        block_processor.process_transactions()

    runner.check(
        "Банк блокирует операцию с высоким риском",
        (
            blocked_transaction.status
            == Transaction.FAILED
            and sender._balance
            == initial_sender_balance
            and receiver._balance
            == initial_receiver_balance
        ),
        (
            f"Статус: {blocked_transaction.status}\n"
            f"Причина: "
            f"{blocked_transaction.failure_reason}"
        )
    )

    # ------------------------------------------------------
    # Подозрительные операции и риск-профиль
    # ------------------------------------------------------

    suspicious = (
        large_risk.get_suspicious_operations()
    )

    runner.check(
        "RiskAnalyzer возвращает подозрительные операции",
        (
            len(suspicious) >= 1
            and suspicious[0]["transaction"]
            is large_transaction
        )
    )

    try:
        profile = (
            large_risk
            .get_client_risk_profile()
        )

        runner.check(
            "RiskAnalyzer формирует риск-профиль клиента",
            (
                sender_client in profile
                and profile[sender_client]["count"]
                >= 1
                and profile[sender_client]["risk"]
                == RiskAnalyzer.HIGH
            ),
            f"Профиль: {profile}"
        )

    except Exception as error:
        runner.check(
            "RiskAnalyzer формирует риск-профиль клиента",
            False,
            f"{type(error).__name__}: {error}"
        )


# ==========================================================
# ДЕНЬ 6
# ==========================================================


def build_day_6_demo(runner):
    runner.section(
        "ДЕНЬ 6. КОМПЛЕКСНАЯ ДЕМОНСТРАЦИЯ"
    )

    bank, risk, audit, queue, processor = (
        create_services()
    )

    clients = []

    for index in range(5):
        client = create_client(
            f"Демо клиент {index + 1}",
            f"+79990006{index:03d}"
        )

        bank.add_client(client)
        clients.append(client)

    accounts = []

    for client in clients:
        first_account = BankAccount(
            None,
            client,
            200000,
            BankAccount.ACTIVE,
            "RUB"
        )

        second_account = BankAccount(
            None,
            client,
            100000,
            BankAccount.ACTIVE,
            "RUB"
        )

        bank.open_account(
            client,
            first_account
        )

        bank.open_account(
            client,
            second_account
        )

        accounts.extend(
            [
                first_account,
                second_account
            ]
        )

    runner.check(
        "Создано от 5 до 10 клиентов",
        5 <= len(clients) <= 10,
        f"Клиентов: {len(clients)}"
    )

    runner.check(
        "Создано от 10 до 15 счетов",
        10 <= len(accounts) <= 15,
        f"Счетов: {len(accounts)}"
    )

    transactions = []

    # 30 обычных внутренних переводов.
    for index in range(30):
        client_index = index % len(clients)

        sender = accounts[
            client_index * 2
        ]

        receiver = accounts[
            client_index * 2 + 1
        ]

        transaction = Transaction(
            Transaction.TRANSFER,
            100,
            "RUB",
            sender,
            receiver,
            priority=index % 5
        )

        transactions.append(transaction)
        queue.add_transaction(transaction)

    # Ошибочная операция на замороженный счёт.
    frozen_receiver = accounts[3]
    frozen_receiver.account_status = (
        BankAccount.FROZEN
    )

    failed_transaction = Transaction(
        Transaction.TRANSFER,
        100,
        "RUB",
        accounts[0],
        frozen_receiver,
        priority=8
    )

    transactions.append(failed_transaction)
    queue.add_transaction(failed_transaction)

    # Подозрительная крупная операция.
    dangerous_transaction = Transaction(
        Transaction.TRANSFER,
        600000,
        "RUB",
        accounts[0],
        accounts[5],
        priority=10
    )

    transactions.append(
        dangerous_transaction
    )

    queue.add_transaction(
        dangerous_transaction
    )

    runner.check(
        "Создано от 30 до 50 транзакций",
        30 <= len(transactions) <= 50,
        f"Транзакций: {len(transactions)}"
    )

    queued_before_processing = (
        len(queue.queue)
    )

    with patch.object(
        models,
        "datetime",
        DaytimeDateTime
    ):
        processor.process_transactions()

    runner.check(
        "Транзакции попали в очередь",
        queued_before_processing
        == len(transactions),
        (
            f"Было в очереди: "
            f"{queued_before_processing}"
        )
    )

    completed_count = sum(
        transaction.status
        == Transaction.COMPLETED
        for transaction in transactions
    )

    failed_count = sum(
        transaction.status
        == Transaction.FAILED
        for transaction in transactions
    )

    runner.check(
        "Демонстрация содержит выполненные операции",
        completed_count >= 1,
        f"Выполнено: {completed_count}"
    )

    runner.check(
        "Демонстрация содержит отклонённые операции",
        failed_count >= 1,
        f"Отклонено: {failed_count}"
    )

    suspicious_operations = (
        risk.get_suspicious_operations()
    )

    runner.check(
        "Демонстрация содержит подозрительные операции",
        len(suspicious_operations) >= 1,
        (
            f"Подозрительных операций: "
            f"{len(suspicious_operations)}"
        )
    )

    client_accounts = (
        bank.search_accounts(clients[0])
    )

    runner.check(
        "Можно показать счета клиента",
        len(client_accounts) == 2,
        f"Счетов клиента: {len(client_accounts)}"
    )

    runner.check(
        "Можно показать историю клиента",
        len(clients[0].transactions) >= 1,
        (
            f"Операций в истории: "
            f"{len(clients[0].transactions)}"
        )
    )

    ranking = bank.get_clients_ranking()

    runner.check(
        "Формируется топ-3 клиентов",
        len(ranking[:3]) == 3,
        f"Топ-3: {ranking[:3]}"
    )

    statistics = bank.transaction_statistics(
        transactions
    )

    runner.check(
        "Формируется статистика транзакций",
        (
            statistics["total"]
            == len(transactions)
            and statistics["completed"]
            == completed_count
            and statistics["failed"]
            == failed_count
        ),
        f"Статистика: {statistics}"
    )

    total_balance = bank.get_total_balance()

    runner.check(
        "Формируется общий баланс банка",
        (
            isinstance(total_balance, dict)
            and "RUB" in total_balance
        ),
        f"Баланс: {total_balance}"
    )

    return {
        "bank": bank,
        "risk": risk,
        "audit": audit,
        "queue": queue,
        "processor": processor,
        "clients": clients,
        "accounts": accounts,
        "transactions": transactions
    }


# ==========================================================
# ДЕНЬ 7
# ==========================================================


def test_day_7(runner, demo_data):
    runner.section(
        "ДЕНЬ 7. ОТЧЁТНОСТЬ И ВИЗУАЛИЗАЦИЯ"
    )

    bank = demo_data["bank"]
    risk = demo_data["risk"]
    clients = demo_data["clients"]
    transactions = demo_data["transactions"]

    report_builder = ReportBuilder(
        bank,
        transactions,
        risk
    )

    # ------------------------------------------------------
    # Отчёт по клиенту
    # ------------------------------------------------------

    client_report = (
        report_builder.client_report(
            clients[0]
        )
    )

    runner.check(
        "Формируется отчёт по клиенту",
        (
            isinstance(client_report, dict)
            and client_report["client"]
            == clients[0].full_name
            and "accounts" in client_report
            and "transactions_count"
            in client_report
        ),
        f"Отчёт: {client_report}"
    )

    # ------------------------------------------------------
    # Отчёт по банку
    # ------------------------------------------------------

    bank_report = (
        report_builder.bank_report()
    )

    runner.check(
        "Формируется отчёт по банку",
        (
            isinstance(bank_report, dict)
            and bank_report["clients"]
            == len(bank.clients)
            and bank_report["accounts"]
            == len(bank.accounts)
            and bank_report["transactions"]
            == len(transactions)
        ),
        f"Отчёт: {bank_report}"
    )

    # ------------------------------------------------------
    # Отчёт по рискам
    # ------------------------------------------------------

    risk_report = (
        report_builder.risk_report()
    )

    runner.check(
        "Формируется отчёт по рискам",
        (
            isinstance(risk_report, list)
            and len(risk_report) >= 1
            and {
                "transaction",
                "risk",
                "reason"
            }.issubset(
                risk_report[0].keys()
            )
        ),
        f"Записей: {len(risk_report)}"
    )

    # ------------------------------------------------------
    # JSON, CSV и графики
    # ------------------------------------------------------

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        json_path = (
            temp_path / "bank_report.json"
        )

        csv_path = (
            temp_path / "risk_report.csv"
        )

        try:
            report_builder.export_to_json(
                bank_report,
                str(json_path)
            )

            json_created = (
                json_path.exists()
                and json_path.stat().st_size > 0
            )

            if json_created:
                with open(
                    json_path,
                    "r",
                    encoding="utf-8"
                ) as file:
                    loaded_json = json.load(file)

                json_valid = isinstance(
                    loaded_json,
                    dict
                )
            else:
                json_valid = False

            runner.check(
                "JSON-отчёт сохраняется",
                json_created and json_valid,
                f"Путь: {json_path}"
            )

        except Exception as error:
            runner.check(
                "JSON-отчёт сохраняется",
                False,
                f"{type(error).__name__}: {error}"
            )

        try:
            report_builder.export_to_csv(
                risk_report,
                str(csv_path)
            )

            csv_created = (
                csv_path.exists()
                and csv_path.stat().st_size > 0
            )

            runner.check(
                "CSV-отчёт сохраняется",
                csv_created,
                f"Путь: {csv_path}"
            )

        except Exception as error:
            runner.check(
                "CSV-отчёт сохраняется",
                False,
                f"{type(error).__name__}: {error}"
            )

        previous_directory = os.getcwd()

        try:
            os.chdir(temp_path)

            report_builder.save_charts()

            expected_charts = [
                "transaction_statuses.png",
                "clients_balance.png",
                "balance_history.png"
            ]

            chart_results = {
                chart_name: (
                    Path(chart_name).exists()
                    and Path(chart_name).stat().st_size > 0
                )
                for chart_name in expected_charts
            }

            runner.check(
                "Создаётся круговая диаграмма",
                chart_results[
                    "transaction_statuses.png"
                ],
                (
                    "Файл: "
                    "transaction_statuses.png"
                )
            )

            runner.check(
                "Создаётся столбчатая диаграмма",
                chart_results[
                    "clients_balance.png"
                ],
                "Файл: clients_balance.png"
            )

            runner.check(
                "Создаётся график движения баланса",
                chart_results[
                    "balance_history.png"
                ],
                "Файл: balance_history.png"
            )

        except Exception as error:
            runner.check(
                "Графики сохраняются",
                False,
                f"{type(error).__name__}: {error}"
            )

        finally:
            os.chdir(previous_directory)


# ==========================================================
# ЗАПУСК
# ==========================================================


def main():
    runner = TestRunner()

    print("=" * 70)
    print("ПОЛНАЯ ПРОВЕРКА БАНКОВСКОГО ПРОЕКТА")
    print("ТРЕБОВАНИЯ ДНЕЙ 1–7")
    print("=" * 70)

    test_day_1(runner)
    test_day_2(runner)
    test_day_3(runner)
    test_day_4(runner)
    test_day_5(runner)

    demo_data = build_day_6_demo(
        runner
    )

    test_day_7(
        runner,
        demo_data
    )

    runner.summary()


if __name__ == "__main__":
    main()