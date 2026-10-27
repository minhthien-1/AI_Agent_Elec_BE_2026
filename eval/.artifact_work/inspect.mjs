import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const input = await FileBlob.load("../../outputs/retrieval_eval/bo_test_danh_gia_20_cau.xlsx");
const workbook = await SpreadsheetFile.importXlsx(input);
const summary = await workbook.inspect({
  kind: "workbook,sheet,table",
  maxChars: 12000,
  tableMaxRows: 30,
  tableMaxCols: 15,
  tableMaxCellChars: 140,
});
console.log(summary.ndjson);
for (const name of ["Bộ test đánh giá", "Sheet1"]) {
  try {
    const preview = await workbook.render({ sheetName: name, autoCrop: "all", scale: 1, format: "png" });
    await fs.writeFile(`eval/.artifact_work/${name.replaceAll(" ", "_")}.png`, new Uint8Array(await preview.arrayBuffer()));
    console.log(`Rendered ${name}`);
  } catch (error) {
    console.log(`No render for ${name}: ${error.message}`);
  }
}
