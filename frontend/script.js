const scanBtn = document.getElementById("scanBtn");
const scanStatus = document.getElementById("scanStatus");
const treeContainer = document.getElementById("treeContainer");
const searchForm = document.getElementById("searchForm");
const queryInput = document.getElementById("queryInput");
const searchStatus = document.getElementById("searchStatus");
const answerBox = document.getElementById("answer");
const sourceBox = document.getElementById("source");

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderNode(node) {
  const name = escapeHtml(node.name);
  const className = node.node_type === "folder" ? "folder" : "file";
  const icon = node.node_type === "folder" ? "[DIR]" : "[FILE]";

  if (!node.children || node.children.length === 0) {
    return `<li><span class="${className}">${icon} ${name}</span></li>`;
  }

  const childrenHtml = node.children.map(renderNode).join("");
  return `<li><span class="${className}">${icon} ${name}</span><ul>${childrenHtml}</ul></li>`;
}

async function scanComputer() {
  scanBtn.disabled = true;
  scanStatus.textContent = "Scanning...";

  try {
    const response = await fetch("/api/scan");
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Scan failed");
    }

    treeContainer.innerHTML = `<ul>${renderNode(data.tree)}</ul>`;
    scanStatus.textContent = `Scan complete. Indexed ${data.indexed_documents} documents.`;
  } catch (error) {
    scanStatus.textContent = `Scan error: ${error.message}`;
  } finally {
    scanBtn.disabled = false;
  }
}

async function askQuestion(event) {
  event.preventDefault();

  const query = queryInput.value.trim();
  if (!query) {
    searchStatus.textContent = "Please enter a question.";
    return;
  }

  searchStatus.textContent = "Searching and generating answer...";
  answerBox.textContent = "";
  sourceBox.textContent = "";

  try {
    const response = await fetch("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Search failed");
    }

    answerBox.textContent = data.answer || "No answer generated.";

    if (data.source && data.source.file_path) {
      sourceBox.textContent = `${data.source.file_path} (${data.source.file_type})`;
    } else {
      sourceBox.textContent = "No matching source file found.";
    }

    searchStatus.textContent = "Done.";
  } catch (error) {
    searchStatus.textContent = `Search error: ${error.message}`;
  }
}

scanBtn.addEventListener("click", scanComputer);
searchForm.addEventListener("submit", askQuestion);
