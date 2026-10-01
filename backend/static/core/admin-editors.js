// Keep Unfold's bundled Trix editor aligned with the server's HTML allowlist.
document.addEventListener("trix-before-initialize", (event) => {
  Trix.config.blockAttributes.default.tagName = "p";
  // Django renumbers field IDs when an inline is added; Trix's input attribute
  // must follow the new ID before it connects to the hidden field.
  event.target.setAttribute("input", `${event.target.id}-input`);
});

document.addEventListener("trix-initialize", (event) => {
  const editor = event.target;
  const forbidden = ["heading1", "underlined", "strike"];
  if (editor.dataset.richTextProfile === "faq") {
    forbidden.push("heading2", "heading3", "heading4", "quote", "code");
  }
  for (const attribute of forbidden) {
    editor.toolbarElement.querySelector(`[data-trix-attribute="${attribute}"]`)?.remove();
  }
  editor.toolbarElement.querySelector('[data-trix-action="attachFiles"]')?.remove();
});

// There is no attachment upload endpoint. Embedded data URLs are not accepted.
document.addEventListener("trix-file-accept", (event) => event.preventDefault());
