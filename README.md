# swiss-budget-tools

## Problem
Many European and Swiss banks don't allow API access, making it difficult to sync your accounts with a centralized budget tool, such as [LunchMoney](https://lunchmoney.app/?refer=x01525r3)  
(please use that referral code if you sign up!)

## Solution
This CLI app takes an account download file from `[Valiant, N26 (deprecated), Wise]` and outputs a CSV file containing cleaned transaction data, making it super-easy to upload on a regular basis and track your spending!

## Usage
```
python main.py --source [wise, valiant, n26] --input ~/path-to-input.csv --output ~/path-to-output --include_bank_fees true
```
`--include_bank_fees` works when the input file is a CAMT (SEPA XML) file and detects differences in the charged amount vs. the account debit amount most likely due to bank fees, such as a foreign transaction fee. If this option is true, the amount exported for the transaction will be the charge amount, the description will reflect the bank fee, and the total bank fees will be bundled in a new transaction line item.

## Examples

### Description Change
|State|Description|Amount|
|---|---|---|
|Before|Debitkarten-Einkauf 18.11.2022 17:14 Relay Lausanne CFF Kartennummer: 1234567812345678|-9.85 CHF|
|After|Relay Lausanne CFF|-9.85 CHF|

### Bank Fees
|State|Description|Amount|
|---|---|---|
|Before|GITHUB|-9.85 CHF|
|After|GITHUB (excl. 0.13 bank fee)|-9.72 CHF|
|After|21 probable bank fees from 2022-10-27 to 2022-11-29|-13.02|

### Transfer excludes creditor/debtor
|State|Description|Amount|
|---|---|---|
|Before|Vergütung|-500.59 CHF|
|After|Migros Klubschule|-500.59 CHF|
