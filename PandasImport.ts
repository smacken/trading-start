import * as child from 'child_process'
const spawn = child.spawn;

export class PandasImport {
    constructor(public dataPath: string) {
    }

    async import(): Promise<void> {
        const pythonProcess = spawn('python', ["path/to/script.py", this.dataPath]);
        pythonProcess.stdout.on('data', (data) => console.log(data));
    }
}