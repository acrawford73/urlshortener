// copy-button
// Get references to the HTML elements
const copyBtn = document.getElementById('copyBtn');
const textToCopy1 = document.getElementById('shortTitle');
const textToCopy2 = document.getElementById('shortAlias');

// Add click event listener to the button
copyBtn.addEventListener('click', () => {
	// Extract the text from the element
	const text1 = textToCopy1.innerText;
	const text2 = textToCopy2.innerText;

// Use the Clipboard API to write the text to the clipboard
navigator.clipboard.writeText(text1+"/n"+text2)
	.then(() => {
		// Optional: Provide feedback to the user
		// alert('Text copied to clipboard!');
	})
	.catch(err => {
		console.error('Failed to copy: ', err);
	});
});