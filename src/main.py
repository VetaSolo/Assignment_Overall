from models import *
import random

from utils import ReportBuilder


def money(value):
    """
    Красивый вывод денежных значений
    """
    return f"{float(value):,.2f}".replace(",", " ")


def main():

    # ===============================
    # Создание банка и сервисов
    # ===============================

    bank = Bank()

    audit = AuditLog()
    risk = RiskAnalyzer()
    queue = TransactionQueue()

    processor = TransactionProcessor(
        queue,
        risk,
        audit,
        bank
    )


    # ===============================
    # Клиенты
    # ===============================

    clients = []

    names = [
        "Иван Иванов",
        "Анна Петрова",
        "Мария Соколова",
        "Петр Смирнов",
        "Елена Орлова",
        "Алексей Волков"
    ]


    for name in names:

        client = Client(
            name,
            "ACTIVE",
            "+79990000000",
            random.randint(20, 60),
            "1234"
        )

        bank.add_client(client)
        clients.append(client)


    # ===============================
    # Счета
    # ===============================

    accounts = []


    for client in clients:

        account = BankAccount(
            None,
            client,
            random.randint(50000, 300000),
            BankAccount.ACTIVE,
            "RUB"
        )

        bank.open_account(
            client,
            account
        )

        accounts.append(account)


    premium = PremiumAccount(
        None,
        clients[1],
        500000,
        BankAccount.ACTIVE,
        "USD",
        50000,
        10000,
        2
    )

    bank.open_account(
        clients[1],
        premium
    )

    accounts.append(premium)


    savings = SavingsAccount(
        None,
        clients[3],
        100000,
        BankAccount.ACTIVE,
        "RUB",
        10000,
        5
    )

    bank.open_account(
        clients[3],
        savings
    )

    accounts.append(savings)



    investment = InvestmentAccount(
        None,
        clients[2],
        300000,
        BankAccount.ACTIVE,
        "EUR",
        {
            "stocks": 150000,
            "bonds": 100000,
            "etf": 50000
        }
    )

    bank.open_account(
        clients[2],
        investment
    )

    accounts.append(investment)



    premium2 = PremiumAccount(
        None,
        clients[4],
        700000,
        BankAccount.ACTIVE,
        "RUB",
        100000,
        20000,
        1
    )

    bank.open_account(
        clients[4],
        premium2
    )

    accounts.append(premium2)



    # ===============================
    # Создание транзакций
    # ===============================

    transactions = []


    for i in range(40):

        sender = random.choice(accounts)
        receiver = random.choice(accounts)


        if i < 30:
            amount = random.randint(
                1000,
                30000
            )

        else:
            amount = random.randint(
                200000,
                1000000
            )


        transaction = Transaction(
            Transaction.TRANSFER,
            amount,
            sender.currency,
            sender,
            receiver,
            priority=random.randint(1, 5)
        )


        transactions.append(transaction)

        queue.add_transaction(
            transaction
        )



    # опасная операция

    danger_transaction = Transaction(
        Transaction.TRANSFER,
        1000000,
        "RUB",
        accounts[0],
        accounts[1],
        priority=10
    )

    transactions.append(
        danger_transaction
    )

    queue.add_transaction(
        danger_transaction
    )



    # замороженный счет

    bank.freeze_account(
        accounts[2]
    )


    bad_transaction = Transaction(
        Transaction.TRANSFER,
        5000,
        "RUB",
        accounts[0],
        accounts[2]
    )


    transactions.append(
        bad_transaction
    )

    queue.add_transaction(
        bad_transaction
    )



    print(queue)



    # ===============================
    # Обработка операций
    # ===============================

    processor.process_transactions()



    # ===============================
    # Счета клиента
    # ===============================

    print("\n----- СЧЕТА ИВАНА -----")

    for account in accounts:

        if account.owner_data.full_name == "Иван Иванов":
            print(account)



    print("\n----- ИСТОРИЯ ИВАНА -----")

    clients[0].show_history()

    print(
        f"Всего операций: {len(clients[0].transactions)}"
    )



    # ===============================
    # Risk
    # ===============================

    print("\n----- RISK -----")


    for item in risk.get_suspicious_operations():

        print(
            item["transaction"].id,
            item["risk"],
            item["reason"]
        )



    # ===============================
    # Клиенты с максимальным балансом
    # ===============================

    print("\n----- TOP CLIENTS -----")


    for client in bank.get_clients_ranking()[:3]:

        print(
            client["client"],
            "|",
            money(client["balance"]),
            "RUB"
        )



    # ===============================
    # Статистика
    # ===============================

    print("\n----- TRANSACTION STATISTICS -----")

    print(
        bank.transaction_statistics(
            transactions
        )
    )


    print("\n----- TOTAL BALANCE -----")

    balances = bank.get_total_balance()

    for currency, amount in balances.items():
        print(f"{amount:,.2f} {currency}".replace(",", " "))


    # ===============================
    # Reports
    # ===============================

    report = ReportBuilder(
        bank,
        transactions,
        risk
    )



    print("\n----- BANK REPORT -----")

    bank_report = report.bank_report()

    bank_report["total_balance"] = {
        currency: money(amount)
        for currency, amount in bank.get_total_balance().items()
    }

    print(bank_report)



    print("\n----- CLIENT REPORT -----")


    ivan_report = report.client_report(
        clients[0]
    )


    for account in ivan_report["accounts"]:

        account["balance"] = money(
            account["balance"]
        )


    print(
        ivan_report
    )



    print("\n----- RISK REPORT -----")


    risk_report = report.risk_report()


    for item in risk_report:

        print(item)



    # ===============================
    # Export
    # ===============================

    report.export_to_json(
        bank_report,
        "bank_report.json"
    )


    report.export_to_csv(
        risk_report,
        "risk_report.csv"
    )


    # ===============================
    # Charts
    # ===============================

    report.save_charts()


    print(
        "\nОтчеты сохранены:"
    )

    print(
        "- bank_report.json"
    )

    print(
        "- risk_report.csv"
    )

    print(
        "- transaction_statuses.png"
    )

    print(
        "- clients_balance.png"
    )

    print(
        "- balance_history.png"
    )



if __name__ == "__main__":
    main()
