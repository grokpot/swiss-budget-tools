import datetime
import logging
import os
import click
import pandas as pd
from parsers.n26 import parse_n26_csv
from parsers.valiant import parse_valiant_csv, parse_valiant_xml
from parsers.wise import parse_wise_csv

LOGLEVEL = os.environ.get("LOGLEVEL", "INFO").upper()
logging.basicConfig(level=LOGLEVEL)

# Basic first name which should appear in your bank transactions, helps to differentiate between inflows/outflows
me = "Ryan"

# default contains todays date
# strf format for HH:MM:SS:
default_output_folder = os.getcwd() if 'workspaces' in os.getcwd() else f'~/Downloads/'
default_output_filename = f'{default_output_folder}{datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")}_SOURCE-converted.csv'
# Use python click to take two parameters
@click.command()
@click.option("--source", help="Sources: valiant, n26, wise")
@click.option("--input", default="input.csv", help="Input file")
@click.option("--output", default=default_output_filename, help="Output file")
@click.option(
    "--include_bank_fees", default=True, help="Include bank fees as separate line item"
)
def main(source, input, output, include_bank_fees):
    df = None
    # If source is valiant, convert valiant input
    if source == "valiant":
        if ".csv" in input:
            # Read the csv file, skipping header data (kontonumber, etc.)
            df = pd.read_csv(
                input, sep=";", skiprows=10, engine="python", encoding="latin-1"
            )
            df = parse_valiant_csv(df)
        elif ".xml" in input:
            df = parse_valiant_xml(input, me, include_bank_fees)
        else:
            raise ("Unknown file type")
    elif source == "wise":
        df = pd.read_csv(input, sep=",")
        df = parse_wise_csv(df)
    elif source == "n26":
        df = pd.read_csv(input, sep=",")
        df = parse_n26_csv(df)
    # Replace SOURCE with the source name
    output = output.replace("SOURCE", source)
    # Write the output file, using comma as delimiter
    df.to_csv(output, index=False, sep=",")


if __name__ == "__main__":
    main()
