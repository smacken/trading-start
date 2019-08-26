import * as fs from 'fs';
import { promisify } from 'util';
import * as path from 'path';
import { moveFiles, fileExists } from './File'

const rename = promisify(fs.rename);
const readdir = promisify(fs.readdir);

export class TradingFile {
    constructor(public isFile: boolean, public from: string, public to: string) {
        this.from = from;
        this.isFile = isFile;
        this.to = to;
    }

    async setupFile(fileMatch: string, outputFile?: string) {
        if (!outputFile) outputFile = fileMatch;
        let files = await readdir(this.from);
        let matches = files.filter((val, idx, array) => val.includes(fileMatch));
        if (!matches) {
            throw new Error("No source file. Remember to download.");
        }

        // handle duplicates for files e.g. Holdings(1).csv
        let highVal = 0;
        let highest: string = '';
        matches.forEach((val) => {
            let match = val.match('(\\d)')
            if (!!match && Number(match[0]) >= highVal) {
                highest = match.input as string;
                highVal = Number(match[0])
            } else if (highVal === 0) {
                highest = val;
            }
        });

        await this.replace(outputFile);
        await moveFiles(path.join(this.from, highest), path.join(this.to, `${outputFile}.csv`));
    }

    leftpad(val: number, resultLength = 2, leftpadChar = '0'): string {
        return (String(leftpadChar).repeat(resultLength)
            + String(val)).slice(String(val).length);
    }

    dateFormat(date: Date): string {
        return this.leftpad(date.getDate(), 2)
            + '_' + this.leftpad(date.getMonth() + 1, 2)
            + '_' + date.getFullYear();
    }

    async replace(existing: string) {
        let existingFile = await fileExists(path.join(this.to, `${existing}.csv`));
        if (!existingFile) return;
        let now = new Date();
        let dateFormat = this.dateFormat(now);
        let newFileDate = `${existing}_${dateFormat}.csv`
        let exists = false;
        try {
            exists = await fileExists(path.join(this.to, newFileDate));
        } catch (error) {
            exists = false;
        }
        if (exists) {
            newFileDate = `${existing}_${dateFormat}_1.csv`
        }
        await rename(path.join(this.to, `${existing}.csv`), path.join(this.to, newFileDate))
    }


}