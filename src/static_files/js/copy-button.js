// copy-button
// Get references to the HTML elements
const copyBtn = document.getElementById('copyBtn');
const textToCopy = document.getElementById('shortAlias');

// Add click event listener to the button
copyBtn.addEventListener('click', () => {
	// Extract the text from the element
	const text = textToCopy.innerText;

// Use the Clipboard API to write the text to the clipboard
navigator.clipboard.writeText(text)
	.then(() => {
		// Optional: Provide feedback to the user
		alert('Text copied to clipboard!');
	})
	.catch(err => {
		console.error('Failed to copy: ', err);
	});
});