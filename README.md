# Assignment_Overall

Учебный проект банковской системы на Python

## Возможности

- 👤 Управление клиентами банка
- 💳 Поддержка различных типов счетов:
  - BankAccount
  - PremiumAccount
  - SavingsAccount
  - InvestmentAccount
- 💸 Выполнение банковских транзакций
- 📋 Очередь обработки транзакций
- ⚠️ Анализ подозрительных операций (Risk Analyzer)
- 📝 Аудит и логирование операций
- 📊 Генерация отчетов по банку, клиентам и рискам
- 📈 Построение графиков статистики
- 📄 Экспорт отчетов в JSON и CSV
- ✅ Валидация данных и обработка пользовательских исключений

## Структура проекта

```
Assignment_Overall/
│
├── src/
│   ├── main.py
│   ├── models.py
│   └── utils.py
│
├── bank_report.json
├── risk_report.csv
├── transaction_statuses.png
├── clients_balance.png
└── balance_history.png
```

## Запуск

```bash
python src/main.py
```

## Результат работы

После запуска автоматически:

- создаются клиенты и счета;
- генерируются тестовые транзакции;
- выполняется обработка операций;
- анализируются риски;
- выводится статистика;
- формируются отчеты;
- сохраняются графики и файлы:
  - `bank_report.json`
  - `risk_report.csv`
  - `transaction_statuses.png`
  - `clients_balance.png`
  - `balance_history.png`