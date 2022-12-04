def parse_n26_csv(df):
    # Ordered header dict from: "Date","Payee","Account number","Transaction type","Payment reference","Amount (EUR)","Amount (Foreign Currency)","Type Foreign Currency","Exchange Rate"
    HEADERS = {
        "DATE": "Date",
        "PAYEE": "Payee",
        "ACCOUNT_NUMBER": "Account number",
        "TRANSACTION_TYPE": "Transaction type",
        "PAYMENT_REFERENCE": "Payment reference",
        "AMOUNT_EUR": "Amount (EUR)",
        "AMOUNT_FOREIGN_CURRENCY": "Amount (Foreign Currency)",
        "TYPE_FOREIGN_CURRENCY": "Type Foreign Currency",
        "EXCHANGE_RATE": "Exchange Rate",
    }

    # Assert headers match DF headers
    assert df.columns.tolist() == list(HEADERS.values())
    # Keep only Date, Description, Amount
    df = df[
        [HEADERS["DATE"], HEADERS["PAYEE"], HEADERS["AMOUNT_EUR"]]
    ].copy()  # Include copy to avoid SettingWithCopyWarning

    # Lowercase column names to be detected by lunchmomey
    df.columns = df.columns.str.lower()

    return df
