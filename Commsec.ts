import { promisify } from 'util';
import fs from 'fs';
import * as path from 'path';
const Commsec = require('commsec');
var CachemanFile = require('cacheman-file');
const cache = new CachemanFile({ tmpDir: path.join(process.cwd(), 'temp') }, {});
import stringify from 'csv-stringify';

import { moveFiles, fileExists } from './File';
import { transformCsv } from './csvTransform';

let getCache = (key: string): Promise<any> => {
    return new Promise((resolve, reject) => {
        cache.get(key, (error: Error, result: any) => {
            if (error) reject(error);
            resolve(result);
        });
    });
}

let setCache = (key: string, item: any): Promise<void> => {
    return new Promise((resolve, reject) => {
        cache.set(key, item, (error: Error) => {
            if (error) reject(error);
            resolve();
        });
    });
}

export { getCache, setCache };
export class CommsecImport {
    deviceId: string = '';
    commsec = new Commsec();;
    cache = new CachemanFile({ tmpDir: path.join(process.cwd(), 'temp') }, {});
    getDevice: any;

    // Set the credentials.  You'd normally load these from a secure location,
    // such as an environment variable or a file outside any git repository.
    creds = {
        "clientId": "12345678",
        "deviceId": this.deviceId,
        "loginType": "password",
        "password": "secret",
        // The trading password is optional and not needed to view prices
        // or holdings.
        "tradingPassword": "supersecret",
    };
    constructor(clientId: string, password: string) {
        this.creds.clientId = clientId;
        this.creds.password = password;
        this.getDevice = getCache;
    }

    async login(): Promise<any> {
        let loginResponse;

        const deviceId = await this.getDevice('deviceid');
        if (deviceId) this.creds.deviceId = deviceId;
        try {
            loginResponse = await this.commsec.login(this.creds);
            console.log('logged in');
        } catch (e) {
            console.log('Unable to log in:', e.message);
            return false;
        }

        if (loginResponse.deviceId) {
            // If you get a new device ID, you should save it and use it for future
            // logins.  It doesn't seem to time out so you can just add it to your
            // credential store along with your password.
            console.log('Received a new device ID:', loginResponse.deviceId);
            this.cache.set('deviceid', loginResponse.deviceId, (err: any, value: any) => {
                if (err) throw err;
            });
        }
        return loginResponse;
    }

    async logout(): Promise<void> {
        const logoutCommsec = promisify(this.commsec.logout);
        await logoutCommsec();
        this.commsec.logout()
    }

    toCsv(items: any[], options: stringify.Options): Promise<void> {
        return new Promise((resolve, reject) => {
            stringify(items, options, (error, result: any) => {
                if (error) reject(error);
                resolve(result);
            });
        });
    }

    async moveTo(holdings: any[], destination: string) {
        const toFile = promisify(fs.writeFile);
        let output = await this.toCsv(holdings, { header: false, columns: Object.keys(holdings[0]) });
        let file = await toFile('Holdings_tmp.csv', output);
        transformCsv('Holdings_tmp.csv', path.join(destination, 'Holdings.csv'));
        fs.unlink('Holdings_tmp.csv', (err) => console.log(err));
    }

    async getHoldings(): Promise<any[]> {
        let holdings: any[] = [];
        try {
            let h = await this.commsec.getHoldings();
            h.entities.forEach((entity: any) => {
                console.log('Entity', entity.entityName);
                for (const account of entity.accounts) {
                    for (const holding of account.holdings) {
                        if (!!holding) holdings.push(holding);
                    }
                }
            });
        } catch (e) {
            console.log('Error retrieving holdings:', e.message);
        }
        return holdings;
    };
}