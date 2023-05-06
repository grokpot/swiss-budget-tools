import xml.etree.ElementTree as ET
import pandas as pd

from parsers.camt_parser import CamtParser

HEADER_DATE = "date"
HEADER_DESCRIPTION = "description"
HEADER_AMOUNT = "amount"


def clean_df(df):
    """Cleans a dataframe (usually the description column) according to various rules"""

    # Remove `Debitkarten-Einkauf date-time`
    df[HEADER_DESCRIPTION] = df[HEADER_DESCRIPTION].str.replace(
        r"Debitkarten-Einkauf \d{2}\.\d{2}\.\d{4} \d{2}:\d{2} ", "", regex=True
    )
    # Remove `Zahlung - `
    df[HEADER_DESCRIPTION] = df[HEADER_DESCRIPTION].str.replace(
        r"Zahlung - ", "", regex=True
    )
    # Remove  - Karten-Nr. 123456******1234
    df[HEADER_DESCRIPTION] = df[HEADER_DESCRIPTION].str.replace(
        r" - Karten-Nr. \d{6}\*{6}\d{4}", "", regex=True
    )
    # Replace `Vergütung` with `(Transfer)`
    df.loc[df[HEADER_DESCRIPTION].str.contains("Vergütung"), HEADER_DESCRIPTION] = df[
        HEADER_DESCRIPTION
    ].str.replace("Vergütung", "Transfer")
    # Remove `TWINT Gutschrift`, then add `(TWINT)`
    df.loc[
        df[HEADER_DESCRIPTION].str.contains("TWINT Gutschrift"), HEADER_DESCRIPTION
    ] = (df[HEADER_DESCRIPTION].str.replace("TWINT Gutschrift", "") + " (TWINT)")
    # Remove `TWINT Belastung`, then add `(TWINT)`
    df.loc[
        df[HEADER_DESCRIPTION].str.contains("TWINT Belastung"), HEADER_DESCRIPTION
    ] = (df[HEADER_DESCRIPTION].str.replace("TWINT Belastung", "") + " (TWINT)")
    # Remove card number format 1
    df[HEADER_DESCRIPTION] = df[HEADER_DESCRIPTION].str.replace(
        r" Kartennummer: \d{16}", "", regex=True
    )
    # Remove card number format 2 (older transactions)
    df[HEADER_DESCRIPTION] = df[HEADER_DESCRIPTION].str.replace(
        r" - Karten-Nr. \w{16}", "", regex=True
    )
    # Remove redundant amount following format 2
    df[HEADER_DESCRIPTION] = df[HEADER_DESCRIPTION].str.replace(
        r" - \d+\.\d+ \D+", "", regex=True
    )
    # Remove date + time in descriptions
    df[HEADER_DESCRIPTION] = df[HEADER_DESCRIPTION].str.replace(
        r" - \d{2}\.\d{2}\.\d{4} \d{2}:\d{2}", "", regex=True
    )
    # Remove forex description. Ex: ` - 2.50 EUR zum Kurs 1.04`
    df[HEADER_DESCRIPTION] = df[HEADER_DESCRIPTION].str.replace(
        r" - \d+\.\d+ \D+ zum Kurs \d+\.\d+", "", regex=True
    )
    # Remove forex amount Ex: `0.99131 = CHF 2.60`
    df[HEADER_DESCRIPTION] = df[HEADER_DESCRIPTION].str.replace(
        r"\d+\.\d+ = \D+ \d+\.\d+", "", regex=True
    )
    # Remove fee description. Ex: ` - Plus Spesen CHF 0.05`
    df[HEADER_DESCRIPTION] = df[HEADER_DESCRIPTION].str.replace(
        r"Plus Spesen \D+ \d+\.\d+", "", regex=True
    )
    # Remove phone numbers from TWINT
    df[HEADER_DESCRIPTION] = df[HEADER_DESCRIPTION].str.replace(
        r" \+\d{11}", "", regex=True
    )
    # Remove 16-digit TWINT number
    df[HEADER_DESCRIPTION] = df[HEADER_DESCRIPTION].str.replace(
        r" \d{16}", "", regex=True
    )
    # Remove commas
    df[HEADER_DESCRIPTION] = df[HEADER_DESCRIPTION].str.replace(r",", "", regex=True)
    # Remove spaces from the beginning and end
    df[HEADER_DESCRIPTION] = df[HEADER_DESCRIPTION].str.strip()

    return df


def parse_valiant_csv(df):
    # Assert the first row is the header, printing a message if not
    assert (
        df.iloc[0, 0] == "Datum"
    ), "First cell does not match expectations, valiant probably changed their template"

    # Make first row the header, and drop the first row
    df.columns = df.iloc[0]
    df = df.drop(df.index[0])
    # Rename the headers to [date, description, amount]
    df = df.rename(
        columns={
            df.columns[0]: HEADER_DATE,
            df.columns[1]: HEADER_DESCRIPTION,
            df.columns[2]: HEADER_AMOUNT,
        }
    )

    # Remove the last column
    df = df.iloc[:, :-1]
    # In all cells, remove commas
    df = df.replace(",", "", regex=True)

    df = clean_df(df)

    return df


def parse_valiant_xml(filename: str, me: str, include_bank_fees: bool) -> pd.DataFrame:
    transactions, bank_fee_instances, bank_fees = CamtParser(
        filename, include_bank_fees
    ).get_transactions()
    df = pd.DataFrame(columns=[HEADER_DATE, HEADER_DESCRIPTION, HEADER_AMOUNT])

    for tx in transactions:
        special_types = ["Vergütung", "Dauerauftrag"]
        desc = tx[CamtParser.HEADER_DESCRIPTION]
        if desc in special_types:
            if me in tx["Creditor"]:
                desc = tx["Debtor"]
            elif me in tx["Debtor"]:
                desc = tx["Creditor"]
            else:
                raise (ValueError("Could not find me in either Debtor or Creditor"))
        df2 = pd.DataFrame(
            [[tx[CamtParser.HEADER_DATE], desc, tx[CamtParser.HEADER_AMOUNT]]],
            columns=[HEADER_DATE, HEADER_DESCRIPTION, HEADER_AMOUNT],
        )
        df = pd.concat([df2, df], ignore_index=True)

    # Include bank fees as a transaction
    if include_bank_fees and bank_fee_instances:
        min_date = df[HEADER_DATE].min()
        max_date = df[HEADER_DATE].max()
        desc = f"{bank_fee_instances} probable bank fees from {min_date} to {max_date}"
        df2 = pd.DataFrame(
            [[max_date, desc, bank_fees]],
            columns=[HEADER_DATE, HEADER_DESCRIPTION, HEADER_AMOUNT],
        )
    df = pd.concat([df2, df], ignore_index=True)

    df = clean_df(df)
    return df
