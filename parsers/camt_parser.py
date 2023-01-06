import logging
from typing import Tuple
from sepa import parser
import re
import pandas as pd

logger = logging.getLogger(__name__)

# build a camt parser class
class CamtParser:
    HEADER_DATE = "Date"
    HEADER_DESCRIPTION = "Description"
    HEADER_AMOUNT = "Amount"
    HEADER_CURRENCY = "Currency"
    HEADER_TYPE = "Type"
    HEADER_CREDITOR = "Creditor"
    HEADER_DEBTOR = "Debtor"

    def __init__(self, filename, include_bank_fees=False):
        """
        :param filename: path to the camt file
        :param include_bank_fees: if True, will include bank fees as a separate line item
        """
        self.filename = filename
        self.include_bank_fees = include_bank_fees
        self.xml = None
        self.camt_dict = None

    # Read file
    def _get_xml(self) -> None:
        with open(self.filename, "r") as f:
            xml = f.read()
        # Remove additional namespaces from the XML
        xml = re.sub(' xmlns="[^"]+"', "", xml, count=1)
        self.xml = xml

    # Parse the bank statement XML to dictionary
    def _get_camt_dict(self) -> None:
        self.camt_dict = parser.parse_string(
            parser.bank_to_customer_statement, bytes(self.xml, "utf8")
        )

    @staticmethod
    def _check_bank_fees(entry, transaction) -> float:
        bank_fees = 0
        # If tx is not batched and tx amt doesn't match the entry amt, it's might be a bank fee
        tx_amt = float(
            transaction["amount_details"]["transaction_amount"]["amount"]["_value"]
        )
        entry_amt = float(entry["amount"]["_value"])
        assert (
            transaction["amount"]["currency"] == entry["amount"]["currency"]
        ), "If this happens, need to update lines below to prevent counting forex change"
        if len(entry["entry_details"][0]["transactions"]) == 1 and tx_amt != entry_amt:
            logger.debug(
                f"Transaction amount does not match entry amount: {entry['additional_information']}, potential fee: {bank_fees}"
            )
            bank_fees = max(tx_amt, entry_amt) - min(tx_amt, entry_amt)
        return bank_fees

    def get_transactions(self) -> Tuple[dict, float, float]:
        # Calling here and not in __init__ because it could be slow
        self._get_xml()
        self._get_camt_dict()

        statements = pd.DataFrame.from_dict(self.camt_dict["statements"])
        bank_fee_instances = 0
        bank_fees = 0
        all_entries = []

        assert len(statements) == 1, "Have not yet seen multiple statements in one file"
        for i, _ in statements.iterrows():
            if "entries" in self.camt_dict["statements"][i]:
                camt = self.camt_dict["statements"][i]["entries"]
                for entry in camt:
                    assert (
                        len(entry["entry_details"]) == 1
                    ), "Have not yet come across a case where there are multiple entries in a batch"
                    # Unbatching in case bank has batched transactions
                    if entry["entry_details"][0].get("transactions"):
                        transactions = entry["entry_details"][0]["transactions"]
                        amount_field = "amount"
                    # Sometimes a transaction does not exist, but the entry is still valid
                    else:
                        transactions = [entry["entry_details"][0]['batch']]
                        amount_field = "total_amount"
                    for transaction in transactions:
                        tx = {}
                        tx[self.HEADER_DATE] = entry["value_date"]["date"]
                        assert (
                            len(entry["additional_information"]) == 1
                        ), "Have not yet come across a case where there are multiple descriptions"
                        tx[self.HEADER_DESCRIPTION] = entry["additional_information"][0]
                        tx[self.HEADER_TYPE] = transaction["credit_debit_indicator"]
                        if transaction.get("related_parties"):
                            tx[self.HEADER_CREDITOR] = transaction["related_parties"][
                                "creditor"
                            ]["name"]
                            tx[self.HEADER_DEBTOR] = transaction["related_parties"][
                                "debtor"
                            ]["name"]
                        # If collecting bank fees as a separate tx, use the pre-fee amount as amount and update description
                        if self.include_bank_fees and amount_field == "amount" and transaction.get("amount_details"):
                            bank_fee = self._check_bank_fees(entry, transaction)
                            if bank_fee > 0:
                                bank_fee_instances += 1
                                bank_fees -= bank_fee
                            amt = float(
                                transaction["amount_details"]["transaction_amount"][amount_field]["_value"]
                            )
                            if bank_fee:
                                tx[
                                    self.HEADER_DESCRIPTION
                                ] = f"{tx[self.HEADER_DESCRIPTION]} (excl. {bank_fee:.{2}f} bank fee)"
                        else:
                            amt = float(transaction[amount_field]["_value"])
                        tx[self.HEADER_AMOUNT] = amt * (
                            -1 if tx[self.HEADER_TYPE] == "DBIT" else 1
                        )
                        tx[self.HEADER_CURRENCY] = transaction[amount_field]["currency"]
                        all_entries.append(tx)
        if bank_fee_instances > 0:
            bank_fees = round(bank_fees, 2)
            logger.info(
                f"There were {bank_fee_instances} instances of entry/tx amt differences which could indicate bank fees. Total potential fees: {bank_fees}"
            )
        return all_entries, bank_fee_instances, bank_fees
