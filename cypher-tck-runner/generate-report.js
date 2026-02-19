const report = require("multiple-cucumber-html-reporter");
const fs = require("fs");
const path = require("path");

const RESULTS_DIR = "results";
const PATCHED_DIR = ".results-patched";

// Behave JSON is missing several fields that multiple-cucumber-html-reporter
// requires. This normalises Behave output to Cucumber-spec format:
//   - feature.uri  (Behave uses `location` instead)
//   - feature.id   (missing)
//   - element.id   (missing)
//   - element.line (missing)
//   - step.result  (missing for skipped/undefined steps)
//   - step.text    (Behave raw string → Cucumber doc_string object)
function patchJson(data) {
    for (const feature of data) {
        // Derive uri from location (e.g. "features/example.feature:5" → "features/example.feature")
        if (!feature.uri && feature.location) {
            feature.uri = feature.location.split(":")[0];
        }
        if (!feature.id) {
            feature.id = (feature.name || "unknown").toLowerCase().replace(/\s+/g, "-");
        }

        for (const element of feature.elements || []) {
            if (!element.id) {
                element.id = `${feature.id};${(element.name || "unknown").toLowerCase().replace(/\s+/g, "-")}`;
            }
            if (!element.line && element.location) {
                element.line = parseInt(element.location.split(":")[1] || "0", 10);
            }

            for (const step of element.steps || []) {
                // Fix missing result for skipped/undefined steps
                if (!step.result) {
                    step.result = { status: "skipped", duration: 0 };
                }
                // Fix error_message: Behave emits it as an array of strings,
                // Cucumber spec (and the reporter) expects a single string
                if (Array.isArray(step.result.error_message)) {
                    step.result.error_message = step.result.error_message.join("\n");
                }
                // Fix doc_string: Behave emits step.text as a plain string,
                // Cucumber spec expects step.doc_string = {value, content_type, line}
                if (typeof step.text === "string") {
                    step.doc_string = { content_type: "", value: step.text, line: 0 };
                    delete step.text;
                }
            }
        }
    }
    return data;
}

// Write patched copies to a temp dir
fs.rmSync(PATCHED_DIR, { recursive: true, force: true });
fs.mkdirSync(PATCHED_DIR, { recursive: true });

const jsonFiles = fs
    .readdirSync(RESULTS_DIR)
    .filter((f) => f.endsWith(".json"));

if (jsonFiles.length === 0) {
    console.error(`WARNING: No JSON files found in '${RESULTS_DIR}/'. NO REPORT CAN BE CREATED!`);
    process.exit(1);
}

for (const file of jsonFiles) {
    const src = path.join(RESULTS_DIR, file);
    const dst = path.join(PATCHED_DIR, file);
    const data = JSON.parse(fs.readFileSync(src, "utf8"));
    fs.writeFileSync(dst, JSON.stringify(patchJson(data)));
}

report.generate({
    jsonDir: PATCHED_DIR,
    reportPath: "report/",
    openReportInBrowser: true,
    displayDuration: true,
    durationInMS: true,
    displayReportTime: true,
    pageTitle: "openCypher TCK Results",
    reportName: "openCypher TCK Compliance",
    customData: {
        title: "Run Info",
        data: [
            { label: "Project", value: "Raphtory" },
            { label: "Suite", value: "openCypher TCK" },
            {
                label: "Execution Date",
                value: new Date().toLocaleString("en-GB", {
                    dateStyle: "medium",
                    timeStyle: "short",
                }),
            },
        ],
    },
});
