import fs from "node:fs/promises";

const inputPath = "eval/output/manual_retrieval_check_after_chunking.csv";
const comparisonPath = "eval/output/chunking_retrieval_comparison.csv";

const relevantRanks = {
  "C-01": [1, 4],
  "C-02": [1, 2, 3, 4],
  "C-03": [1],
  "C-04": [1],
  "C-05": [4, 5],
  "C-06": [1],
  "C-07": [],
  "C-08": [],
  "C-09": [1, 3, 4],
  "C-10": [2, 3],
  "C-11": [1, 2, 5],
  "C-12": [],
  "C-13": [3],
  "C-14": [],
  "C-15": [1, 2],
  "C-16": [2],
  "C-17": [],
  "C-18": [2, 3, 4],
  "C-19": [1],
  "C-20": [1, 2],
};

const failureNotes = {
  "C-07": "Top-5 không có lịch hoặc bước bảo dưỡng cụ thể.",
  "C-08": "Không có chunk đúng nguồn T009 trong Top-5; nội dung sát nhất thuộc T012.",
  "C-12": "Top-5 không liệt kê lỗi thường gặp và hướng xử lý cụ thể.",
  "C-14": "Không có chunk đúng nguồn W001 hoặc thời hạn bảo hành trong Top-5.",
  "C-17": "Top-5 không có hướng dẫn lắp đặt hoặc sử dụng lần đầu cụ thể.",
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
  if (value || row.length) { row.push(value); records.push(row); }
  return records;
}

function escapeCsv(value) {
  const stringValue = String(value ?? "");
  return /[",\n\r]/.test(stringValue) ? `"${stringValue.replaceAll('"', '""')}"` : stringValue;
}

const records = parseCsv((await fs.readFile(inputPath, "utf8")).replace(/^\uFEFF/, ""));
const header = records[0];
const columns = Object.fromEntries(header.map((name, index) => [name, index]));
for (const row of records.slice(1)) {
  const caseId = row[columns.case_id];
  const rank = Number(row[columns.rank]);
  row[columns.relevant] = relevantRanks[caseId].includes(rank) ? "1" : "0";
  row[columns.review_note] = rank === 1 && failureNotes[caseId] ? failureNotes[caseId] : "";
}
await fs.writeFile(
  inputPath,
  `\uFEFF${records.map((row) => row.map(escapeCsv).join(",")).join("\r\n")}\r\n`,
  "utf8",
);

const afterRelevant = Object.values(relevantRanks).reduce((total, ranks) => total + ranks.length, 0);
const afterPassed = Object.values(relevantRanks).filter((ranks) => ranks.length > 0).length;
const comparisonRows = [
  ["run", "relevant_chunks", "retrieved_chunks", "precision_at_5", "passed_cases", "total_cases", "recall_at_5", "review_basis"],
  ["before_chunking", "26", "100", "0.26", "16", "20", "0.80", "Chunk content; retrieved_source and page were blank."],
  ["after_chunking", String(afterRelevant), "100", (afterRelevant / 100).toFixed(2), String(afterPassed), "20", (afterPassed / 20).toFixed(2), "Expected source and chunk content."],
];
await fs.writeFile(
  comparisonPath,
  `\uFEFF${comparisonRows.map((row) => row.map(escapeCsv).join(",")).join("\r\n")}\r\n`,
  "utf8",
);
console.log(JSON.stringify({ afterRelevant, afterPassed, precisionAt5: afterRelevant / 100, recallAt5: afterPassed / 20 }));
