// import * as fs from 'fs';
import fs from "fs";
export function fileExists(filepath: string): Promise<boolean> {
    return new Promise((resolve, reject) => {
        fs.access(filepath, fs.constants.F_OK, error => {
            if (error) reject(error);
            resolve(!error);
        });
    });
}
export async function moveFiles(from: string, to: string): Promise<void> {
    try {
        fs.readFile(from, (err, data: Buffer) => {
            if (err) throw err;

            fs.writeFile(to, data, function (err) {
                if (err) throw err;
            });

            fs.unlink(from, function (err) {
                if (err) throw err;
            });
        });
    } catch (error) {
        console.error("moveFiles error: ", error);
    }
}