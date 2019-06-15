#!/usr/bin/env node

import { promisify } from 'util';
import * as path from 'path';
import { TradingFile } from './TradingFile'
import { CommsecImport, getCache, setCache } from './Commsec'
var config = require('./config.json');
const prompt = require('prompt');
const CachemanFile = require('cacheman-file');
const cache = new CachemanFile({ tmpDir: path.join(process.cwd(), 'temp') }, {});

// args
// node index.js --file -holding -trans -account
const argv = process.argv.slice(2);
let isFile = argv.some(arg => ['--file', '-file', '--f', '-f'].includes(arg));
let isHoldings = argv.some(arg => ['--holdings', '-holdings', '--holding', '-holding', '--h', '-h'].includes(arg));
let isTransactions = argv.some(arg => ['--transactions', '-transactions', '--trans', '-trans', '--t', '-t'].includes(arg));
let isAccountTrans = argv.some(arg => ['--account', '-account', '-a', '--a'].includes(arg));


let getCredentials = (username?: string): Promise<any> => {
    var schema = {
        properties: {
            username: {
                required: false,
                ask: !config.saveUsername
            },
            password: {
                hidden: true,
                required: true
            }
        }
    };
    if (!!username) delete schema.properties.username;
    console.log(schema);
    return new Promise((resolve, reject) => {
        prompt.get(schema, (error: Error, result: any) => {
            if (!!error) reject(error);
            resolve(result);
        });
    });
}
(async () => {
    if (isFile) {
        let trading = new TradingFile(isFile, config.sourcePath, config.destinationPath);
        try {
            if (isHoldings) await trading.setupFile("Holdings");
            if (isTransactions) await trading.setupFile("Transactions");
            if (isAccountTrans) await trading.setupFile("CSVData", "Account");
        } catch (error) {
            console.error(error);
        }
    } else {
        prompt.start();
        let commsec;
        try {
            // use prompt credentials to auth with commsec and retrieve holdings
            let user = await getCache('username');
            console.log(`user: ${user}`);
            let credentials = await getCredentials(user);
            console.log(`trading import using Commsec: ${credentials.username}`)
            if (config.saveUsername) {
                await setCache('username', credentials.username);
            }
            commsec = new CommsecImport(credentials.username, credentials.password);
            let auth = await commsec.login();
            credentials = null;
            if (auth && isHoldings) {
                const holdings = await commsec.getHoldings();
                console.log(`holdings: ${holdings.length}`);
                await commsec.moveTo(holdings, config.destinationPath);
            }
        } catch (error) {
            console.log(error);
        } finally {
            commsec = undefined;
        }
    }
})();
