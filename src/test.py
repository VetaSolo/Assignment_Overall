from decimal import Decimal

from models import *


def print_result(test_name, passed, details=""):
    status = "✅ ПРОЙДЕН" if passed else "❌ НЕ ПРОЙДЕН"

    print(f"\n{status}: {test_name}")

    if details:
        print(details)
from decimal import Decimal

from models import *


def print_result(test_name, passed, details=""):
    status = "✅ ПРОЙДЕН" if passed else "❌ НЕ ПРОЙДЕН"

    print(f"\n{status}: {test_name}")

    if details:
        print(details)


def main():

    # ТЕСТ 1. PremiumAccount
    # ТЕСТ 2. Риск-профиль клиента
    # ТЕСТ 3. Новый получатель
    # ТЕСТ 4. Комиссия за перевод
    # ТЕСТ 5. Рейтинг клиентов

    print("=" * 70)
    print("ПРОВЕРКА ИСПРАВЛЕНИЙ ПРОЕКТА")
    print("=" * 70)

    # ==========================================================
    # Общие объекты
    # ==========================================================

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

    # Отключаем временное ограничение только для тестирования.
    bank.check_operation_time = lambda: None

    client_1 = Client(
        "Иван Иванов",
        "ACTIVE",
        "+79990000001",
        30,
        "1234"
    )

    client_2 = Client(
        "Анна Петрова",
        "ACTIVE",
        "+79990000002",
        28,
        "1234"
    )

    client_3 = Client(
        "Петр Смирнов",
        "ACTIVE",
        "+79990000003",
        35,
        "1234"
    )

    bank.add_client(client_1)
    bank.add_client(client_2)
    bank.add_client(client_3)

    # ==========================================================
    # ТЕСТ 1
    # PremiumAccount:
    # - нет AttributeError;
    # - проверяется комиссия;
    # - работает овердрафт;
    # - проверяется withdraw_limit.
    # ==========================================================

    print("\n" + "=" * 70)
    print("ТЕСТ 1. PREMIUM ACCOUNT")
    print("=" * 70)

    premium = PremiumAccount(
        None,
        client_1,
        1000,
        BankAccount.ACTIVE,
        "RUB",
        1500,   # withdraw_limit
        500,    # overdraft_limit
        2       # комиссия 2%
    )

    bank.open_account(
        client_1,
        premium
    )

    initial_balance = premium._balance

    try:
        premium.withdraw(1200)

        expected_commission = (
            Decimal("1200")
            * Decimal("2")
            / Decimal("100")
        )

        expected_balance = (
            initial_balance
            - Decimal("1200")
            - expected_commission
        )

        passed = premium._balance == expected_balance

        print_result(
            "PremiumAccount использует комиссию и овердрафт",
            passed,
            (
                f"Начальный баланс: {initial_balance}\n"
                f"Снятие: 1200\n"
                f"Комиссия: {expected_commission}\n"
                f"Ожидаемый баланс: {expected_balance}\n"
                f"Фактический баланс: {premium._balance}"
            )
        )

    except AttributeError as error:
        print_result(
            "PremiumAccount не обращается к withdraw_fee",
            False,
            f"Получен AttributeError: {error}"
        )

    except Exception as error:
        print_result(
            "PremiumAccount использует комиссию и овердрафт",
            False,
            f"Неожиданная ошибка: {type(error).__name__}: {error}"
        )

    # Проверка лимита снятия

    try:
        premium.withdraw(1600)

        print_result(
            "PremiumAccount проверяет withdraw_limit",
            False,
            "Снятие выше лимита ошибочно разрешено"
        )

    except InvalidOperationError as error:
        print_result(
            "PremiumAccount проверяет withdraw_limit",
            True,
            f"Операция правильно отклонена: {error}"
        )

    except Exception as error:
        print_result(
            "PremiumAccount проверяет withdraw_limit",
            False,
            (
                "Ожидался InvalidOperationError, "
                f"получен {type(error).__name__}: {error}"
            )
        )

    # ==========================================================
    # ТЕСТ 2
    # get_client_risk_profile() не падает с TypeError.
    # ==========================================================

    print("\n" + "=" * 70)
    print("ТЕСТ 2. РИСК-ПРОФИЛЬ КЛИЕНТА")
    print("=" * 70)

    risk_for_profile = RiskAnalyzer()

    sender_account = BankAccount(
        None,
        client_1,
        1000000,
        BankAccount.ACTIVE,
        "RUB"
    )

    receiver_account = BankAccount(
        None,
        client_2,
        10000,
        BankAccount.ACTIVE,
        "RUB"
    )

    risk_transaction = Transaction(
        Transaction.TRANSFER,
        600000,
        "RUB",
        sender_account,
        receiver_account
    )

    risk_for_profile.analyze(
        risk_transaction
    )

    try:
        profile = (
            risk_for_profile
            .get_client_risk_profile()
        )

        client_found = client_1 in profile

        passed = (
            isinstance(profile, dict)
            and client_found
            and profile[client_1]["count"] == 1
        )

        print_result(
            "get_client_risk_profile() работает",
            passed,
            f"Полученный профиль: {profile}"
        )

    except TypeError as error:
        print_result(
            "get_client_risk_profile() работает",
            False,
            f"Метод всё ещё падает с TypeError: {error}"
        )

    except Exception as error:
        print_result(
            "get_client_risk_profile() работает",
            False,
            f"Неожиданная ошибка: {type(error).__name__}: {error}"
        )

    # ==========================================================
    # ТЕСТ 3
    # Первый перевод новому получателю считается подозрительным.
    # ==========================================================

    print("\n" + "=" * 70)
    print("ТЕСТ 3. НОВЫЙ ПОЛУЧАТЕЛЬ")
    print("=" * 70)

    new_receiver_risk = RiskAnalyzer()

    new_receiver_transaction = Transaction(
        Transaction.TRANSFER,
        1000,
        "RUB",
        sender_account,
        receiver_account
    )

    risk_level, reasons = (
        new_receiver_risk.analyze(
            new_receiver_transaction
        )
    )

    has_new_account_reason = any(
        "нов" in reason.lower()
        and (
            "сч" in reason.lower()
            or "получател" in reason.lower()
        )
        for reason in reasons
    )

    print_result(
        "Первый новый получатель отмечается как риск",
        has_new_account_reason,
        (
            f"Уровень риска: {risk_level}\n"
            f"Причины: {reasons}"
        )
    )

    # Повторный перевод тому же получателю
    repeat_transaction = Transaction(
        Transaction.TRANSFER,
        1000,
        "RUB",
        sender_account,
        receiver_account
    )

    repeat_risk, repeat_reasons = (
        new_receiver_risk.analyze(
            repeat_transaction
        )
    )

    repeated_new_reason = any(
        "нов" in reason.lower()
        and (
            "сч" in reason.lower()
            or "получател" in reason.lower()
        )
        for reason in repeat_reasons
    )

    print_result(
        "Повторный получатель уже не считается новым",
        not repeated_new_reason,
        (
            f"Уровень риска: {repeat_risk}\n"
            f"Причины: {repeat_reasons}"
        )
    )

    # ==========================================================
    # ТЕСТ 4
    # Комиссия:
    # - внутренний перевод между счетами одного клиента — 0%;
    # - перевод другому клиенту — 2%.
    # ==========================================================

    print("\n" + "=" * 70)
    print("ТЕСТ 4. КОМИССИЯ ЗА ПЕРЕВОД")
    print("=" * 70)

    same_client_account_1 = BankAccount(
        None,
        client_2,
        10000,
        BankAccount.ACTIVE,
        "RUB"
    )

    same_client_account_2 = BankAccount(
        None,
        client_2,
        1000,
        BankAccount.ACTIVE,
        "RUB"
    )

    external_account = BankAccount(
        None,
        client_3,
        1000,
        BankAccount.ACTIVE,
        "RUB"
    )

    internal_transfer = Transaction(
        Transaction.TRANSFER,
        1000,
        "RUB",
        same_client_account_1,
        same_client_account_2
    )

    external_transfer = Transaction(
        Transaction.TRANSFER,
        1000,
        "RUB",
        same_client_account_1,
        external_account
    )

    internal_commission = (
        processor.calculate_commission(
            internal_transfer
        )
    )

    external_commission = (
        processor.calculate_commission(
            external_transfer
        )
    )

    print_result(
        "Внутренний перевод выполняется без комиссии",
        internal_commission == Decimal("0"),
        f"Комиссия: {internal_commission}"
    )

    print_result(
        "Внешний перевод облагается комиссией 2%",
        external_commission == Decimal("20"),
        (
            f"Сумма перевода: 1000\n"
            f"Ожидаемая комиссия: 20\n"
            f"Фактическая комиссия: {external_commission}"
        )
    )

    # Проверка реального внутреннего перевода через процессор

    internal_sender_balance = (
        same_client_account_1._balance
    )

    internal_receiver_balance = (
        same_client_account_2._balance
    )

    queue.add_transaction(
        internal_transfer
    )

    processor.process_transactions()

    expected_sender_balance = (
        internal_sender_balance
        - Decimal("1000")
    )

    expected_receiver_balance = (
        internal_receiver_balance
        + Decimal("1000")
    )

    internal_processed_correctly = (
        internal_transfer.status
        == Transaction.COMPLETED
        and same_client_account_1._balance
        == expected_sender_balance
        and same_client_account_2._balance
        == expected_receiver_balance
    )

    print_result(
        "Внутренний перевод не уменьшает баланс комиссией",
        internal_processed_correctly,
        (
            f"Статус: {internal_transfer.status}\n"
            f"Баланс отправителя: "
            f"{same_client_account_1._balance}\n"
            f"Баланс получателя: "
            f"{same_client_account_2._balance}\n"
            f"Комиссия: {internal_transfer.commission}"
        )
    )

    # ==========================================================
    # ТЕСТ 5
    # Рейтинг клиентов конвертирует валюты в RUB.
    # ==========================================================

    print("\n" + "=" * 70)
    print("ТЕСТ 5. РЕЙТИНГ КЛИЕНТОВ")
    print("=" * 70)

    ranking_bank = Bank()

    rub_client = Client(
        "Клиент RUB",
        "ACTIVE",
        "+79990000101",
        30,
        "1234"
    )

    usd_client = Client(
        "Клиент USD",
        "ACTIVE",
        "+79990000102",
        30,
        "1234"
    )

    eur_client = Client(
        "Клиент EUR",
        "ACTIVE",
        "+79990000103",
        30,
        "1234"
    )

    ranking_bank.add_client(rub_client)
    ranking_bank.add_client(usd_client)
    ranking_bank.add_client(eur_client)

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

    eur_account = BankAccount(
        None,
        eur_client,
        1500,
        BankAccount.ACTIVE,
        "EUR"
    )

    ranking_bank.open_account(
        rub_client,
        rub_account
    )

    ranking_bank.open_account(
        usd_client,
        usd_account
    )

    ranking_bank.open_account(
        eur_client,
        eur_account
    )

    try:
        ranking = (
            ranking_bank.get_clients_ranking()
        )

        print("\nПолученный рейтинг:")

        for position, item in enumerate(
            ranking,
            start=1
        ):
            print(
                f"{position}. "
                f"{item['client']}: "
                f"{item['balance']} "
                f"{item.get('currency', 'валюта не указана')}"
            )

        all_rub = all(
            item.get("currency") == "RUB"
            for item in ranking
        )

        # Проверяем конкретные результаты по курсам Bank.
        expected_balances = {
            "Клиент RUB":
                ranking_bank.convert_to_rub(
                    Decimal("100000"),
                    "RUB"
                ),

            "Клиент USD":
                ranking_bank.convert_to_rub(
                    Decimal("2000"),
                    "USD"
                ),

            "Клиент EUR":
                ranking_bank.convert_to_rub(
                    Decimal("1500"),
                    "EUR"
                )
        }

        actual_balances = {
            item["client"]: item["balance"]
            for item in ranking
        }

        balances_correct = (
            actual_balances
            == expected_balances
        )

        sorted_correctly = (
            ranking
            == sorted(
                ranking,
                key=lambda item: item["balance"],
                reverse=True
            )
        )

        print_result(
            "Рейтинг конвертирует все валюты в RUB",
            all_rub and balances_correct,
            (
                f"Ожидаемые суммы: {expected_balances}\n"
                f"Фактические суммы: {actual_balances}"
            )
        )

        print_result(
            "Рейтинг отсортирован по RUB-эквиваленту",
            sorted_correctly
        )

    except AttributeError as error:
        print_result(
            "Рейтинг конвертирует валюты",
            False,
            (
                "В классе Bank отсутствует convert_to_rub(): "
                f"{error}"
            )
        )

    except Exception as error:
        print_result(
            "Рейтинг конвертирует валюты",
            False,
            f"Ошибка: {type(error).__name__}: {error}"
        )

    print("\n" + "=" * 70)
    print("ПРОВЕРКА ЗАВЕРШЕНА")
    print("=" * 70)


if __name__ == "__main__":
    main()