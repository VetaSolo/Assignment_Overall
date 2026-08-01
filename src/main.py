from models import BankAccount, AccountFrozenError, AccountClosedError, InvalidOperationError, InsufficientFundsError, PremiumAccount, InvestmentAccount, SavingsAccount

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



if __name__ == "__main__":
    main()