def parse_wise_csv(df):
    # Ordered header dict from: "TransferWise ID",Date,Amount,Currency,Description,"Payment Reference","Running Balance","Exchange From","Exchange To","Exchange Rate","Payer Name","Payee Name","Payee Account Number",Merchant,"Card Last Four Digits","Card Holder Full Name",Attachment,Note,"Total fees"
    HEADERS = {
        "WISE_ID": "TransferWise ID",
        "DATE": "Date",
        "AMOUNT": "Amount",
        "CURRENCY": "Currency",
        "DESCRIPTION": "Description",
        "PAYMENT_REFERENCE": "Payment Reference",
        "RUNNING_BALANCE": "Running Balance",
        "EXCHANGE_FROM": "Exchange From",
        "EXCHANGE_TO": "Exchange To",
        "EXCHANGE_RATE": "Exchange Rate",
        "PAYER_NAME": "Payer Name",
        "PAYEE_NAME": "Payee Name",
        "PAYEE_ACCOUNT_NUMBER": "Payee Account Number",
        "MERCHANT": "Merchant",
        "CARD_LAST_FOUR_DIGITS": "Card Last Four Digits",
        "CARD_HOLDER_FULL_NAME": "Card Holder Full Name",
        "ATTACHMENT": "Attachment",
        "NOTE": "Note",
        "TOTAL_FEES": "Total fees",
    }

    # Assert headers match DF headers
    assert df.columns.tolist() == list(HEADERS.values())
    # Keep only Date, Description, Amount
    df = df[
        [HEADERS["DATE"], HEADERS["DESCRIPTION"], HEADERS["AMOUNT"]]
    ].copy()  # Include copy to avoid SettingWithCopyWarning

    # Remove pattern `Card transaction of 40.00 CHF issued by `
    df.loc[
        df[HEADERS["DESCRIPTION"]].str.contains(
            "Card transaction of \d+\.\d+ \D+ issued by "
        ),
        HEADERS["DESCRIPTION"],
    ] = df[HEADERS["DESCRIPTION"]].str.replace(
        r"Card transaction of \d+\.\d+ \D+ issued by ", "", regex=True
    )

    # Lowercase column names to be detected by lunchmomey
    df.columns = df.columns.str.lower()

    return df
