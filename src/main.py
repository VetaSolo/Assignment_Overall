from models import BankAccount, AccountFrozenError, AccountClosedError, InvalidOperationError, InsufficientFundsError, PremiumAccount, InvestmentAccount, SavingsAccount, Bank, Client

def main():

    active_account = BankAccount(
        None,
        "Иван",
        10000,
        BankAccount.ACTIVE,
        "RUB"
    )

    frozen_account = BankAccount(
        None,
        "Анна",
        5000,
        BankAccount.FROZEN,
        "RUB"
    )


    print(active_account)
    print(frozen_account)


    try:
        frozen_account.deposit(1000)

    except AccountFrozenError as error:
        print(error)


    active_account.deposit(5000)
    active_account.withdraw(2000)

    print(active_account)

    bank = BankAccount(
        None,
        "Банк",
        1000000,
        BankAccount.ACTIVE,
        "RUB"
    )

    premium_account = PremiumAccount(
        None,
        "Премиум", 
        50000,
        BankAccount.ACTIVE,
        "RUB",
        10000,
        5000, 
        2
    )   
    investment_account = InvestmentAccount(
        None,
        "Мария Соколова",
        300000,
        BankAccount.ACTIVE,
        "RUB",
        {
            "stocks": 150000,
            "bonds": 100000,
            "etf": 50000
        }
    )

    savings_account = SavingsAccount(
        None,
        "Сбережения",
        200000,
        BankAccount.ACTIVE,
        "RUB",
        2000,
        5
    )

    print(bank)
    bank.withdraw(100000)
    print(bank.get_account_info())


    print(premium_account)
    premium_account.withdraw(5000)
    print(premium_account.get_account_info())

    print(investment_account)
    investment_account.withdraw(500)
    print(investment_account.get_account_info())

    print(savings_account)
    savings_account.withdraw(5000)
    savings_account.apply_monthly_interest()
    print(savings_account.get_account_info())


    bank = Bank()

    # Клиенты
    client1 = Client(
        "Иван Иванов",
        "ACTIVE",
        "ivan@mail.com",
        25,
        "1234"
    )

    client2 = Client(
        "Анна Петрова",
        "ACTIVE",
        "anna@mail.com",
        30,
        "5678"
    )

    bank.add_client(client1)
    bank.add_client(client2)

    # Счета
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

    # Открываем счета
    bank.open_account(client1, account1)
    bank.open_account(client1, account2)
    bank.open_account(client2, account3)

    print("----- СЧЕТА -----")
    print(account1)
    print(account2)
    print(account3)

    # Проверяем поиск счетов
    print("\n----- СЧЕТА ИВАНА -----")
    accounts = bank.search_accounts(
        "Иван Иванов"
    )

    for account in accounts:
        print(account)

    # Авторизация
    print("\n----- ВХОД -----")

    print(
        bank.authenticate_client(
            client1,
            "1234"
        )
    )


    # 3 неправильных входа
    print(
        bank.authenticate_client(
            client2,
            "0000"
        )
    )

    print(
        bank.authenticate_client(
            client2,
            "1111"
        )
    )

    try:
        bank.authenticate_client(
            client2,
            "2222"
        )
    except InvalidOperationError as error:
        print(error)
    print(
        "Анна заблокирована:",
        client2.is_blocked
    )

    # Заморозка счета
    print("\n----- ЗАМОРОЗКА -----")
    bank.freeze_account(account1)
    print(account1)

    try:
        account1.withdraw(1000)

    except AccountFrozenError as error:
        print(error)



    # Подозрительные действия
    print("\n----- ЛОГ -----")

    for action in bank.suspicious_actions:
        print(action)


if __name__ == "__main__":
    main()