import fs from 'node:fs/promises';
import path from 'node:path';
import { FileBlob, SpreadsheetFile } from '@oai/artifact-tool';

const root = path.resolve(import.meta.dirname, '..', '..');
const work = path.join(root, '代码', '结果导出', '缓存');
const out = path.join(work, 'filled');
const preview = path.join(work, 'previews');
await fs.mkdir(out, { recursive: true });
await fs.mkdir(preview, { recursive: true });
const mode = process.argv[2] || 'preview';
const payload = mode === 'fill' ? JSON.parse(await fs.readFile(path.join(work, 'payload.json'), 'utf8')) : null;
const requested = process.argv.slice(3);
const readyNames = payload ? payload.workbooks.filter(s=>s.ready).map(s=>s.file) : ['result1.xlsx','result2.xlsx'];
if (requested.some(name=>!readyNames.includes(name))) throw new Error('Requested workbook is not ready');
const names = requested.length ? requested : readyNames;

async function render(wb, name, sheet, range, suffix) {
  const blob = await wb.render({sheetName:sheet,range,scale:1.6,format:'png'});
  await fs.writeFile(path.join(preview,`${name}-${sheet}-${suffix}.png`),new Uint8Array(await blob.arrayBuffer()));
}

for (const name of names) {
  const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(root,'基础数据',name)));
  if (mode === 'preview') {
    for (const sheet of name==='result1.xlsx'?['计划购电量','充放电量']:['计划购电量','充放电量','紧急购电量']) {
      await render(wb,name,sheet,sheet==='计划购电量'?(name==='result1.xlsx'?'A1:B8':'A1:D5'):(sheet==='充放电量'?'A1:F8':'A1:C6'),'before');
    }
    console.log('PREVIEW',name);
    continue;
  }
  const spec=payload.workbooks.find(s=>s.file===name);
  for (const [sheet,values] of Object.entries(spec.plans)) {
    const ws=wb.worksheets.getItem(sheet);
    const range=spec.kind==='single'?'B2:B145':'B2:EQ335';
    ws.getRange(range).values=values;
    ws.getRange(range).format.numberFormat='0.0000';
    // Keep long daily totals fully visible in the adjustment sheets.
    if (sheet==='调整购电量') ws.getRange('EP:EQ').format.columnWidth=18;
  }
  const storage=wb.worksheets.getItem('充放电量');
  if (spec.kind==='single') {
    storage.getRange('B2:C7').values=spec.storage;
    storage.getRange('E2:E3').values=[[spec.start],[spec.end]];
    storage.getRange('B2:C7').format.numberFormat='0.0000';
    storage.getRange('E2:E3').format.numberFormat='0.0000';
  } else {
    const rowCount=spec.storage.length;
    for (let row=8;row<=rowCount+1;row+=6) storage.getRange(`A${row}:F${row+5}`).copyFrom(storage.getRange('A2:F7'),'all');
    storage.getRange(`A2:F${rowCount+1}`).values=spec.storage;
    storage.getRange(`A2:F${rowCount+1}`).format.rowHeight=14;
    storage.getRange(`C2:D${rowCount+1}`).format.numberFormat='0.0000';
    storage.getRange(`F2:F${rowCount+1}`).format.numberFormat='0.0000';
    const emergency=wb.worksheets.getItem('紧急购电量');
    emergency.getRange('A2:C11').clear({applyTo:'contents'});
    let row=2;
    for (const count of spec.daygroups) {
      for (let j=0;j<count;j++) {
        const source=j===0?2:(j===count-1?4:3);
        if(row>4)emergency.getRange(`A${row}:C${row}`).copyFrom(emergency.getRange(`A${source}:C${source}`),'all');
        row++;
      }
    }
    emergency.getRange(`A2:C${spec.emergency.length+1}`).values=spec.emergency;
    emergency.getRange(`A2:A${spec.emergency.length+1}`).format.numberFormat='mm-dd-yy';
    emergency.getRange(`C2:C${spec.emergency.length+1}`).format.numberFormat='0.0000';
    emergency.getRange(`A2:C${spec.emergency.length+1}`).format.rowHeight=14;
  }
  wb.recalculate();
  console.log((await wb.inspect({kind:'table',range:'计划购电量!A1:D4',include:'values',tableMaxRows:4,tableMaxCols:4,maxChars:1200})).ndjson);
  for (const [sheet] of Object.entries(spec.plans)) {
    await render(wb,name,sheet,spec.kind==='single'?'A1:B8':'A1:D5','after');
    await render(wb,name,sheet,spec.kind==='single'?'A140:B145':'EM331:EQ335','tail');
  }
  await render(wb,name,'充放电量',spec.kind==='single'?'A1:E7':'A1:F8','after');
  if(spec.kind==='annual')await render(wb,name,'紧急购电量','A1:C8','after');
  const file=await SpreadsheetFile.exportXlsx(wb);
  await file.save(path.join(out,name));
  console.log('SAVED',name);
}
