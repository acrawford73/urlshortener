// copy-button.js

// Get references to the HTML elements
const copyBtn = document.getElementById('copyBtn');
const textToCopy1 = document.getElementById('shortTitle');
const textToCopy2 = document.getElementById('shortAlias');
const textToCopy3 = document.getElementById('shortTags');
const copyMessage = document.getElementById('copyMessage');

// Function to display a temporary message on the page
function showMessage(message, duration = 5000) {
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
	const text1 = textToCopy1.textContent.trim();
	const text2 = textToCopy2.textContent.trim();
	const text3 = textToCopy3.textContent.trim();
	const text = `${text1}\n${text2}\n${text3}`;
	//const text = text1.concat("\n", text2).concat("\n", text3);

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
