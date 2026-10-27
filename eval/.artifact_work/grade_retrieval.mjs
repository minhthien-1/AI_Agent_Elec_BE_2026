import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const csvPath = "../../eval/output/manual_retrieval_check.csv";
const xlsxPath = "../../outputs/retrieval_eval/bo_test_danh_gia_20_cau.xlsx";

const relevantRanks = {
  "C-01": [1, 4],
  "C-02": [1, 3, 4],
  "C-03": [1],
  "C-04": [1],
  "C-05": [2, 3],
  "C-06": [1],
  "C-07": [],
  "C-08": [1, 2],
  "C-09": [1, 5],
  "C-10": [3, 5],
  "C-11": [1, 3, 4],
  "C-12": [],
  "C-13": [2],
  "C-14": [],
  "C-15": [1],
  "C-16": [],
  "C-17": [2, 3],
  "C-18": [5],
  "C-19": [4],
  "C-20": [2],
};

const failureNotes = {
  "C-07": "Top-5 không nêu lịch hoặc bước bảo dưỡng cụ thể.",
  "C-12": "Top-5 không nêu lỗi thường gặp hay hướng xử lý cụ thể.",
  "C-14": "Top-5 không có thời hạn bảo hành tủ lạnh Panasonic.",
  "C-16": "Top-5 không nêu thao tác bảo quản thực phẩm/cài đặt cụ thể.",
};

function parseCsv(text) {
  const records = [];
  let row = [];
  let value = "";
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    if (char === '"') {
      if (quoted && text[i + 1] === '"') { value += '"'; i += 1; }
      else quoted = !quoted;
    } else if (char === "," && !quoted) {
      row.push(value); value = "";
    } else if (char === "\n" && !quoted) {
      row.push(value); records.push(row); row = []; value = "";
    } else if (char !== "\r") {
      value += char;
    }
  }
  if (value !== "" || row.length) { row.push(value); records.push(row); }
  return records;
}

function escapeCsv(value) {
  const stringValue = String(value ?? "");
  return /[",\n\r]/.test(stringValue) ? `"${stringValue.replaceAll('"', '""')}"` : stringValue;
}

const csvText = await fs.readFile(csvPath, "utf8");
const records = parseCsv(csvText.replace(/^\uFEFF/, ""));
const headers = records[0];
const columns = Object.fromEntries(headers.map((header, index) => [header, index]));
for (const row of records.slice(1)) {
  const caseId = row[columns.case_id];
  const rank = Number(row[columns.rank]);
  row[columns.relevant] = relevantRanks[caseId].includes(rank) ? "1" : "0";
  row[columns.review_note] = rank === 1 && failureNotes[caseId] ? failureNotes[caseId] : "";
}
await fs.writeFile(csvPath, `\uFEFF${records.map((row) => row.map(escapeCsv).join(",")).join("\r\n")}\r\n`, "utf8");

const input = await FileBlob.load(xlsxPath);
const workbook = await SpreadsheetFile.importXlsx(input);
const sheet = workbook.worksheets.getItem("Bo test danh gia");
const statuses = Object.keys(relevantRanks).map((caseId) => [relevantRanks[caseId].length ? "✓" : "✗"]);
sheet.getRange("I6:I25").values = statuses;
workbook.recalculate();

const check = await workbook.inspect({
  kind: "table",
  range: "Bo test danh gia!A4:I25",
  include: "values,formulas",
  tableMaxRows: 22,
  tableMaxCols: 9,
});
console.log(check.ndjson);
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
  options: { useRegex: true, maxResults: 100 },
  summary: "final formula error scan",
});
console.log(errors.ndjson);
const preview = await workbook.render({ sheetName: "Bo test danh gia", range: "A1:I25", scale: 1, format: "png" });
await fs.writeFile("review_preview.png", new Uint8Array(await preview.arrayBuffer()));
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(xlsxPath);

const passed = Object.values(relevantRanks).filter((ranks) => ranks.length > 0).length;
console.log(JSON.stringify({ passed, total: 20, recallAt5: passed / 20 }));
