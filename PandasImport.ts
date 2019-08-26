import * as child from 'child_process'
const spawn = child.spawn;

export class PandasImport {
    constructor(public dataPath: string) {
    }

    async import(): Promise<void> {
        const pythonProcess = spawn('cmd.exe', ["/c", "call .\\pandas\\run.bat"]);
        pythonProcess.stdout.on('data', (chunk) => console.log(chunk.toString('utf8')));
    }
}