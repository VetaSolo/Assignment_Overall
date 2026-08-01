from models import BankAccount, AccountFrozenError, AccountClosedError, InvalidOperationError, InsufficientFundsError

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


if __name__ == "__main__":
    main()