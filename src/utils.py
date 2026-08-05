from decimal import Decimal
import json
import csv
import matplotlib.pyplot as plt
from collections import Counter

from models import Transaction


class ReportBuilder:

    def __init__(self, bank, transactions, risk_analyzer):
        self.bank = bank
        self.transactions = transactions
        self.risk_analyzer = risk_analyzer
    # ОТЧЕТ ПО КЛИЕНТУ

    def client_report(self, client):
        completed = [
            t for t in client.transactions
            if t.status == Transaction.COMPLETED
        ]

        return {
            "client": client.full_name,
            "id": client.id,
            "status": client.status,

            "accounts": [
                {
                    "id": acc.id,
                    "balance": acc._balance,
                    "currency": acc.currency
                }
                for acc in client.accounts
            ],

            "transactions_count": len(client.transactions),

            "completed_transactions": len(completed)
        }

    # ОТЧЕТ ПО БАНКУ

    def bank_report(self):
        completed = len(
            [
                t for t in self.transactions
                if t.status == "COMPLETED"
            ]
        )
        failed = len(
            [
                t for t in self.transactions
                if t.status == "FAILED"
            ]
        )
        return {

            "clients":
                len(self.bank.clients),

            "accounts":
                len(self.bank.accounts),

            "total_balance":
                self.bank.get_total_balance(),

            "transactions":
                len(self.transactions),

            "completed":
                completed,

            "failed":
                failed
        }

    # ОТЧЕТ ПО РИСКАМ

    def risk_report(self):

        suspicious = (
            self.risk_analyzer
            .get_suspicious_operations()
        )
        result=[]
        for item in suspicious:

            result.append(
                {
                    "transaction":
                        item["transaction"].id,

                    "risk":
                        item["risk"],

                    "reason":
                        item["reason"]
                }
            )

        return result

    # JSON

    def export_to_json(self, data, filename):
        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False,
                default=str
            )

    # CSV

    def export_to_csv(self, data, filename):
        if not data:
            return
        with open(
            filename,
            "w",
            encoding="utf-8",
            newline=""
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=data[0].keys()
            )
            writer.writeheader()
            writer.writerows(data)

    # ГРАФИКИ

    def save_charts(self):

        # ---------------------------
        # 1. Статусы транзакций
        # круговая диаграмма
        # ---------------------------

        statuses = Counter(
            [
                t.status
                for t in self.transactions
            ]
        )
        plt.figure(figsize=(6,6))

        plt.pie(
            statuses.values(),
            labels=statuses.keys(),
            autopct="%1.1f%%"
        )

        plt.title(
            "Transaction statuses"
        )

        plt.savefig(
            "transaction_statuses.png"
        )

        plt.close()

        # ---------------------------
        # 2. Баланс клиентов
        # столбчатый график
        # ---------------------------

        clients=[]
        balances=[]

        for client in self.bank.clients:

            balance=sum(
                account._balance
                for account in self.bank.accounts
                if account.owner_data.id == client.id
            )

            clients.append(
                client.full_name
            )

            balances.append(
                balance
            )

        plt.figure(figsize=(10,5))

        plt.bar(
            clients,
            balances
        )

        plt.xticks(
            rotation=45
        )

        plt.title(
            "Clients balance"
        )

        plt.tight_layout()

        plt.savefig(
            "clients_balance.png"
        )


        plt.close()

        # ---------------------------
        # 3. Движение баланса
        # ---------------------------
        final_balance_rub = Decimal("0")

        for account in self.bank.accounts:
            final_balance_rub += self.bank.convert_to_rub(
                account._balance,
                account.currency
            )

        # Сначала определяем, насколько баланс изменился
        # за все успешно выполненные операции.
        total_change_rub = Decimal("0")

        for transaction in self.transactions:
            if transaction.status != Transaction.COMPLETED:
                continue

            amount_rub = self.bank.convert_to_rub(
                transaction.amount,
                transaction.currency
            )

            if transaction.transaction_type == Transaction.DEPOSIT:
                total_change_rub += amount_rub

            elif transaction.transaction_type == Transaction.WITHDRAW:
                total_change_rub -= amount_rub

            elif transaction.transaction_type == Transaction.TRANSFER:
                # Основная сумма просто перемещается между счетами.
                # Общий баланс уменьшается только на комиссию.
                commission_rub = self.bank.convert_to_rub(
                    transaction.commission,
                    transaction.currency
                )

                total_change_rub -= commission_rub

        # Восстанавливаем баланс до начала обработки транзакций.
        current_balance_rub = (
            final_balance_rub - total_change_rub
        )

        # Первая точка — баланс до первой транзакции.
        balance_history = [
            float(current_balance_rub)
        ]

        for transaction in self.transactions:
            if transaction.status == Transaction.COMPLETED:
                amount_rub = self.bank.convert_to_rub(
                    transaction.amount,
                    transaction.currency
                )

                if transaction.transaction_type == Transaction.DEPOSIT:
                    current_balance_rub += amount_rub

                elif transaction.transaction_type == Transaction.WITHDRAW:
                    current_balance_rub -= amount_rub

                elif transaction.transaction_type == Transaction.TRANSFER:
                    commission_rub = self.bank.convert_to_rub(
                        transaction.commission,
                        transaction.currency
                    )

                    current_balance_rub -= commission_rub

            # Для неуспешной операции баланс не меняется,
            # но точка всё равно добавляется.
            balance_history.append(
                float(current_balance_rub)
            )

        plt.figure(figsize=(10, 5))

        plt.plot(
            range(len(balance_history)),
            balance_history,
            marker="o",
            markersize=3
        )

        plt.title(
            "Total bank balance movement"
        )

        plt.xlabel(
            "Transactions"
        )

        plt.ylabel(
            "Balance, RUB"
        )

        plt.grid(
            alpha=0.3
        )

        plt.tight_layout()

        plt.savefig(
            "balance_history.png"
        )

        plt.close()