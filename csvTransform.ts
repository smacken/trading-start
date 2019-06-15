'use strict';

const parse = require('csv-parse');
const stringify = require('csv-stringify');
const transform = require('stream-transform');
const fs = require('fs-extra-promise');

// const infname = process.argv[2];
// const outfname = process.argv[3];

const inputFields: string[] = [
    'announcementStatusNote',
    'availableUnits',
    'changeValueAmt',
    'changeValuePrc',
    'code',
    'lastPrice',
    'marketValue',
    'name',
    'profitLossAmt',
    'profitLossPrc',
    'purchasePrice',
    'sponsor',
    'unitChangeAmt'
];

const extractFields: string[] = [
    // List field names to extract from input
    'code',
    'availableUnits',
    'purchasePrice',
    'lastPrice',
    'marketValue',
    'profitLossAmt',
    'profitLossPrc',
    'unitChangeAmt',
    'changeValueAmt'
];

const outputFields: string[] = [
    // List field names in the output file
    'Code',
    'Avail Units',
    'Purchase($)',
    'Last($)',
    'Mkt Value($)',
    'Profit / Loss($)',
    'Profit / Loss(%)',
    'Change($)',
    'Chg Value($)'
]

let transformCsv = (infname?: string, outfname?: string): void => {
    if (!infname) infname = process.argv[2];
    if (!outfname) outfname = process.argv[3];
    fs.createReadStream(infname)
        .pipe(parse({
            delimiter: ',',
            // Use columns: true if the input has column headers
            // Otherwise list the input field names in the array above.
            columns: inputFields
        }))
        .pipe(transform(function (data: any) {
            // This sample transformation selects out fields
            // that will make it through to the output.  Simply
            // list the field names in the array above.
            return extractFields
                .map(nm => { return data[nm]; });
        }))
        .pipe(stringify({
            delimiter: ',',
            relax_column_count: true,
            skip_empty_lines: true,
            header: true,
            // This names the resulting columns for the output file.
            columns: outputFields
        }))
        .pipe(fs.createWriteStream(outfname));
}
export { transformCsv };