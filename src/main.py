from models import BankAccount, AccountFrozenError, AccountClosedError, InvalidOperationError, InsufficientFundsError, PremiumAccount, InvestmentAccount, SavingsAccount, Bank, Client, Transaction, TransactionProcessor, TransactionProcessor, TransactionQueue, TransactionProcessor


def main():
    # -----------------------------
    # Создание банка
    # -----------------------------
    bank = Bank()

    # -----------------------------
    # Клиенты
    # -----------------------------
    ivan = Client(
        "Иван Иванов",
        "ACTIVE",
        "+79990001111",
        30,
        "1234"
    )

    anna = Client(
        "Анна Петрова",
        "ACTIVE",
        "+79990002222",
        27,
        "5678"
    )

    bank.add_client(ivan)
    bank.add_client(anna)

    # -----------------------------
    # Счета
    # -----------------------------
    account1 = BankAccount(
        None,
        "Иван Иванов",
        100000,
        BankAccount.ACTIVE,
        "RUB"
    )

    account2 = SavingsAccount(
        None,
        "Иван Иванов",
        50000,
        BankAccount.ACTIVE,
        "RUB",
        10000,
        5
    )

    account3 = PremiumAccount(
        None,
        "Анна Петрова",
        200000,
        BankAccount.ACTIVE,
        "USD",
        50000,
        10000,
        2
    )

    account4 = InvestmentAccount(
        None,
        "Анна Петрова",
        300000,
        BankAccount.ACTIVE,
        "EUR",
        {
            "stocks": 150000,
            "bonds": 100000,
            "etf": 50000
        }
    )

    bank.open_account(ivan, account1)
    bank.open_account(ivan, account2)
    bank.open_account(anna, account3)
    bank.open_account(anna, account4)

    # -----------------------------
    # Очередь
    # -----------------------------
    queue = TransactionQueue()

    # -----------------------------
    # 10 транзакций
    # -----------------------------

    # 1
    t1 = Transaction(
        Transaction.DEPOSIT,
        10000,
        "RUB",
        account1,
        account1,
        priority=1
    )

    # 2
    t2 = Transaction(
        Transaction.WITHDRAW,
        5000,
        "RUB",
        account1,
        account1,
        priority=1
    )

    # 3
    t3 = Transaction(
        Transaction.TRANSFER,
        15000,
        "RUB",
        account1,
        account2,
        priority=2
    )

    # 4
    t4 = Transaction(
        Transaction.TRANSFER,
        20000,
        "RUB",
        account1,
        account3,
        priority=3
    )

    # 5
    t5 = Transaction(
        Transaction.TRANSFER,
        30000,
        "USD",
        account3,
        account4,
        priority=2
    )

    # 6
    t6 = Transaction(
        Transaction.WITHDRAW,
        1000,
        "EUR",
        account4,
        account4,
        priority=1
    )

    # 7
    t7 = Transaction(
        Transaction.DEPOSIT,
        25000,
        "USD",
        account3,
        account3,
        priority=1
    )

    # 8
    t8 = Transaction(
        Transaction.TRANSFER,
        500000,
        "RUB",
        account1,
        account3,
        priority=5
    )

    # 9
    bank.freeze_account(account2)

    t9 = Transaction(
        Transaction.TRANSFER,
        1000,
        "RUB",
        account1,
        account2,
        priority=4
    )

    # 10
    t10 = Transaction(
        Transaction.TRANSFER,
        7000,
        "USD",
        account3,
        account1,
        priority=2
    )

    # -----------------------------
    # Добавляем в очередь
    # -----------------------------
    for transaction in [
        t1,
        t2,
        t3,
        t4,
        t5,
        t6,
        t7,
        t8,
        t9,
        t10
    ]:
        queue.add_transaction(transaction)

    print(queue)

    # -----------------------------
    # Обработка
    # -----------------------------
    processor = TransactionProcessor(queue)

    processor.process_transactions()

    # -----------------------------
    # Итоги
    # -----------------------------
    print("\n------ СТАТУСЫ ------")

    for transaction in [
        t1,
        t2,
        t3,
        t4,
        t5,
        t6,
        t7,
        t8,
        t9,
        t10
    ]:
        print(
            transaction.id,
            transaction.transaction_type,
            transaction.status,
            transaction.failure_reason
        )

    print("\n------ СЧЕТА ------")
    print(account1)
    print(account2)
    print(account3)
    print(account4)

    print("\n------ ЛОГ ОШИБОК ------")

    for error in processor.error_log:
        print(error)

if __name__ == "__main__":
    main()