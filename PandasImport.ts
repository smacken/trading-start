import * as child from 'child_process'
import * as stringDecode from 'string_decoder';
const spawn = child.spawn;
const StringDecoder = stringDecode.StringDecoder;

export class PandasImport {
    constructor(public dataPath: string) {
    }

    async import(): Promise<void> {
        var decoder = new StringDecoder('utf8');
        const pythonProcess = spawn('cmd.exe', ["/c", "call .\\pandas\\run.bat"]);
        pythonProcess.stdout.on('data', (chunk) => console.log(decoder.write(chunk)));
    }
}