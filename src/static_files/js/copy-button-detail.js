// Function to display a temporary message on the page
function showMessage(button, duration = 5000) {
  let messageSpan = button.nextElementSibling;
  if (messageSpan && messageSpan.classList.contains("copy-message")) {
    messageSpan.textContent = "Copied!";
    messageSpan.style.display = "inline";
    setTimeout(() => {
      messageSpan.textContent = "";
      messageSpan.style.display = "none";
    }, duration);
  }
}

// Fallback function using a temporary textarea for older browsers
function fallbackCopyText(text, button) {
  const textarea = document.createElement('textarea');
  textarea.value = text;
  document.body.appendChild(textarea);
  textarea.select();
  try {
    document.execCommand('copy');
    showMessage(button); // Pass the button to showMessage
  } catch (err) {
    console.error('Fallback: Unable to copy', err);
  }
  document.body.removeChild(textarea);
}

function copyText(event) {
  let button = event.target; // Get the clicked button
  //let row = button.closest("div");
  //let dataDiv = row.querySelector(".copy-data");

  let block = button.closest(".copy-block");
  let messageSpan = block.querySelector(".copy-message");
  let dataDiv = block.querySelector(".copy-data");

  if (dataDiv) {
    // Extract values
    let title = dataDiv.getAttribute("data-title");
    let alias = dataDiv.getAttribute("data-alias");
    let tags = dataDiv.getAttribute("data-tags");

    // Format text for copying
    let text = `${title}\n${alias}\n${tags}`;

    // Check if the Clipboard API is available
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text)
        .then(() => {
          showMessage(button); // Pass the button to showMessage
        })
        .catch(err => {
          console.error('Failed to copy using Clipboard API, using fallback method', err);
          fallbackCopyText(text, button); // Pass the button to fallbackCopyText
        });
    } else {
      // Use the fallback method if Clipboard API is not available
      fallbackCopyText(text, button); // Pass the button to fallbackCopyText
    }
  }
}

document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".copy-btn").forEach(button => {
    button.addEventListener("click", copyText);
  });
});