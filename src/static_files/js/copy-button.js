// copy-button.js

// Get references to the HTML elements
const copyBtn = document.getElementById('copyBtn');
const textToCopy1 = document.getElementById('shortTitle');
const textToCopy2 = document.getElementById('shortAlias');
const copyMessage = document.getElementById('copyMessage');

// Function to display a temporary message on the page
function showMessage(message, duration = 3000) {
	copyMessage.textContent = message;
	// Clear the message after the specified duration (default 2000ms)
	setTimeout(() => {
		copyMessage.textContent = '';
	}, duration);
}

// Fallback function using a temporary textarea for older browsers
function fallbackCopyText(text) {
	const textarea = document.createElement('textarea');
	textarea.value = text;
	document.body.appendChild(textarea);
	textarea.select();
	try {
		document.execCommand('copy');
		showMessage('Copied!');
	} catch (err) {
		console.error('Fallback: Unable to copy', err);
	}
	document.body.removeChild(textarea);
}

// Add click event listener to the button
copyBtn.addEventListener('click', () => {
	// Extract the text from the element
	const text1 = textToCopy1.innerText;
	const text2 = textToCopy2.innerText;
	const text = text1.concat("\n", text2)

	// Check if the Clipboard API is available
	if (navigator.clipboard && window.isSecureContext) {
		navigator.clipboard.writeText(text)
			.then(() => {
				// Instead of alerting, show the message on the page
				showMessage('Copied!');
			})
			.catch(err => {
				console.error('Failed to copy using Clipboard API, using fallback method', err);
				fallbackCopyText(text);
			});
	} else {
		// Use the fallback method if Clipboard API is not available
		fallbackCopyText(text);
	}
});
